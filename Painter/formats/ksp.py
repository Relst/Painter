from pathlib import Path
import struct
import zlib
import numpy as np

from Painter.simple_file import SimpleFile
from Painter.layers import Layer


def write_ksp(path: Path, sf: SimpleFile) -> None:
    """
    Write a SimpleFile to a custom KSP format.

    Layout:
    - Header: magic, width, height, channels, dtype_code, compression_flag, num_layers
    - Payload: concatenated raw layer buffers (RGBA uint16)
    """
    layers_data = []
    for layer in sf.layers:
        # Ensure uint16 RGBA
        data = layer.pixels.astype(np.uint16)
        layers_data.append(data.tobytes())

    payload = b"".join(layers_data)
    compression = 1
    payload = zlib.compress(payload)

    header = struct.pack(
        "<4sIIBBBH",
        b"KSP1",
        sf.width,
        sf.height,
        4,  # RGBA
        2,  # uint16
        compression,
        len(sf.layers),
    )

    with open(path, "wb") as f:
        f.write(header)
        f.write(payload)


def read_ksp(path: Path) -> SimpleFile:
    """
    Read a KSP file and return a SimpleFile.
    """
    with open(path, "rb") as f:
        magic, w, h, c, dtype_code, compression, num_layers = struct.unpack(
            "<4sIIBBBH", f.read(17)
        )
        payload = f.read()

    if magic != b"KSP1":
        #First 4 bytes detail the custom format + version
        raise ValueError("Invalid KSP file")
    if c != 4 or dtype_code != 2:
        raise ValueError("Unsupported KSP pixel format")

    if compression:
        payload = zlib.decompress(payload)

    layer_size = w * h * 4 * 2  # RGBA * uint16
    sf = SimpleFile(path.stem, w, h, filetype="ksp")
    print(sf.layers)
    sf.canvas.layers.clear()


    for i in range(num_layers):
        offset = i * layer_size
        layer_data = np.frombuffer(
            payload[offset : offset + layer_size], dtype=np.uint16
        ).reshape(h, w, 4)
        layer = Layer(w, h, dtype=np.uint16)
        with layer.unlocked():
            layer[:, :, :] = layer_data
        sf.add_layer(layer)
    print(sf.layers)
    return sf
