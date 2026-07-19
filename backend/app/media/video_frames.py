"""Shared FFmpeg video-frame extraction.

Used by two independent callers that each need one representative frame from
a video: the CUDA object detector (SAM2/GroundingDINO run on a single frame)
and the generation job runner (the content-safety classifier screens
generated video via its first frame, since the classifier itself is
image-only). Both want "frame 1 as PNG bytes" — kept as one implementation
so the ffmpeg invocation and error handling don't drift between them.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


def extract_first_frame(video_bytes: bytes) -> bytes:
    """Return the first frame of `video_bytes` as PNG bytes, via ffmpeg.

    Raises `RuntimeError` (with the ffmpeg stderr tail) if extraction fails —
    e.g. corrupt or empty video data.
    """
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "src.mp4"
        src.write_bytes(video_bytes)
        frame = Path(tmp) / "frame.png"
        proc = subprocess.run(
            ["ffmpeg", "-y", "-i", str(src), "-frames:v", "1", str(frame)],
            capture_output=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                "ffmpeg frame extract failed: "
                + proc.stderr.decode("utf-8", "replace")[-400:]
            )
        return frame.read_bytes()
