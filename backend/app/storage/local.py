"""Local filesystem storage backend (Mac dev & tests)."""

from __future__ import annotations

from pathlib import Path

from app.storage.base import Storage


class LocalStorage(Storage):
    def __init__(self, base_dir: str) -> None:
        self._base = Path(base_dir)
        self._base.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # Keys may contain "/" — preserve as nested dirs, but stay inside base.
        path = (self._base / key).resolve()
        if not str(path).startswith(str(self._base.resolve())):
            raise ValueError("invalid storage key")
        return path

    def put(self, key: str, data: bytes, content_type: str) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()
