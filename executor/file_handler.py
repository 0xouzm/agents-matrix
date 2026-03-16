"""Manage temporary files for ebook uploads and outputs."""

from __future__ import annotations

import uuid
import shutil
from pathlib import Path


class FileHandler:
    """Thread-safe temp file manager for ebook I/O."""

    def __init__(self, temp_dir: Path) -> None:
        self._temp_dir = temp_dir
        self._temp_dir.mkdir(parents=True, exist_ok=True)
        self._files: dict[str, Path] = {}

    def store_upload(self, content: bytes, filename: str) -> str:
        """Save uploaded content to a temp file and return a file_id."""
        file_id = uuid.uuid4().hex[:12]
        suffix = Path(filename).suffix or ""
        dest = self._temp_dir / f"{file_id}{suffix}"
        dest.write_bytes(content)
        self._files[file_id] = dest
        return file_id

    def resolve(self, file_id: str) -> Path:
        """Resolve a file_id to its filesystem path."""
        path = self._files.get(file_id)
        if path is None or not path.exists():
            raise FileNotFoundError(f"File not found: {file_id}")
        return path

    def create_output_path(self, extension: str) -> Path:
        """Create a new output path with the given extension."""
        file_id = uuid.uuid4().hex[:12]
        ext = extension if extension.startswith(".") else f".{extension}"
        path = self._temp_dir / f"{file_id}{ext}"
        self._files[file_id] = path
        return path

    def register_output(self, path: Path) -> str:
        """Register an existing output file and return its file_id."""
        file_id = uuid.uuid4().hex[:12]
        self._files[file_id] = path
        return file_id

    def cleanup(self, file_id: str) -> None:
        """Remove a temp file by file_id."""
        path = self._files.pop(file_id, None)
        if path and path.exists():
            path.unlink()

    def cleanup_all(self) -> None:
        """Remove all tracked temp files."""
        for path in self._files.values():
            if path.exists():
                path.unlink(missing_ok=True)
        self._files.clear()

    @property
    def temp_dir(self) -> Path:
        return self._temp_dir
