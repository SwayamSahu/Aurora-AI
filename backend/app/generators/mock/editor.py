"""Mock video editor — real, visible FFmpeg transforms (no GPU).

Three families are genuinely real (no stand-in), keyed by the catalog preset
id passed through as `params.preset_id`:

  - retime-camera  → real speed/reverse/loop/boomerang/freeze/ramp via
                      setpts/concat/tpad, and real stabilize/pan/zoom/orbit
                      via deshake/crop/zoompan/rotate.
  - global-restyle  → real color grading (eq/colorbalance/curves/vignette/
                      noise) for the `lighting` and `time-season` catalog
                      categories. Presets outside those categories (sky
                      replacement, style transfer, weather particles, …)
                      genuinely need a generative model and keep a labeled
                      stand-in filter until the CUDA editor (Phase 9).
  - text-ops        → real on-screen text DETECTION via Tesseract OCR,
                      drawn as a timed overlay. Text replace/translate/
                      remove/restyle still need generative inpainting and
                      keep the stand-in filter.

Everything else (masked-v2v, inpaint-remove, enhance, and any unmatched
global-restyle/text-ops preset) uses a distinct but clearly-a-stand-in filter
so the pipeline — API, job, layer stack, compare slider, export — is fully
exercised end-to-end before Phase 9 swaps in real generative models.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from app.generators.base import (
    GeneratedMedia,
    ProgressCallback,
    VideoEditor,
    VideoEditParams,
    _noop_progress,
)

_ENCODE_TAIL = [
    "-c:v",
    "libx264",
    "-preset",
    "veryfast",
    "-pix_fmt",
    "yuv420p",
    "-movflags",
    "+faststart",
]

# Full-frame stand-in filter per engine — used when there's no real,
# deterministic recipe for the specific preset (i.e. it needs a generative
# model, deferred to the CUDA editor).
_ENGINE_FILTER: dict[str, str] = {
    "masked-v2v": "hue=h=110:s=1.35",
    "inpaint-remove": "boxblur=12:2,eq=saturation=0.6",
    "global-restyle": "eq=contrast=1.18:saturation=1.12,colorbalance=rs=0.05:bs=-0.05",
    "enhance": "unsharp=5:5:1.0:5:5:0.0",
    "text-ops": "eq=brightness=-0.03",
    "segment-track": "null",
}

# -- Real color grading: `lighting` + `time-season` catalog categories ----- #
GRADE_RECIPES: dict[str, str] = {
    "light-brighten": "eq=brightness=0.08:contrast=1.05",
    "light-studio": "eq=contrast=1.1:brightness=0.02,colorbalance=rm=0.02:gm=0.02:bm=0.02",
    "light-cinematic": "eq=contrast=1.2:saturation=1.1,colorbalance=rs=0.08:bs=-0.08:rm=0.04:bm=-0.04,curves=vintage",
    "light-neon": "eq=saturation=1.4:contrast=1.15,colorbalance=rs=-0.1:bs=0.15:gs=-0.05",
    "light-soft": "eq=contrast=0.92:brightness=0.03,gblur=sigma=0.4",
    "light-golden": "eq=brightness=0.05:saturation=1.15,colorbalance=rs=0.15:gs=0.05:bs=-0.15",
    "light-volumetric": "eq=contrast=1.15:brightness=0.03,vignette=PI/5",
    "time-morning": "eq=brightness=0.04:saturation=0.95,colorbalance=bs=0.08:gs=0.02",
    "time-noon": "eq=brightness=0.06:contrast=1.05:saturation=1.05",
    "time-golden": "eq=brightness=0.05:saturation=1.15,colorbalance=rs=0.18:gs=0.05:bs=-0.18",
    "time-blue": "eq=brightness=-0.05:saturation=0.9,colorbalance=bs=0.2:rs=-0.1",
    "time-night": "eq=brightness=-0.22:contrast=1.1:saturation=0.75,colorbalance=bs=0.12",
    "time-rainy-night": "eq=brightness=-0.25:contrast=1.15:saturation=0.6,colorbalance=bs=0.15,noise=alls=8:allf=t",
    "season-summer": "eq=saturation=1.2:brightness=0.03:contrast=1.03",
    "season-winter": "eq=saturation=0.75:brightness=0.05,colorbalance=bs=0.15:rs=-0.05",
    "season-autumn": "eq=saturation=1.1,colorbalance=rs=0.15:gs=0.05:bs=-0.15",
    "season-spring": "eq=saturation=1.15:brightness=0.03,colorbalance=gs=0.08",
    "season-xmas": "eq=saturation=1.1:contrast=1.05,colorbalance=rs=0.05:gs=0.05",
}

# -- Real retime/camera: `motion-camera` catalog category ------------------ #
_RETIME_MODE: dict[str, str] = {
    "mo-slow": "slow",
    "mo-ramp": "ramp",
    "mo-freeze": "freeze",
    "mo-reverse": "reverse",
    "mo-boomerang": "boomerang",
    "mo-loop": "loop",
    "cam-stabilize": "stabilize",
    "cam-pan": "pan",
    "cam-zoom": "zoom",
    "cam-orbit": "orbit",
}


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "ffmpeg failed: " + proc.stderr.decode("utf-8", "replace")[-500:]
        )


def _run_vf(src: Path, out: Path) -> _VfBuilder:
    return _VfBuilder(src, out)


class _VfBuilder:
    """Small helper so each retime mode reads as one clear statement."""

    def __init__(self, src: Path, out: Path) -> None:
        self.src = src
        self.out = out

    def simple(self, vf: str) -> None:
        _run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(self.src),
                "-vf",
                vf,
                "-an",
                *_ENCODE_TAIL,
                str(self.out),
            ]
        )

    def complex(self, filtergraph: str, map_out: str = "[v]") -> None:
        _run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(self.src),
                "-filter_complex",
                filtergraph,
                "-map",
                map_out,
                "-an",
                *_ENCODE_TAIL,
                str(self.out),
            ]
        )


def _probe_duration(path: Path) -> float:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    try:
        return float(proc.stdout.strip())
    except ValueError:
        return 4.0


def _probe_size(path: Path) -> tuple[int, int]:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=s=x:p=0",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    try:
        w, h = proc.stdout.strip().split("x")
        return int(w), int(h)
    except (ValueError, IndexError):
        return 1280, 720


class MockVideoEditor(VideoEditor):
    name = "mock-editor"

    def edit(
        self,
        params: VideoEditParams,
        progress: ProgressCallback = _noop_progress,
    ) -> GeneratedMedia:
        progress(0.1, "loading source")

        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            src = d / "src.mp4"
            out = d / "out.mp4"
            src.write_bytes(params.source)

            if params.engine == "retime-camera":
                self._retime(src, out, params)
            elif params.engine == "text-ops" and params.preset_id == "text-detect":
                self._text_detect(src, out)
            else:
                self._filter(src, out, params, d)

            progress(0.9, "encoding")
            data = out.read_bytes()

        progress(1.0, "done")
        return GeneratedMedia(
            kind="video",
            data=data,
            content_type="video/mp4",
            suggested_filename="edit.mp4",
            meta={
                "backend": self.name,
                "engine": params.engine,
                "preset_id": params.preset_id,
            },
        )

    # -- filter-based engines (optionally masked) --------------------------- #
    def _pick_filter(self, params: VideoEditParams) -> str:
        if params.engine == "global-restyle" and params.preset_id in GRADE_RECIPES:
            return GRADE_RECIPES[params.preset_id]
        return _ENGINE_FILTER.get(params.engine, "hue=h=110:s=1.3")

    def _filter(self, src: Path, out: Path, params: VideoEditParams, d: Path) -> None:
        vf = self._pick_filter(params)

        if params.mask:
            # Apply the effect only inside the mask region:
            #   [effect] and [original] blended by the mask's luminance as alpha.
            mask = d / "mask.png"
            mask.write_bytes(params.mask)
            # maskedmerge needs base, effect and mask at identical dimensions.
            # The mask is authored at a fixed canvas size, so split the base,
            # apply the effect to one copy, and scale the mask to the base's
            # size (scale2ref) before merging.
            filtergraph = (
                "[0:v]split=2[b1][b2];"
                f"[b1]{vf}[fx];"
                "[2:v]format=gray[mg];"
                "[mg][b2]scale2ref=flags=bilinear[m][base];"
                "[base][fx][m]maskedmerge[v]"
            )
            _run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(src),
                    "-i",
                    str(src),
                    "-i",
                    str(mask),
                    "-filter_complex",
                    filtergraph,
                    "-map",
                    "[v]",
                    "-map",
                    "0:a?",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-pix_fmt",
                    "yuv420p",
                    "-movflags",
                    "+faststart",
                    str(out),
                ]
            )
        else:
            _run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(src),
                    "-vf",
                    vf,
                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-pix_fmt",
                    "yuv420p",
                    "-movflags",
                    "+faststart",
                    "-c:a",
                    "copy",
                    str(out),
                ]
            )

    # -- real on-screen text detection (Tesseract OCR) ----------------------- #
    def _text_detect(self, src: Path, out: Path) -> None:
        from app.media.ocr import detect_text_boxes, render_ocr_overlay  # noqa: PLC0415

        boxes = detect_text_boxes(src)
        render_ocr_overlay(src, out, boxes)

    # -- real retime / camera engine ----------------------------------------- #
    def _retime(self, src: Path, out: Path, params: VideoEditParams) -> None:
        mode = _RETIME_MODE.get(params.preset_id or "", "slow")
        b = _run_vf(src, out)

        if mode == "slow":
            b.simple("setpts=2.0*PTS")
        elif mode == "reverse":
            b.simple("reverse")
        elif mode == "stabilize":
            b.simple("deshake")
        elif mode == "pan":
            dur = _probe_duration(src)
            b.simple(
                f"crop=w='iw*0.82':h='ih*0.82':x='(iw-ow)*t/{dur:.3f}':y='(ih-oh)/2'"
            )
        elif mode == "zoom":
            w, h = _probe_size(src)
            b.simple(
                "scale=8000:-2,"
                "zoompan=z='min(zoom+0.0018,1.35)':d=1:"
                "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"s={w}x{h}:fps=24"
            )
        elif mode == "orbit":
            b.simple(
                "scale=iw*1.15:ih*1.15,"
                "rotate=a='0.035*sin(2*PI*t/4)':fillcolor=black@0,"
                "crop=iw/1.15:ih/1.15"
            )
        elif mode == "boomerang":
            b.complex("[0:v]split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0[v]")
        elif mode == "loop":
            b.complex("[0:v]split[a][b];[a][b]concat=n=2:v=1:a=0[v]")
        elif mode == "ramp":
            dur = _probe_duration(src)
            d1, d2 = dur / 3, 2 * dur / 3
            b.complex(
                f"[0:v]trim=0:{d1:.3f},setpts=PTS-STARTPTS[a];"
                f"[0:v]trim={d1:.3f}:{d2:.3f},setpts=PTS-STARTPTS,setpts=2.2*PTS[m];"
                f"[0:v]trim={d2:.3f}:{dur:.3f},setpts=PTS-STARTPTS[c];"
                f"[a][m][c]concat=n=3:v=1:a=0[v]"
            )
        elif mode == "freeze":
            dur = _probe_duration(src)
            mid = max(0.2, dur / 2)
            freeze_end = min(dur, mid + 0.08)
            b.complex(
                f"[0:v]trim=0:{mid:.3f},setpts=PTS-STARTPTS[a];"
                f"[0:v]trim={mid:.3f}:{freeze_end:.3f},setpts=PTS-STARTPTS,"
                "tpad=stop_mode=clone:stop_duration=1[f];"
                f"[0:v]trim={mid:.3f}:{dur:.3f},setpts=PTS-STARTPTS[c];"
                f"[a][f][c]concat=n=3:v=1:a=0[v]"
            )
        else:
            b.simple("setpts=2.0*PTS")
