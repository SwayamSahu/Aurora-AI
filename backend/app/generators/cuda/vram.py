"""VRAM manager for the single-GPU 16 GB NVIDIA box.

Enforces a one-model-at-a-time policy: before loading a new diffusion pipeline
the current tenant is deleted, Python GC is run, and the CUDA cache is flushed.
This prevents OOM when models each occupy 6–10 GB.

The worker runs with --concurrency=1 so the threading lock is belt-and-suspenders,
but it is cheap and keeps things correct if concurrency ever changes.

Usage::

    from app.generators.cuda.vram import acquire_pipeline

    def _loader():
        return MyPipeline.from_pretrained(...)

    pipe = acquire_pipeline("my-model-id", _loader)
"""

from __future__ import annotations

import gc
import logging
import threading
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_tenant_id: str | None = None
_pipeline: Any | None = None


def acquire_pipeline(tenant_id: str, loader: Callable[[], Any]) -> Any:
    """Return the loaded pipeline for *tenant_id*.

    If the requested model is already resident it is returned immediately.
    Otherwise the current model is evicted first, then *loader()* is called.
    *loader* must return the pipeline object (e.g. a diffusers Pipeline).
    """
    global _tenant_id, _pipeline  # noqa: PLW0603

    with _lock:
        if _tenant_id == tenant_id and _pipeline is not None:
            return _pipeline

        if _pipeline is not None:
            logger.info("VRAM: evicting '%s' to make room for '%s'", _tenant_id, tenant_id)
            _evict()

        logger.info("VRAM: loading '%s'", tenant_id)
        _pipeline = loader()
        _tenant_id = tenant_id

        used = _vram_used_gb()
        if used is not None:
            logger.info("VRAM: '%s' loaded  (%.1f GB allocated)", tenant_id, used)
        return _pipeline


def evict() -> None:
    """Force-evict the current pipeline. Safe to call even when no model is loaded."""
    with _lock:
        _evict()


def _evict() -> None:
    """Internal — caller must hold *_lock*."""
    global _tenant_id, _pipeline  # noqa: PLW0603

    if _pipeline is None:
        return
    del _pipeline
    _pipeline = None
    _tenant_id = None
    gc.collect()
    _flush_cuda_cache()


def _flush_cuda_cache() -> None:
    try:
        import torch  # noqa: PLC0415

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
    except ImportError:
        pass


def _vram_used_gb() -> float | None:
    try:
        import torch  # noqa: PLC0415

        if torch.cuda.is_available():
            return torch.cuda.memory_allocated() / 1024**3
    except ImportError:
        pass
    return None
