"""CUDA generator implementations — loaded only when GENERATOR_BACKEND=cuda.

All heavy imports (torch, diffusers, transformers) are lazy so this package
can be imported on a CPU-only Mac without raising ImportError.
"""

from app.generators.cuda.detector import CudaObjectDetector
from app.generators.cuda.editor import CudaVideoEditor
from app.generators.cuda.generators import (
    CudaImageGenerator,
    CudaImageToVideoGenerator,
    CudaMusicGenerator,
    CudaVideoGenerator,
)

__all__ = [
    "CudaVideoGenerator",
    "CudaImageToVideoGenerator",
    "CudaImageGenerator",
    "CudaMusicGenerator",
    "CudaVideoEditor",
    "CudaObjectDetector",
]
