"""Mock generators — return real fixture media instantly.

These let the entire platform (UI, queue, editor, export) be developed and
tested on the Mac with NO GPU. They emit genuine, valid media files so that
downstream FFmpeg/MoviePy processing is exercised for real.
"""

from app.generators.mock.detector import MockObjectDetector
from app.generators.mock.editor import MockVideoEditor
from app.generators.mock.generators import (
    MockImageGenerator,
    MockImageToVideoGenerator,
    MockMusicGenerator,
    MockTranscriber,
    MockVideoGenerator,
    MockVoiceGenerator,
)

__all__ = [
    "MockVideoGenerator",
    "MockImageToVideoGenerator",
    "MockImageGenerator",
    "MockVoiceGenerator",
    "MockMusicGenerator",
    "MockTranscriber",
    "MockVideoEditor",
    "MockObjectDetector",
]
