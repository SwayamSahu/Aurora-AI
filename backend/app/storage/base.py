"""Storage abstraction.

Like the generator contract, storage is swappable: `local` (filesystem) for
Mac development & tests, `minio` (S3) for the docker stack and production.
Application code depends only on this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Storage(ABC):
    @abstractmethod
    def put(self, key: str, data: bytes, content_type: str) -> str:
        """Store bytes under `key`; return the key."""

    @abstractmethod
    def get(self, key: str) -> bytes:
        """Return the stored bytes. Raises FileNotFoundError if absent."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove the object. No-op if it does not exist."""

    @abstractmethod
    def exists(self, key: str) -> bool: ...
