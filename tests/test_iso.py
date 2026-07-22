# tests/test_iso.py
"""Тесты изометрической проекции core/iso.py (чистая математика, без GL)."""
import math

from core.iso import (
    world_to_screen, screen_to_world, depth,
    ISO_SCALE_X, ISO_SCALE_Y,
)


def test_origin_maps_to_origin():
    assert world_to_screen(0, 0) == (0.0, 0.0)


def test_round_trip_forward_back():
    """screen_to_world(world_to_screen(p)) == p для набора точек."""
    points = [(0, 0), (100, 0), (0, 100), (325, 130),
              (-500, 200), (1234.5, -678.25), (65, 65)]
    for wx, wy in points:
        sx, sy = world_to_screen(wx, wy)
        rx, ry = screen_to_world(sx, sy)
        assert math.isclose(rx, wx, abs_tol=1e-6), (wx, wy, rx)
        assert math.isclose(ry, wy, abs_tol=1e-6), (wx, wy, ry)


def test_round_trip_back_forward():
    """world_to_screen(screen_to_world(p)) == p для экранных точек."""
    points = [(0, 0), (200, 100), (-300, 50), (17.5, -42.0)]
    for sx, sy in points:
        wx, wy = screen_to_world(sx, sy)
        rx, ry = world_to_screen(wx, wy)
        assert math.isclose(rx, sx, abs_tol=1e-6), (sx, sy, rx)
        assert math.isclose(ry, sy, abs_tol=1e-6), (sx, sy, ry)


def test_pure_x_axis_goes_right_and_down():
    """+X мира уходит вправо (+sx) и вниз (+sy) на экране."""
    sx, sy = world_to_screen(100, 0)
    assert sx > 0
    assert sy > 0


def test_pure_y_axis_goes_left_and_down():
    """+Y мира уходит влево (-sx) и вниз (+sy) на экране."""
    sx, sy = world_to_screen(0, 100)
    assert sx < 0
    assert sy > 0


def test_diamond_aspect_ratio_2_to_1():
    """Тайл ts x ts проецируется в ромб шириной ts и высотой ts/2."""
    ts = 64
    # Четыре угла клетки в мировых пикселях
    corners = [(0, 0), (ts, 0), (ts, ts), (0, ts)]
    pts = [world_to_screen(x, y) for x, y in corners]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    width = max(xs) - min(xs)
    height = max(ys) - min(ys)
    assert math.isclose(width, ts, abs_tol=1e-6)
    assert math.isclose(height, ts / 2, abs_tol=1e-6)


def test_depth_increases_toward_camera():
    """Объект с большим (x+y) ближе к камере (рисуется поверх)."""
    assert depth(0, 0) < depth(100, 0)
    assert depth(100, 0) < depth(100, 100)
    # depth монотонен по сумме координат
    assert depth(50, 50) == depth(0, 100) == depth(100, 0)


def test_scale_constants_consistent():
    """Обратная проекция согласована с прямыми коэффициентами."""
    assert ISO_SCALE_X > 0 and ISO_SCALE_Y > 0
    # Высота ромба вдвое меньше ширины -> ISO_SCALE_Y = ISO_SCALE_X / 2
    assert math.isclose(ISO_SCALE_Y, ISO_SCALE_X / 2, abs_tol=1e-9)
