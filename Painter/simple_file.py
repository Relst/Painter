from pathlib import Path


from Painter.canvas import Canvas
from Painter.file_manager import FileManager
from Painter.layers import Layer


class SimpleFile:
    """
    Document descriptor for the paint app.

    - Holds metadata (name, filetype).
    - Owns a Canvas (layers, pixels).
    - Delegates actual reading/writing to FileManager.
    """

    def __init__(
        self,
        name: str = "untitled_document",
        width: int = 800,
        height: int = 600,
        filetype: str = "ksp",
    ):
        self.name = name
        self.filetype = filetype  # e.g. "ksp", "png"
        self.canvas = Canvas(width, height)

    @property
    def width(self) -> int:
        return self.canvas.width

    @property
    def height(self) -> int:
        return self.canvas.height

    @property
    def layers(self):
        return self.canvas.layers

    @property
    def shape(self):
        return self.canvas.shape

    # ---------- File operations ----------

    @classmethod
    def load(cls, path: str | Path) -> "SimpleFile":
        """
        Load a SimpleFile from disk using FileManager.
        """
        return FileManager.read(path)

    def save(self, path: str | Path | None = None) -> Path:
        """
        Save this document to disk.
        If path is None, uses self.name and self.filetype.
        """
        if path is None:
            path = Path(f"{self.name}.{self.filetype}")
        path = Path(path)
        FileManager.write(path, self)
        return path

    def export(self, path: str | Path, format: str) -> Path:
        """
        Export this document to a different format.
        """
        path = Path(path)
        # Override extension based on requested format
        path = path.with_suffix(f".{format.lower()}")
        FileManager.write(path, self)
        return path

    # ---------- Convenience layer methods ----------

    def add_layer(self, layer: Layer = None) -> Layer:
        return self.canvas.add_layer(layer)

    def create_layers(self, count: int):
        self.canvas.create_layers(count)
