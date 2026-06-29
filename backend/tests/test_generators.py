"""Verifies the generator contract works end-to-end with the mock backend.

This is the core Phase 0 guarantee: the swappable generator interface
produces real, valid media on the Mac with no GPU.
"""

from app.generators.base import (
    ImageGenParams,
    VideoGenParams,
    VoiceGenParams,
)
from app.generators.registry import (
    get_image_generator,
    get_video_generator,
    get_voice_generator,
)


def test_video_generator_returns_real_mp4():
    gen = get_video_generator()
    progress_calls: list[float] = []

    media = gen.generate(
        VideoGenParams(prompt="a cat surfing", duration_seconds=4.0),
        progress=lambda f, m=None: progress_calls.append(f),
    )

    assert media.kind == "video"
    assert media.content_type == "video/mp4"
    # Real MP4 bytes (ISO base media file signature contains 'ftyp').
    assert b"ftyp" in media.data[:32]
    assert media.duration_seconds == 4.0
    # Progress was reported and ended at 1.0.
    assert progress_calls and progress_calls[-1] == 1.0


def test_image_generator_returns_real_png():
    media = get_image_generator().generate(ImageGenParams(prompt="a sunset"))
    assert media.kind == "image"
    assert media.data.startswith(b"\x89PNG\r\n")


def test_voice_generator_returns_real_wav():
    media = get_voice_generator().generate(VoiceGenParams(text="hello world"))
    assert media.kind == "audio"
    assert media.data[:4] == b"RIFF"
