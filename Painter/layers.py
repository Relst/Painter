from collections import deque

import numpy as np
from functools import wraps
from contextlib import contextmanager

from PyQt6.QtCore import QPoint

# Optional numba JIT
try:
    from numba import njit
    _NUMBA_AVAILABLE = True
except Exception:
    _NUMBA_AVAILABLE = False


def requires_unlocked(fn):
    """
    Decorator prevents mutation when the layer is locked.
    """
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        if self._locked:
            raise RuntimeError(f"{self.__class__.__name__} is locked")
        return fn(self, *args, **kwargs)
    return wrapper


class Layer:
    """
    A single RGBA layer.

    - Owns pixel data and all pixel-level operations.
    - Canvas and tools call into this class to modify pixels.
    """

    def __init__(self, width: int, height: int, dtype: np.dtype = np.uint16) -> None:
        self._cached_mask = None
        self._width = int(width)
        self._height = int(height)
        self._dtype = dtype

        # Data layout: (H, W, 4) RGBA
        self._max_val = np.iinfo(self._dtype).max
        self._data = np.full(
            (self._height, self._width, 4),
            dtype=self._dtype,
            fill_value=self._max_val,
        )  # default white, opaque

        self._visible = True
        self._locked = False
        self._opacity = 1.0
        self._last_pos: QPoint | None = None

        # brush cache
        self._cached_brush_size = None
        self._cached_radius = None
        self.pixel_points = deque(maxlen=10)
        self._interpolation_alpha = np.iinfo(self._dtype).max

    # ---------- Core properties ----------

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def shape(self):
        return self._data.shape

    @property
    def dtype(self):
        return self._dtype

    @dtype.setter
    @requires_unlocked
    def dtype(self, dtype: np.dtype):
        """
        Change underlying dtype and convert existing data.
        """
        self._dtype = dtype
        self._data = self._data.astype(dtype)

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: bool):
        self._visible = bool(value)

    @property
    def opacity(self) -> float:
        return self._opacity

    @opacity.setter
    def opacity(self, value: float):
        """
        Clamped opacity to [0, 1].
        """
        self._opacity = float(np.clip(value, 0.0, 1.0))

    @property
    def locked(self) -> bool:
        return self._locked

    @locked.setter
    def locked(self, value: bool):
        self._locked = bool(value)

    # ---------- Lock context ----------

    @contextmanager
    def unlocked(self):
        """
        Temporarily unlock the layer inside a context.
        Useful for engine-level overrides.
        """
        was_locked = self._locked
        self._locked = False
        try:
            yield self
        finally:
            self._locked = was_locked

    # ---------- Pixel access ----------

    def __getitem__(self, key):
        """
        Read-only access to pixel data via slicing.
        """
        return self._data[key]

    @requires_unlocked
    def __setitem__(self, key, value):
        """
        Direct pixel write access via slicing.
        """
        self._data[key] = value

    @property
    def pixels(self) -> np.ndarray:
        """
        Returns a read-only view of the pixel buffer.
        """
        view = self._data.view()
        view.setflags(write=False)
        return view

    @requires_unlocked
    def set_region(self, key, value):
        """
        Convenience method for setting a region of pixels if direct indexing becomes obsolete.
        """
        self._data[key] = value

    # ---------- Utility / info ----------

    def __len__(self):
        return self._width * self._height

    def __iter__(self):
        return iter(self._data)

    def __str__(self):
        return (
            f"{self.__class__.__name__}\n"
            f" Width: {self._width}\n"
            f" Height: {self._height}\n"
            f" Data Type: {self._dtype}"
        )

    # ---------- High-level operations ----------

    @requires_unlocked
    def reset(self, rgba : np.ndarray | None = None):
        """
        Reset the layer to a solid color.
        If alpha is None, keep existing alpha.
        """
        if rgba is None:
            maxv = np.iinfo(self._dtype).max
            rgba = np.array((maxv, maxv, maxv, maxv), dtype=self._dtype)
        r, g, b, a = rgba
        self._data[..., 0] = r
        self._data[..., 1] = g
        self._data[..., 2] = b
        if a is not None:
            self._data[..., 3] = a

    @requires_unlocked
    def resize(self, width: int, height: int):
        """
        Resize the layer. For now, this just resets the buffer.
        You can later implement resampling here.
        """
        self._width = int(width)
        self._height = int(height)
        self._data = np.zeros((self._height, self._width, 4), dtype=self._dtype)
        self._data[..., :3] = 255
        self._data[..., 3] = np.iinfo(self._dtype).max

    @requires_unlocked
    def fill(self, rgba: tuple[int, int, int, int]):
        """
        Fill the entire layer with a single RGBA color.
        """
        r, g, b, a = rgba
        self._data[..., 0] = r
        self._data[..., 1] = g
        self._data[..., 2] = b
        self._data[..., 3] = a

    # ---------- Stroke rasterization helpers ----------

    if _NUMBA_AVAILABLE:
        @staticmethod
        @njit
        def _stroke_capsule_mask(h, w, x0, y0, lx, ly, x, y, r):
            """
            Build a boolean mask for a capsule-shaped stroke segment inside region [y0:y1, x0:x1].
            (lx, ly) -> (x, y) is the segment, r is radius.
            """
            mask = np.zeros((h, w), dtype=np.bool_)
            dx = x - lx
            dy = y - ly
            seg_len2 = dx * dx + dy * dy

            for j in range(h):
                py = y0 + j
                for i in range(w):
                    px = x0 + i

                    if seg_len2 == 0:
                        # just a circle at (x, y)
                        ddx = px - x
                        ddy = py - y
                        if ddx * ddx + ddy * ddy <= r * r:
                            mask[j, i] = True
                        continue

                    # project point onto segment
                    t = ((px - lx) * dx + (py - ly) * dy) / seg_len2
                    if t < 0.0:
                        cx = lx
                        cy = ly
                    elif t > 1.0:
                        cx = x
                        cy = y
                    else:
                        cx = lx + t * dx
                        cy = ly + t * dy

                    ddx = px - cx
                    ddy = py - cy
                    if ddx * ddx + ddy * ddy <= r * r:
                        mask[j, i] = True

            return mask

    @staticmethod
    def _stroke_capsule_mask_py(h, w, x0, y0, lx, ly, x, y, r):
        """
        Pure Python/numpy version of capsule mask.
        """
        yy, xx = np.mgrid[0:h, 0:w]
        px = x0 + xx
        py = y0 + yy

        dx = x - lx
        dy = y - ly
        seg_len2 = dx * dx + dy * dy

        if seg_len2 == 0:
            ddx = px - x
            ddy = py - y
            return (ddx * ddx + ddy * ddy) <= r * r

        # projection factor t along segment
        t = ((px - lx) * dx + (py - ly) * dy) / seg_len2
        t = np.clip(t, 0.0, 1.0)
        cx = lx + t * dx
        cy = ly + t * dy

        ddx = px - cx
        ddy = py - cy
        return (ddx * ddx + ddy * ddy) <= r * r

    # ---------- Brush drawing (capsule stroke, no repeated stamping) ----------

    @requires_unlocked
    def draw_brush(self, x: int, y: int, size: int, color: tuple[int, int, int, int]):
        """
        Draw a continuous stroke segment from last_pos to (x, y) using a circular brush
        of given size, rasterized as a capsule. Each pixel in the swept area is written
        at most once.
        """
        h, w, _ = self._data.shape
        r = size // 2

        # First point in stroke: just draw a circle
        if self._last_pos is None:
            cx = int(x)
            cy = int(y)

            x0 = max(cx - r, 0)
            y0 = max(cy - r, 0)
            x1 = min(cx + r + 1, w)
            y1 = min(cy + r + 1, h)

            region = self._data[y0:y1, x0:x1]
            rh = y1 - y0
            rw = x1 - x0

            if rh <= 0 or rw <= 0:
                self._last_pos = QPoint(x, y)
                return (x0, y0, x1, y1)

            yy, xx = np.mgrid[0:rh, 0:rw]
            px = x0 + xx
            py = y0 + yy
            ddx = px - cx
            ddy = py - cy
            mask = (ddx * ddx + ddy * ddy) <= r * r

            r_c, g_c, b_c, a_c = color
            region[mask, 0] = r_c
            region[mask, 1] = g_c
            region[mask, 2] = b_c
            region[mask, 3] = a_c

            self._last_pos = QPoint(x, y)
            return (x0, y0, x1, y1)

        # Subsequent points: rasterize capsule between last_pos and (x, y)
        lx = int(self._last_pos.x())
        ly = int(self._last_pos.y())
        x = int(x)
        y = int(y)

        # bounding box of segment + radius
        x0 = max(min(lx, x) - r, 0)
        y0 = max(min(ly, y) - r, 0)
        x1 = min(max(lx, x) + r + 1, w)
        y1 = min(max(ly, y) + r + 1, h)

        rh = y1 - y0
        rw = x1 - x0
        if rh <= 0 or rw <= 0:
            self._last_pos = QPoint(x, y)
            return (x0, y0, x1, y1)

        region = self._data[y0:y1, x0:x1]

        if _NUMBA_AVAILABLE:
            mask = Layer._stroke_capsule_mask(rh, rw, x0, y0, lx, ly, x, y, r)
        else:
            mask = Layer._stroke_capsule_mask_py(rh, rw, x0, y0, lx, ly, x, y, r)

        r_c, g_c, b_c, a_c = color
        region[mask, 0] = r_c
        region[mask, 1] = g_c
        region[mask, 2] = b_c
        region[mask, 3] = a_c

        self._last_pos = QPoint(x, y)
        return (x0, y0, x1, y1)

    # ---------- Stroke state ----------

    @requires_unlocked
    def draw_brush_slow(self, x: int, y: int, size: int, color):
        r = size // 2
        h, w, _ = self._data.shape

        x0 = max(x - r, 0)
        y0 = max(y - r, 0)
        x1 = min(x + r + 1, w)
        y1 = min(y + r + 1, h)

        region = self._data[y0:y1, x0:x1]
        rh = y1 - y0
        rw = x1 - x0
        if rh <= 0 or rw <= 0:
            return

        yy, xx = np.mgrid[0:rh, 0:rw]
        px = x0 + xx
        py = y0 + yy
        mask = (px - x) ** 2 + (py - y) ** 2 <= r * r

        r_c, g_c, b_c, a_c = color
        region[mask, 0] = r_c
        region[mask, 1] = g_c
        region[mask, 2] = b_c
        region[mask, 3] = a_c

    @requires_unlocked
    def draw_spline_brush(self, x: int, y: int, size: int, color: tuple[int, int, int, int]):
        pts = self.pixel_points
        x, y = self._smoothed_point(x, y)
        pts.append((x, y))

        if len(pts) < 4:
            return

        p0, p1, p2, p3 = pts[-4], pts[-3], pts[-2], pts[-1]

        # Vectorized cubic spline interpolation
        # Step count based on distance between p1 and p2, but limited for performance
        dist = max(abs(p2[0] - p1[0]), abs(p2[1] - p1[1]), 1)

        # If brush is large, reduce steps to avoid calling draw_brush too often
        # This keeps the spline smooth but avoids thousands of calls for huge brushes
        max_steps = 200  # adjust as needed
        steps = min(dist, max_steps)

        t = np.linspace(0, 1, steps)
        t2 = t * t
        t3 = t2 * t

        xt = 0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (
                    -p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
        yt = 0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (
                    -p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)

        # Round to ints for draw_brush
        xt = np.round(xt).astype(int)
        yt = np.round(yt).astype(int)

        # Draw brush only at points that are far enough from previous
        last_draw = None
        for xi, yi in zip(xt, yt):
            if last_draw is None or abs(xi - last_draw[0]) + abs(yi - last_draw[1]) >= max(1, size // 4):
                self.draw_brush(xi, yi, size, color)
                last_draw = (xi, yi)

    def reset_stroke(self):
        self.pixel_points.clear()

    @property
    def last_pos(self) -> QPoint:
        return self._last_pos

    @last_pos.setter
    def last_pos(self, pos: QPoint | None) -> None:
        if isinstance(pos, QPoint):
            self._last_pos = pos
        else:
            self._last_pos = None

    @property
    def interpolation_alpha(self):
        return self._interpolation_alpha

    @interpolation_alpha.setter
    def interpolation_alpha(self, alpha):
        self._interpolation_alpha = np.clip(
            alpha, 0, np.iinfo(self._dtype).max
        )

    def _smoothed_point(self, x, y):
        if not self.pixel_points:
            return x, y

        last_x, last_y = self.pixel_points[-1]
        a = self.interpolation_alpha / np.iinfo(self._dtype).max

        sx = int(last_x + a * (x - last_x))
        sy = int(last_y + a * (y - last_y))
        return sx, sy


