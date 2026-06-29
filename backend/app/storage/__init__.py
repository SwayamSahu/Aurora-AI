"""Storage registry — resolves the configured backend."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import StorageBackend, settings
from app.storage.base import Storage


@lru_cache
def get_storage() -> Storage:
    if settings.storage_backend == StorageBackend.LOCAL:
        from app.storage.local import LocalStorage

        return LocalStorage(settings.local_storage_dir)

    from app.storage.minio_backend import MinioStorage

    return MinioStorage()
