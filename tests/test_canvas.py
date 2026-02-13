import pytest
import numpy as np
from Painter.layers import Layer
from Painter.canvas import Canvas, merge_layer_into, merge_layers, alpha_composite

@pytest.fixture
def simple_layer():
    l = Layer(4, 4, dtype=np.uint8)
    l.reset((100, 150, 200, 255))  # RGBA
    return l

@pytest.fixture
def canvas_4x4():
    return Canvas(4, 4)

# ----------------------
# Layer Encapsulation
# ----------------------
def test_layer_read_only_data(simple_layer):
    data = simple_layer.pixels
    with pytest.raises(ValueError):
        data[0, 0, 0] = 123  # read-only view should fail

def test_locked_layer_setitem(simple_layer):
    simple_layer._locked = True
    with pytest.raises(RuntimeError):
        simple_layer[0, 0] = (0, 0, 0, 0)

def test_unlocked_context_allows_mutation(simple_layer):
    simple_layer._locked = True
    with simple_layer.unlocked():
        simple_layer[0, 0] = (1, 2, 3, 4)
    assert tuple(simple_layer[0, 0]) == (1, 2, 3, 4)

# ----------------------
# Layer opacity and compositing
# ----------------------
def test_alpha_composite_respects_opacity():
    bottom = Layer(2, 2, dtype=np.uint8)
    bottom.reset((0, 0, 0, 255))
    top = Layer(2, 2, dtype=np.uint8)
    top.reset((255, 0, 0, 255))
    top.opacity = 0.5

    result = alpha_composite(top, bottom)
    # pixel should be roughly halfway between black and red
    assert np.all(result[..., 0] > 120) and np.all(result[..., 0] < 140)
    assert np.all(result[..., 1] == 0)
    assert np.all(result[..., 2] == 0)

def test_alpha_composite_respects_visibility():
    bottom = Layer(2, 2, dtype=np.uint8)
    bottom.reset((0, 0, 0, 255))
    top = Layer(2, 2, dtype=np.uint8)
    top.reset((255, 255, 255, 255))
    top.visible = False

    result = alpha_composite(top, bottom)
    # Should be identical to bottom
    np.testing.assert_array_equal(result, bottom[:, :, :])

# ----------------------
# Canvas layer management
# ----------------------
def test_canvas_create_and_move_layers(canvas_4x4):
    c = canvas_4x4
    l1 = c.create_layer()
    l2 = c.create_layer()
    assert len(list(c.render_order())) == 2
    c.move_layer(0, 1)
    layers = list(c.render_order())
    assert layers[1] is l1  # l1 moved to top visually

def test_merge_layers_obeys_order():
    l_bottom = Layer(2, 2, dtype=np.uint8)
    l_bottom.reset((0, 0, 0, 255))
    l_middle = Layer(2, 2, dtype=np.uint8)
    l_middle.reset((255, 0, 0, 255))
    l_middle.opacity = 0.5
    l_top = Layer(2, 2, dtype=np.uint8)
    l_top.reset((0, 255, 0, 255))
    l_top.opacity = 0.5

    merged = merge_layers([l_bottom, l_middle, l_top])
    # Bottom layer survives
    assert merged is l_bottom
    # Topmost pixel should be greenish due to layering order
    g_val = merged[0, 0, 1]
    r_val = merged[0, 0, 0]
    assert g_val > r_val

def test_merge_layer_into_respects_visibility():
    bottom = Layer(2, 2, dtype=np.uint8)
    bottom.reset((0, 0, 0, 255))
    top = Layer(2, 2, dtype=np.uint8)
    top.reset((255, 255, 255, 255))
    top.visible = False

    merge_layer_into(top, bottom)
    # Bottom should be unchanged
    np.testing.assert_array_equal(bottom[:, :, :], np.zeros((2, 2, 4), dtype=np.uint8) + np.array([0,0,0,255], dtype=np.uint8))
