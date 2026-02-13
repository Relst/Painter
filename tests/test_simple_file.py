import numpy as np
from Painter.simple_file import SimpleFile


def test_file_dimensions():
    f = SimpleFile("test", 320, 240)
    data = f.data

    assert data.shape == (240, 320, 3)

def test_file_initial_color():
    f = SimpleFile()
    data = f.data

    assert np.all(data == 255)

def test_dtype():
    f = SimpleFile()
    assert f.data.dtype == np.uint16
