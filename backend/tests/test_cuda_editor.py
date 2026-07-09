"""E5 — CUDA editor/detector: importable & partially runnable on a CPU-only Mac.

Real generative inference (SD inpaint/img2img, Real-ESRGAN, SAM 2,
GroundingDINO) runs only on the NVIDIA box and is NOT exercised here. What IS
verified on the Mac:

  * the CUDA classes import with no torch/CUDA installed (lazy-import contract);
  * the CUDA editor's non-generative engines (retime-camera, FFmpeg color
    grade, OCR text-detect) run for real via delegation — no GPU needed;
  * the CUDA detector guards clearly when its required source frame is missing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.generators.base import DetectParams, VideoEditParams

FIXTURE = Path(__file__).parent.parent / "app/generators/mock/fixtures/sample.mp4"


def test_cuda_classes_import_on_cpu_only():
    # The whole point of the lazy-import pattern: this must not touch torch.
    from app.generators.cuda import CudaObjectDetector, CudaVideoEditor

    assert CudaVideoEditor().name == "cuda-editor"
    assert CudaObjectDetector().name == "cuda-detector"


def test_cuda_editor_delegates_retime_without_gpu():
    from app.generators.cuda import CudaVideoEditor

    editor = CudaVideoEditor()
    result = editor.edit(
        VideoEditParams(
            source=FIXTURE.read_bytes(),
            source_content_type="video/mp4",
            engine="retime-camera",
            preset_id="mo-reverse",
        )
    )
    assert result.kind == "video"
    assert result.content_type == "video/mp4"
    assert len(result.data) > 0


def test_cuda_editor_delegates_color_grade_without_gpu():
    from app.generators.cuda import CudaVideoEditor

    editor = CudaVideoEditor()
    result = editor.edit(
        VideoEditParams(
            source=FIXTURE.read_bytes(),
            source_content_type="video/mp4",
            engine="global-restyle",
            preset_id="light-cinematic",  # a real FFmpeg grade recipe
        )
    )
    assert len(result.data) > 0


def test_cuda_detector_requires_source_frame():
    from app.generators.cuda import CudaObjectDetector

    detector = CudaObjectDetector()
    # No source bytes attached → clear error rather than a torch import blowup.
    with pytest.raises(RuntimeError, match="source"):
        detector.detect(DetectParams(mode="click", x=0.5, y=0.5))
