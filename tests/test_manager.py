import numpy as np
from pathlib import Path
import pytest
from Painter.application_manager import PaintAppManager
from Painter.simple_file import SimpleFile

UNSUPPORTED_FILE_TYPES  = [".bmp", ".jpg", ".tiff"]


def test_create_file():
    mgr = PaintAppManager()
    f = mgr.create_file("hello", 100, 50)

    assert isinstance(f, SimpleFile)
    assert f.name == "hello"
    assert f.width == 100
    assert f.height == 50
    assert f.data.shape == (50, 100, 3)
    assert f.data.dtype == np.uint16

def test_save_and_read_ksp(tmp_path, monkeypatch):
    mgr = PaintAppManager()

    monkeypatch.setattr(mgr, "_save_dir", tmp_path)

    f = mgr.create_file("img", 16, 16)

    # Write deterministic data
    data = f.data
    data[:] = np.arange(data.size, dtype=np.uint16).reshape(data.shape)

    path = mgr.save_file("img.ksp", compress=False)

    assert path.exists()
    assert path.suffix == ".ksp"

    loaded = mgr.read_file(path)

    assert isinstance(loaded, SimpleFile)
    assert loaded.width == 16
    assert loaded.height == 16
    np.testing.assert_array_equal(loaded.data, data)

def test_save_and_read_ksp_compressed(tmp_path, monkeypatch):
    mgr = PaintAppManager()
    monkeypatch.setattr(mgr, "_save_dir", tmp_path)

    f = mgr.create_file("compressed", 32, 32)
    f.data[:] = 12345

    path = mgr.save_file("compressed.ksp", compress=True)
    loaded = mgr.read_file(path)

    np.testing.assert_array_equal(
        loaded.data,
        f.data
    )

def test_save_and_read_png(tmp_path, monkeypatch):
    mgr = PaintAppManager()
    monkeypatch.setattr(mgr, "_save_dir", tmp_path)

    f = mgr.create_file("img_png", 20, 10)

    # PNG path forces uint8 conversion
    f.data[:] = 200

    path = mgr.save_file("img_png.png")

    assert path.exists()
    assert path.suffix == ".png"

    loaded = mgr.read_file(path)

    assert loaded.width == 20
    assert loaded.height == 10

    # PNG loads back into uint16 internal format
    np.testing.assert_array_equal(
        loaded.data,
        f.data
    )

def test_absolute_path_save_and_load(tmp_path):
    mgr = PaintAppManager()

    f = mgr.create_file("abs", 8, 8)
    f.data[:] = 42

    abs_path = tmp_path / "absolute.ksp"

    saved_path = mgr.save_file(abs_path)

    assert saved_path.is_absolute()
    assert saved_path.exists()

    loaded = mgr.read_file(abs_path)

    np.testing.assert_array_equal(
        loaded.data,
        f.data
    )
@pytest.mark.parametrize("ext", UNSUPPORTED_FILE_TYPES)
def test_read_unsupported_extension(tmp_path, ext):
    mgr = PaintAppManager()

    bad_file = tmp_path / f"bad{ext}"
    bad_file.write_text("nope")

    with pytest.raises(ValueError, match="Unsupported file format"):
        mgr.read_file(bad_file)

@pytest.mark.parametrize("ext", UNSUPPORTED_FILE_TYPES)
def test_save_unsupported_extension(ext):
    mgr = PaintAppManager()
    mgr.create_file("bad", 4, 4)

    with pytest.raises(ValueError, match="Unsupported file format"):
        mgr.save_file(f"bad{ext}")



def test_read_updates_internal_reference(tmp_path, monkeypatch):
    mgr = PaintAppManager()
    monkeypatch.setattr(mgr, "_save_dir", tmp_path)

    original = mgr.create_file("state", 5, 5)
    original.data[:] = 99

    path = mgr.save_file("state.ksp")

    new_file = mgr.read_file(path)

    assert mgr._file_ref is new_file
    np.testing.assert_array_equal(
        new_file.data,
        original.data
    )
