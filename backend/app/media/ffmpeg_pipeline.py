"""FFmpeg-based export pipeline.

Compiles a timeline document (tracks → clips referencing assets in storage)
into a final MP4. Runs entirely on CPU — real on the Mac and the GPU box.

Architecture:
1. `build_render_plan` validates the document and resolves asset storage keys
   to local temp files (no FFmpeg-specific code, easily unit-tested).
2. `render_to_mp4` drives FFmpeg via `ffmpeg-python` to assemble the final
   output.  Complex filter graphs are built dynamically from the render plan.

Supports:
  - Multiple video clips on the video track, trimmed and placed at their
    timeline positions (with black gap fills between clips)
  - Audio track clips mixed down alongside the video
  - Text/caption clips burned-in via `drawtext` (when libfreetype is present)
    or written as a sidecar SRT (graceful degradation on stripped FFmpeg builds)
  - Fade-in at start / fade-out at end (controlled by render params)
  - Final output: H.264 / AAC, configurable resolution and CRF

Caption burning note:
  The Homebrew FFmpeg on macOS may be built without libfreetype (no drawtext).
  The pipeline detects this at runtime, skips burning, and writes an SRT sidecar
  next to the output MP4 instead. The Docker image (Linux) has a full FFmpeg
  build with libfreetype so burning works there.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import ffmpeg

logger = logging.getLogger(__name__)


def _ffmpeg_has_drawtext() -> bool:
    """Return True if this FFmpeg build includes the drawtext filter (libfreetype)."""
    import subprocess  # noqa: PLC0415
    try:
        result = subprocess.run(
            ["ffmpeg", "-filters"],
            capture_output=True, text=True, timeout=5
        )
        return "drawtext" in result.stdout
    except Exception:  # noqa: BLE001
        return False


def _captions_to_srt(captions: list[Caption]) -> str:
    """Render captions to an SRT string (sidecar when drawtext unavailable)."""
    def ts(s: float) -> str:
        ms = int(round(s * 1000))
        h, ms = divmod(ms, 3_600_000)
        m, ms = divmod(ms, 60_000)
        sec, ms = divmod(ms, 1000)
        return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"

    lines: list[str] = []
    for i, cap in enumerate(captions, 1):
        lines.extend([str(i), f"{ts(cap.start)} --> {ts(cap.end)}", cap.text, ""])
    return "\n".join(lines)

ProgressCb = Callable[[float, str], None]


def _noop(fraction: float, message: str = "") -> None:  # noqa: ARG001
    pass


# --------------------------------------------------------------------------- #
# Render plan data structures
# --------------------------------------------------------------------------- #

@dataclass
class VideoSegment:
    """A single video or image clip placed on the output timeline."""
    local_path: str
    is_image: bool
    timeline_start: float   # output timeline position (seconds)
    timeline_end: float     # = timeline_start + duration
    trim_start: float       # in-point in the source file (seconds)
    source_duration: float  # how many seconds to use from the source
    transition_in: str | None = None  # FFmpeg xfade name, or None for hard cut


@dataclass
class AudioSegment:
    """An audio clip (voiceover, music, …) placed on the output timeline."""
    local_path: str
    timeline_start: float
    timeline_end: float
    trim_start: float
    source_duration: float


@dataclass
class Caption:
    """A text caption burned into the video."""
    text: str
    start: float
    end: float
    font_size: int = 48
    color: str = "white"
    y_pct: int = 85     # vertical position as % of output height
    align: str = "center"


@dataclass
class RenderParams:
    width: int = 1280
    height: int = 720
    fps: int = 24
    crf: int = 23          # H.264 quality (lower = better; 23 is sane default)
    fade_duration: float = 0.5
    total_duration: float = 0.0


@dataclass
class RenderPlan:
    params: RenderParams
    video_segments: list[VideoSegment] = field(default_factory=list)
    audio_segments: list[AudioSegment] = field(default_factory=list)
    captions: list[Caption] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Plan builder (pure, no FFmpeg — easy to test)
# --------------------------------------------------------------------------- #

def build_render_plan(
    document: dict,
    asset_paths: dict[str, str],  # asset_id → local temp path
    params: RenderParams,
) -> RenderPlan:
    """Translate a timeline JSON document into a RenderPlan.

    `asset_paths` maps asset IDs to paths of their bytes already written to
    temp files.  Unknown/missing asset IDs are silently skipped (the clip is
    treated as a gap).
    """
    plan = RenderPlan(params=params)
    total = 0.0

    for track in document.get("tracks", []):
        track_type = track.get("type")
        for clip in track.get("clips", []):
            start = float(clip.get("start", 0))
            dur = float(clip.get("duration", 0))
            if dur <= 0:
                continue
            end = start + dur
            trim = float(clip.get("trim_start", 0))
            kind = clip.get("kind")
            total = max(total, end)

            if track_type == "video":
                asset_id = clip.get("asset_id")
                path = asset_paths.get(asset_id or "")
                if not path:
                    continue
                plan.video_segments.append(
                    VideoSegment(
                        local_path=path,
                        is_image=(kind == "image"),
                        timeline_start=start,
                        timeline_end=end,
                        trim_start=trim,
                        source_duration=dur,
                        transition_in=clip.get("transition_in") or None,
                    )
                )

            elif track_type == "audio":
                asset_id = clip.get("asset_id")
                path = asset_paths.get(asset_id or "")
                if not path:
                    continue
                plan.audio_segments.append(
                    AudioSegment(
                        local_path=path,
                        timeline_start=start,
                        timeline_end=end,
                        trim_start=trim,
                        source_duration=dur,
                    )
                )

            elif track_type == "text" and kind == "text":
                style = clip.get("style", {})
                plan.captions.append(
                    Caption(
                        text=str(clip.get("text", "") or ""),
                        start=start,
                        end=end,
                        font_size=int(style.get("fontSize", 48)),
                        color=str(style.get("color", "white")).replace("#", ""),
                        y_pct=int(style.get("y", 85)),
                        align=str(style.get("align", "center")),
                    )
                )

    if params.total_duration > 0:
        total = params.total_duration
    params.total_duration = total or 1.0
    return plan


# --------------------------------------------------------------------------- #
# Escape helpers for FFmpeg drawtext
# --------------------------------------------------------------------------- #

def _escape_drawtext(text: str) -> str:
    """Escape special characters for the FFmpeg drawtext filter."""
    return (
        text.replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace(":", "\\:")
            .replace("%", "\\%")
    )


# Blend window for clip-to-clip transitions (seconds).
_XFADE_DUR = 0.5


# --------------------------------------------------------------------------- #
# Renderer
# --------------------------------------------------------------------------- #

def render_to_mp4(
    plan: RenderPlan,
    output_path: str,
    progress: ProgressCb = _noop,
) -> str:
    """Render the plan to an MP4 file at `output_path`.

    Returns `output_path` on success, raises on failure.
    """
    p = plan.params
    total = p.total_duration
    w, h = p.width, p.height

    progress(0.05, "building filter graph")

    # ------------------------------------------------------------------ #
    # 1. Build the video stream: concat + xfade chain with black gap fills
    # ------------------------------------------------------------------ #
    def _clip_src(seg: VideoSegment):
        seg_dur = seg.source_duration
        if seg.is_image:
            return (
                ffmpeg.input(seg.local_path, loop=1, t=seg_dur).video
                .filter("scale", w, h, force_original_aspect_ratio="decrease")
                .filter("pad", w, h, "(ow-iw)/2", "(oh-ih)/2")
                .filter("setsar", "1").filter("fps", p.fps)
            )
        return (
            ffmpeg.input(seg.local_path, ss=seg.trim_start, t=seg_dur).video
            .filter("scale", w, h, force_original_aspect_ratio="decrease")
            .filter("pad", w, h, "(ow-iw)/2", "(oh-ih)/2")
            .filter("setsar", "1").filter("fps", p.fps)
        )

    def _black(dur: float):
        return ffmpeg.input(
            f"color=black:s={w}x{h}:r={p.fps}:d={dur}", f="lavfi"
        ).video

    if plan.video_segments:
        segs = sorted(plan.video_segments, key=lambda s: s.timeline_start)

        # Flatten clips + gap fills into an ordered list of (stream, dur, transition).
        items = []
        prev_end = 0.0
        for seg in segs:
            gap = seg.timeline_start - prev_end
            if gap > 0.05:
                items.append((_black(gap), gap, None))
            t_in = seg.transition_in if seg.transition_in not in (None, "", "none", "cut") else None
            items.append((_clip_src(seg), seg.source_duration, t_in))
            prev_end = seg.timeline_end

        # Build the chain with xfade (transition) or concat (hard cut).
        chain, chain_dur = items[0][0], items[0][1]
        for seg_stream, dur, t_in in items[1:]:
            if t_in:
                xd = min(_XFADE_DUR, chain_dur * 0.4, dur * 0.4)
                chain = ffmpeg.filter(
                    [chain, seg_stream],
                    "xfade",
                    transition=t_in,
                    duration=xd,
                    offset=max(0.0, chain_dur - xd),
                )
                chain_dur += dur - xd
            else:
                chain = ffmpeg.filter([chain, seg_stream], "concat", n=2, v=1, a=0)
                chain_dur += dur

        # Sync total to actual chain duration (transitions shrink it slightly).
        total = chain_dur
        p.total_duration = total
        video_stream = chain
    else:
        video_stream = _black(total)

    # ------------------------------------------------------------------ #
    # 2. Burn-in captions via drawtext (or sidecar SRT if unavailable)
    # ------------------------------------------------------------------ #
    srt_sidecar: str | None = None

    if plan.captions:
        if _ffmpeg_has_drawtext():
            for cap in plan.captions:
                if not cap.text.strip():
                    continue
                safe_text = _escape_drawtext(cap.text)
                color_val = cap.color if cap.color.startswith("#") else f"#{cap.color}"
                y_expr = f"(h*{cap.y_pct}/100)"
                if cap.align == "center":
                    x_expr = "(w-text_w)/2"
                elif cap.align == "right":
                    x_expr = "w-text_w-20"
                else:
                    x_expr = "20"

                video_stream = video_stream.drawtext(
                    text=safe_text,
                    fontsize=cap.font_size,
                    fontcolor=color_val,
                    x=x_expr,
                    y=y_expr,
                    borderw=2,
                    bordercolor="black",
                    enable=f"between(t,{cap.start},{cap.end})",
                )
        else:
            # drawtext unavailable (stripped FFmpeg build); write SRT sidecar.
            logger.warning(
                "FFmpeg drawtext not available — captions written as SRT sidecar "
                "next to the output file. Install FFmpeg with libfreetype for burned-in captions."
            )
            srt_sidecar = _captions_to_srt(plan.captions)

    # ------------------------------------------------------------------ #
    # 3. Fade in / out
    # ------------------------------------------------------------------ #
    if p.fade_duration > 0 and total > p.fade_duration * 2:
        video_stream = video_stream.filter(
            "fade", type="in", start_time=0, duration=p.fade_duration
        ).filter(
            "fade", type="out",
            start_time=total - p.fade_duration,
            duration=p.fade_duration,
        )

    progress(0.3, "compositing video")

    # ------------------------------------------------------------------ #
    # 4. Audio stream
    # ------------------------------------------------------------------ #
    if plan.audio_segments:
        audio_inputs = []
        for seg in plan.audio_segments:
            a = (
                ffmpeg
                .input(seg.local_path, ss=seg.trim_start, t=seg.source_duration)
                .audio
                .filter("adelay", f"{int(seg.timeline_start * 1000)}|{int(seg.timeline_start * 1000)}")
            )
            audio_inputs.append(a)

        if len(audio_inputs) == 1:
            audio_stream = audio_inputs[0]
        else:
            audio_stream = ffmpeg.filter(audio_inputs, "amix", inputs=len(audio_inputs), duration="longest")

        # Pad/trim to match total duration.
        audio_stream = audio_stream.filter("apad").filter("atrim", duration=total)
    else:
        # Silent audio track so the output always has an audio stream.
        audio_stream = (
            ffmpeg
            .input(f"anullsrc=r=44100:cl=stereo:d={total}", f="lavfi")
            .audio
        )

    progress(0.5, "mixing audio")

    # ------------------------------------------------------------------ #
    # 5. Encode
    # ------------------------------------------------------------------ #
    out = (
        ffmpeg
        .output(
            video_stream,
            audio_stream,
            output_path,
            vcodec="libx264",
            acodec="aac",
            crf=p.crf,
            preset="fast",
            pix_fmt="yuv420p",
            movflags="+faststart",
            t=total,
        )
        .overwrite_output()
    )

    progress(0.6, "encoding")
    logger.info("FFmpeg render started: %s", output_path)

    try:
        out.run(capture_stdout=True, capture_stderr=True, quiet=True)
    except ffmpeg.Error as exc:
        stderr = exc.stderr.decode("utf-8", errors="replace") if exc.stderr else ""
        logger.error("FFmpeg error:\n%s", stderr)
        raise RuntimeError(f"FFmpeg render failed:\n{stderr[:2000]}") from exc

    # Write SRT sidecar if drawtext was unavailable.
    if srt_sidecar is not None:
        srt_path = str(output_path).rsplit(".", 1)[0] + ".srt"
        Path(srt_path).write_text(srt_sidecar, encoding="utf-8")
        logger.info("SRT sidecar written: %s", srt_path)

    progress(1.0, "done")
    logger.info("FFmpeg render complete: %s", output_path)
    return output_path
