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
        data16 = (data.astype(np.float32) / 255 * np.iinfo(layer.dtype).max).astype(layer.dtype)
        layer[:] = center_pad_to_shape(data16, layer.height, layer.width)

    print("sflayers", sf.layers)

    return sf




def center_pad_to_shape(img, target_h, target_w):
    img_h, img_w = img.shape[:2]

    # Crop center
    y1 = max(0, (img_h - target_h) // 2)
    x1 = max(0, (img_w - target_w) // 2)
    img = img[y1:y1 + min(img_h, target_h),
              x1:x1 + min(img_w, target_w)]

    # Pad center
    pad_y = target_h - img.shape[0]
    pad_x = target_w - img.shape[1]

    return np.pad(
        img,
        ((pad_y // 2, pad_y - pad_y // 2),
         (pad_x // 2, pad_x - pad_x // 2),
         (0, 0)),
        mode="constant", constant_values=np.iinfo(img.dtype).max
    )
