from __future__ import annotations
from pathlib import Path
from typing import Callable, Dict



class FileManager:
    """
    Central registry for file formats.

    - Delegates to format-specific reader/writer functions.
    """

    _readers: Dict[str, Callable[[Path], "SimpleFile"]] = {}
    _writers: Dict[str, Callable[[Path, "SimpleFile"], None]] = {}

    @staticmethod
    def register(ext: str, reader: Callable[[Path], "SimpleFile"], writer: Callable[[Path, "SimpleFile"], None]) -> None:
        """
        Register a file format handler.

        ext: extension without dot, e.g. "ksp", "png"
        """
        ext = ext.lower().lstrip(".")
        FileManager._readers[ext] = reader
        FileManager._writers[ext] = writer

    @staticmethod
    def read(path: str | Path) -> "SimpleFile":
        """
        Read a file from disk and return a SimpleFile.
        """
        path = Path(path)
        ext = path.suffix.lower().lstrip(".")
        if ext not in FileManager._readers:
            raise ValueError(f"Unsupported file format: {ext}")
        reader = FileManager._readers[ext]
        return reader(path)

    @staticmethod
    def write(path: str | Path, sf: "SimpleFile") -> None:
        """
        Write a SimpleFile to disk using the appropriate format handler.
        """
        path = Path(path)
        ext = path.suffix.lower().lstrip(".")
        if ext not in FileManager._writers:
            raise ValueError(f"Unsupported file format: {ext}")
        writer = FileManager._writers[ext]
        writer(path, sf)
