from typing import Iterable, List, Tuple, Optional
import numpy as np
from PyQt6.QtCore import QPoint

from Painter.layers import Layer


import numpy as np
from typing import Union

ArrayLike = Union[np.ndarray]

# Painter/canvas.py (alpha_composite signature)
def alpha_composite(top: np.ndarray, bottom: np.ndarray, out: Optional[np.ndarray] = None) -> np.ndarray:
    if top.shape != bottom.shape:
        raise ValueError("Layer size mismatch")

    dtype = bottom.dtype
    max_val = np.iinfo(dtype).max

    # Promote to uint32 for intermediates (allocate temporaries once if needed)
    top32 = top.astype(np.uint32, copy=False)
    bot32 = bottom.astype(np.uint32, copy=False)

    top_rgb = top32[..., :3]
    top_a_raw = top32[..., 3]
    bot_rgb = bot32[..., :3]
    bot_a_raw = bot32[..., 3]

    opacity = getattr(top, "opacity", 1.0)
    if opacity != 1.0:
        top_a = ((top_a_raw.astype(np.float32) / max_val) * opacity * max_val).astype(np.uint32)
    else:
        top_a = top_a_raw

    top_rgb_p = (top_rgb * top_a) // max_val
    bot_rgb_p = (bot_rgb * bot_a_raw) // max_val

    inv_top_a = max_val - top_a
    out_a = top_a + (bot_a_raw * inv_top_a) // max_val
    out_rgb_p = top_rgb_p + (bot_rgb_p * inv_top_a) // max_val

    out_rgb = np.zeros_like(out_rgb_p, dtype=np.uint32)
    mask = out_a > 0
    if np.any(mask):
        out_rgb[mask] = (out_rgb_p[mask] * max_val) // out_a[mask, None]

    if out is None:
        out = np.empty_like(bottom, dtype=dtype)

    out[..., :3] = np.clip(out_rgb, 0, max_val).astype(dtype)
    out[..., 3] = np.clip(out_a, 0, max_val).astype(dtype)

    return out




def merge_layer_into(top: ArrayLike, bottom_layer_obj) -> None:
    """
    Merge `top` into `bottom_layer_obj` in-place. `bottom_layer_obj` must be a Layer
    instance (so we can use its unlocked() context and assignment).
    """
    # Compute merged pixels using the optimized composite
    merged = alpha_composite(top.pixels if hasattr(top, "pixels") else top,
                             bottom_layer_obj.pixels)

    # Write back into bottom layer in a single assignment inside unlocked()
    with bottom_layer_obj.unlocked():
        bottom_layer_obj[:, :, :] = merged



def merge_layers(layers: List[Layer]) -> Layer:
    """
    Merge a list of layers into the bottom-most one.
    Returns the bottom layer after merging.
    """
    if len(layers) < 1:
        raise ValueError("Need at least one layer to merge")

    bottom = layers[0]
    for top in layers[1:]:
        merge_layer_into(top, bottom)

    return bottom


class Canvas:
    """
    Represents the current working document.

    - Holds layers and the active layer index.
    - Exposes API for tools and the application manager.
    """

    def __init__(self, width: int = 800, height: int = 600, dtype=np.uint16) -> None:
        self._width = int(width)
        self._height = int(height)
        self._dtype = dtype

        self._layers: List[Layer] = []
        self._active_layer_index: int | None = None
        self._render_buf = np.empty((self._height, self._width, 4), dtype=self._dtype)


    # ---------- Core properties ----------

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def layers(self) -> List[Layer]:
        """
        Direct access to the list of layers.
        """
        return self._layers

    @property
    def active_layer_index(self) -> int | None:
        return self._active_layer_index

    @property
    def active_layer(self) -> Layer | None:
        if self._active_layer_index is None:
            return None
        if not (0 <= self._active_layer_index < len(self._layers)):
            return None
        return self._layers[self._active_layer_index]

    # ---------- Layer management ----------

    def add_layer(self, layer : Layer | None = None) -> Layer:
        """
        Append a new layer on top and make it active.
        """
        if layer is None:
            layer = Layer(self._width, self._height, dtype=self._dtype)
        self._layers.append(layer)
        self._active_layer_index = len(self._layers) - 1
        return layer

    def insert_layer(self, index: int) -> Layer:
        """
        Insert a new layer at a specific index.
        """
        index = max(0, min(index, len(self._layers)))
        layer = Layer(self._width, self._height, dtype=self._dtype)
        self._layers.insert(index, layer)
        self._active_layer_index = index
        return layer

    def remove_layer(self, index: int) -> None:
        """
        Remove a layer by index.
        """
        if not (0 <= index < len(self._layers)):
            raise IndexError("Layer index out of range")
        self._layers.pop(index)
        if not self._layers:
            self._active_layer_index = None
        else:
            self._active_layer_index = min(index, len(self._layers) - 1)

    def move_layer(self, from_index: int, to_index: int) -> None:
        """
        Reorder layers.
        """
        n = len(self._layers)
        if not (0 <= from_index < n):
            raise IndexError("from_index out of range")
        to_index = max(0, min(to_index, n - 1))

        layer = self._layers.pop(from_index)
        self._layers.insert(to_index, layer)

        # Update active index if needed
        if self._active_layer_index == from_index:
            self._active_layer_index = to_index

    def select_layer(self, index: int) -> None:
        """
        Set the active layer.
        """
        if not (0 <= index < len(self._layers)):
            raise IndexError("Layer index out of range")
        self._active_layer_index = index

    def create_layers(self, count: int) -> None:
        """
        Convenience method to create multiple layers.
        """
        for _ in range(count):
            self.add_layer()

    def render_order(self) -> Iterable[Layer]:
        """
        Generator of layers in render order (bottom to top), only visible ones.
        """
        return (layer for layer in self._layers if layer.visible)

    # ---------- Rendering ----------


    # Painter/canvas.py (replace render)
    def render(self) -> np.ndarray:
        visible = [L for L in self._layers if L.visible]
        if not visible:
            return self._render_buf  # already zeroed or set elsewhere

        np.copyto(self._render_buf, visible[0].pixels)  # single copy into prealloc
        for top in visible[1:]:
            alpha_composite(top.pixels, self._render_buf, out=self._render_buf)
        return self._render_buf

    def merge_visible_layers(self) -> Layer:
        """
        Merge all visible layers into the bottom-most visible layer.
        Returns that layer.
        """
        visible_layers = [layer for layer in self._layers if layer.visible]
        if not visible_layers:
            raise ValueError("No visible layers to merge")

        return merge_layers(visible_layers)

    @property
    def shape(self) -> Tuple[int, ...]:
        if not self._layers:
            return self._height, self._width, 4
        return self._layers[0].shape

    def set_active_last_pos(self, value : QPoint | None) -> None:
        if self._layers and type(value) is QPoint or type(value) is type(None):
            self.layers[self._active_layer_index].last_pos = value