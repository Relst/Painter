from pathlib import Path
import numpy as np
from PIL import Image

from Painter.simple_file import SimpleFile
from Painter.layers import Layer
from Painter.canvas import merge_layers


def write_png(path: Path, sf: SimpleFile) -> None:
    """
    Export a SimpleFile as a PNG with full RGBA support.
    """
    if not sf.layers:
        # Transparent blank image
        data = np.zeros((sf.height, sf.width, 4), dtype=np.uint8)
    else:
        merged = merge_layers(sf.layers)
        data = merged.pixels  # keep RGBA

        # Convert to 8-bit
        if data.dtype != np.uint8:
            max_val = np.iinfo(data.dtype).max
            data = (data.astype(np.float32) / max_val * 255).astype(np.uint8)

    # Save as RGBA PNG
    Image.fromarray(data, "RGBA").save(path)



def read_png(path: Path) -> SimpleFile:
    """
    Open a PNG as a SimpleFile with a single RGBA layer.
    """
    img = Image.open(path).convert("RGBA")
    data = np.array(img)
    h, w, _ = data.shape

    sf = SimpleFile(path.stem, w, h, filetype="png")
    layer = sf.add_layer()

    with layer.unlocked():
        # Convert 8-bit → uint16 internal format
        data16 = (data.astype(np.float32) / 255 * np.iinfo(layer.dtype).max).astype(layer.dtype)
        layer[:, :, :] = data16

    return sf

