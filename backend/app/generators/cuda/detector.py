"""CUDA object detector — real segmentation, GENERATOR_BACKEND=cuda only.

Runs on the NVIDIA box (Phase 9 / E5). Lazy GPU imports so this is importable
on a CPU-only Mac.

  click mode → SAM 2 point prompt → mask → tight bounding box
  text mode  → GroundingDINO open-vocabulary detection for the query phrase

Both operate on a representative frame (the clip's first frame), extracted with
FFmpeg. Boxes are returned in normalized (0-1) coordinates — the same contract
the mock detector satisfies, so the frontend is unchanged.
"""

from __future__ import annotations

import io
import logging
import os

from app.generators.base import DetectedObject, DetectParams, ObjectDetector
from app.generators.cuda.vram import acquire_pipeline
from app.media.video_frames import extract_first_frame

logger = logging.getLogger(__name__)

_HF_HOME = os.environ.get("HF_HOME", "/models/hf")
_GROUNDING_DINO = "IDEA-Research/grounding-dino-tiny"
_SAM2_MODEL = "facebook/sam2-hiera-large"

_BOX_THRESHOLD = 0.3
_TEXT_THRESHOLD = 0.25
_MAX_TEXT_BOXES = 8


class CudaObjectDetector(ObjectDetector):
    """Real click/text object detection. Needs a source frame — callers pass
    the clip bytes via `params` is not enough, so the detect service supplies
    the frame through the `source` attribute set on params (see below)."""

    name = "cuda-detector"

    def detect(self, params: DetectParams) -> list[DetectedObject]:
        # The clip bytes are attached by the detect route for GPU backends.
        source = getattr(params, "source", None)
        if not source:
            raise RuntimeError(
                "CUDA detection requires the clip's source bytes on params.source."
            )
        frame = extract_first_frame(source)
        if params.mode == "click":
            return self._detect_click(frame, params)
        return self._detect_text(frame, params)

    def _detect_click(
        self, frame: bytes, params: DetectParams
    ) -> list[DetectedObject]:
        import numpy as np  # noqa: PLC0415
        from PIL import Image  # noqa: PLC0415
        from sam2.sam2_image_predictor import SAM2ImagePredictor  # noqa: PLC0415

        def _loader():
            return SAM2ImagePredictor.from_pretrained(_SAM2_MODEL, cache_dir=_HF_HOME)

        predictor = acquire_pipeline(f"{self.name}:sam2", _loader)
        image = np.array(Image.open(io.BytesIO(frame)).convert("RGB"))
        h, w = image.shape[:2]
        predictor.set_image(image)

        point = np.array([[(params.x or 0.5) * w, (params.y or 0.5) * h]])
        masks, scores, _ = predictor.predict(
            point_coords=point, point_labels=np.array([1]), multimask_output=True
        )
        best = masks[int(np.argmax(scores))]
        ys, xs = np.where(best > 0)
        if len(xs) == 0:
            return []
        x0, x1 = xs.min() / w, xs.max() / w
        y0, y1 = ys.min() / h, ys.max() / h
        return [
            DetectedObject(
                label="Selection",
                x=float(x0),
                y=float(y0),
                w=float(x1 - x0),
                h=float(y1 - y0),
                confidence=float(scores.max()),
            )
        ]

    def _detect_text(
        self, frame: bytes, params: DetectParams
    ) -> list[DetectedObject]:
        import torch  # noqa: PLC0415
        from PIL import Image  # noqa: PLC0415
        from transformers import (  # noqa: PLC0415
            AutoModelForZeroShotObjectDetection,
            AutoProcessor,
        )

        query = (params.query or "object").strip()
        label = query.title()

        def _loader():
            processor = AutoProcessor.from_pretrained(
                _GROUNDING_DINO, cache_dir=_HF_HOME
            )
            model = AutoModelForZeroShotObjectDetection.from_pretrained(
                _GROUNDING_DINO, cache_dir=_HF_HOME
            ).to("cuda")
            return processor, model

        processor, model = acquire_pipeline(f"{self.name}:gdino", _loader)
        image = Image.open(io.BytesIO(frame)).convert("RGB")
        w, h = image.size

        # GroundingDINO expects a lowercased, period-terminated prompt.
        text = f"{query.lower()}."
        inputs = processor(images=image, text=text, return_tensors="pt").to("cuda")
        with torch.no_grad():
            outputs = model(**inputs)
        results = processor.post_process_grounded_object_detection(
            outputs,
            inputs.input_ids,
            box_threshold=_BOX_THRESHOLD,
            text_threshold=_TEXT_THRESHOLD,
            target_sizes=[(h, w)],
        )[0]

        objects: list[DetectedObject] = []
        for i, (box, score) in enumerate(
            zip(results["boxes"], results["scores"], strict=False)
        ):
            x0, y0, x1, y1 = (float(v) for v in box.tolist())
            objects.append(
                DetectedObject(
                    label=f"{label} {i + 1}",
                    x=x0 / w,
                    y=y0 / h,
                    w=(x1 - x0) / w,
                    h=(y1 - y0) / h,
                    confidence=round(float(score), 2),
                )
            )
            if len(objects) >= _MAX_TEXT_BOXES:
                break
        return objects
