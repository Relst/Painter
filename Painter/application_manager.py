from pathlib import Path

from PyQt6.QtCore import QPoint

from Painter.simple_file import SimpleFile
from Painter.file_manager import FileManager
from Painter.formats.ksp import read_ksp, write_ksp
from Painter.formats.png import read_png, write_png


class PaintAppManager:
    """
    Main application façade.

    - Owns the current SimpleFile (document).
    - Exposes high-level operations for the UI.
    - Does not expose low-level pixel details directly.
    """

    def __init__(self):
        # Register formats once
        FileManager.register("ksp", read_ksp, write_ksp)
        FileManager.register("png", read_png, write_png)

        self._file_ref: SimpleFile | None = None
        self._save_dir = self._resolve_save_dir()
        self._last_pos : QPoint | None = None

    # ---------- Internal helpers ----------

    @staticmethod
    def _resolve_save_dir() -> Path:
        """
        Default directory for saving files.
        """
        save_dir = Path.cwd() / "FILES"
        save_dir.mkdir(parents=True, exist_ok=True)
        return save_dir

    @property
    def file(self) -> SimpleFile:
        """
        Current document. Raises if none is loaded.
        """
        if self._file_ref is None:
            raise RuntimeError("No file loaded")
        return self._file_ref

    # ---------- Document lifecycle ----------

    def new_document(self, name="untitled_document", width=800, height=600, filetype="ksp") -> SimpleFile:
        """
        Create a new document and make it current.
        """
        self._file_ref = SimpleFile(name, width, height, filetype=filetype)
        # Start with one layer
        self._file_ref.add_layer()
        return self._file_ref

    def open_document(self, path: str | Path) -> SimpleFile:
        """
        Open an existing document from disk.
        """
        path = Path(path).expanduser()
        if not path.is_absolute():
            path = self._save_dir / path

        self._file_ref = SimpleFile.load(path)
        return self._file_ref

    def save_document(self, path: str | Path | None = None) -> Path:
        """
        Save the current document.
        If path is None, uses the document's name and filetype in the default save dir.
        """
        if self._file_ref is None:
            raise RuntimeError("No file to save")

        if path is None:
            path = self._save_dir / f"{self._file_ref.name}.{self._file_ref.filetype}"
        else:
            path = Path(path).expanduser()
            if not path.is_absolute():
                path = self._save_dir / path

        return self._file_ref.save(path)

    def export_png(self, path: str | Path | None = None) -> Path:
        """
        Convenience method to export the current document as PNG.
        """
        if self._file_ref is None:
            raise RuntimeError("No file to export")

        if path is None:
            path = self._save_dir / f"{self._file_ref.name}.png"
        else:
            path = Path(path).expanduser()
            if not path.is_absolute():
                path = self._save_dir / path

        return self._file_ref.export(path, "png")

    # ---------- Canvas / layer operations ----------

    def select_layer(self, index: int) -> None:
        self.file.canvas.select_layer(index)

    def add_layer(self):
        return self.file.canvas.add_layer()

    def move_layer(self, from_index: int, to_index: int) -> None:
        self.file.canvas.move_layer(from_index, to_index)

    # ---------- Drawing operations ----------

    def draw_brush(self, x: int, y: int, size: int, color: tuple[int, int, int, int]):
        """
        Draw with a brush on the active layer.
        """
        layer = self.file.canvas.active_layer
        if layer is None:
            raise RuntimeError("No active layer")
        layer.draw_brush(x, y, size, color)

    def draw_spline_brush(self, x: int, y: int, size: int, color: tuple[int, int, int, int]):
        """
        Draw with a brush on the active layer.
        """
        layer = self.file.canvas.active_layer
        if layer is None:
            raise RuntimeError("No active layer")
        layer.draw_spline_brush(x, y, size, color)

    def fill_active_layer(self, rgba: tuple[int, int, int, int]):
        """
        Fill the active layer with a solid color.
        """
        layer = self.file.canvas.active_layer
        if layer is None:
            raise RuntimeError("No active layer")
        layer.fill(rgba)

    # ---------- Rendering for UI ----------

    def render(self):
        """
        Render the current document to an RGBA buffer for display.
        """
        return self.file.canvas.render()
