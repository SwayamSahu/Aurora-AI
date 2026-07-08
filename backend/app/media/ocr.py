"""Real, CPU-only on-screen text detection (Tesseract OCR).

Samples frames from a video at a fixed interval, runs Tesseract on each, and
returns timestamped bounding boxes for confident text detections. Used by the
`text-detect` AI Edit preset to draw a real, visible overlay — genuinely
real on the Mac, no GPU or generative model required.
"""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

MIN_CONFIDENCE = 45.0
MAX_BOXES_PER_FRAME = 8
MAX_TOTAL_BOXES = 60


@dataclass
class TextBox:
    t: float
    x: int
    y: int
    w: int
    h: int
    text: str
    confidence: float


def _extract_frames(video_path: Path, out_dir: Path, interval: float) -> list[Path]:
    pattern = out_dir / "f_%04d.jpg"
    proc = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            f"fps=1/{interval}",
            "-qscale:v",
            "3",
            str(pattern),
        ],
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            "ffmpeg frame extraction failed: "
            + proc.stderr.decode("utf-8", "replace")[-400:]
        )
    return sorted(out_dir.glob("f_*.jpg"))


def detect_text_boxes(video_path: Path, interval: float = 1.0) -> list[TextBox]:
    """Sample frames and run Tesseract OCR on each, real detections only."""
    import pytesseract  # noqa: PLC0415 — optional, imported lazily
    from PIL import Image  # noqa: PLC0415

    boxes: list[TextBox] = []
    with tempfile.TemporaryDirectory() as tmp:
        frames = _extract_frames(video_path, Path(tmp), interval)
        for i, frame_path in enumerate(frames):
            if len(boxes) >= MAX_TOTAL_BOXES:
                break
            t = i * interval
            image = Image.open(frame_path)
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            frame_boxes: list[TextBox] = []
            for j, text in enumerate(data["text"]):
                if not text.strip():
                    continue
                try:
                    conf = float(data["conf"][j])
                except (ValueError, TypeError):
                    continue
                if conf < MIN_CONFIDENCE:
                    continue
                frame_boxes.append(
                    TextBox(
                        t=t,
                        x=int(data["left"][j]),
                        y=int(data["top"][j]),
                        w=int(data["width"][j]),
                        h=int(data["height"][j]),
                        text=text.strip(),
                        confidence=conf,
                    )
                )
            frame_boxes.sort(key=lambda b: b.confidence, reverse=True)
            boxes.extend(frame_boxes[:MAX_BOXES_PER_FRAME])
    return boxes[:MAX_TOTAL_BOXES]


def render_ocr_overlay(
    src: Path, out: Path, boxes: list[TextBox], box_duration: float = 1.0
) -> None:
    """Burn a translucent box over each detection, timed to when it appeared."""
    if not boxes:
        # Nothing detected — still produce a valid, unmodified output so the
        # edit succeeds and the user sees the (empty) result rather than an
        # opaque failure.
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(src),
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(out),
            ],
            check=True,
            capture_output=True,
        )
        return

    filters = []
    for b in boxes:
        end = b.t + box_duration
        filters.append(
            f"drawbox=x={b.x}:y={b.y}:w={b.w}:h={b.h}:"
            f"color=yellow@0.85:thickness=3:"
            f"enable='between(t,{b.t:.2f},{end:.2f})'"
        )
    vf = ",".join(filters)

    proc = subprocess.run(
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
            str(out),
        ],
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            "ffmpeg overlay render failed: "
            + proc.stderr.decode("utf-8", "replace")[-400:]
        )
