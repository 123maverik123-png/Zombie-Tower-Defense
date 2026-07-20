# tests/test_gl_core.py
"""Тесты ядра GPU-рендера на standalone-контексте (без окна).

Проверяют: упаковку атласа, порядок каналов (swizzle), геометрию батча,
рендер в FBO с чтением пикселей.
"""
import numpy as np
import pygame
import pytest

moderngl = pytest.importorskip("moderngl")

from core.opengl.atlas import TextureAtlas, PAGE_SIZE, surface_swizzle
from core.opengl.batch import SpriteBatch, BLEND_ADDITIVE


@pytest.fixture(scope="module")
def ctx():
    pygame.init()
    try:
        c = moderngl.create_context(standalone=True)
    except Exception:
        pytest.skip("Нет OpenGL контекста (headless без GPU)")
    c.enable(moderngl.BLEND)
    c.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
    yield c
    c.release()


@pytest.fixture()
def fbo(ctx):
    fbo = ctx.framebuffer(color_attachments=[ctx.texture((64, 64), 4)])
    fbo.use()
    fbo.clear(0.0, 0.0, 0.0, 1.0)
    yield fbo
    fbo.release()


def solid(color, size=(4, 4)):
    s = pygame.Surface(size, pygame.SRCALPHA, 32)
    s.fill(color)
    return s


def read_pixel(fbo, x, y):
    data = np.frombuffer(fbo.read(components=4), dtype=np.uint8).reshape(64, 64, 4)
    return data[63 - y, x]  # fbo.read отдаёт снизу вверх


class TestAtlas:
    def test_pack_and_regions(self, ctx):
        atlas = TextureAtlas(ctx)
        r1 = atlas.add("a", solid((255, 0, 0, 255), (10, 10)))
        r2 = atlas.add("b", solid((0, 255, 0, 255), (20, 8)))
        assert r1.w == 10 and r2.w == 20
        # Регионы не пересекаются
        assert (r1.x + r1.w <= r2.x or r2.x + r2.w <= r1.x
                or r1.y + r1.h <= r2.y or r2.y + r2.h <= r1.y)
        # UV в пределах [0,1]
        for r in (r1, r2):
            assert 0 <= r.u0 < r.u1 <= 1
            assert 0 <= r.v0 < r.v1 <= 1
        atlas.destroy()

    def test_add_idempotent(self, ctx):
        atlas = TextureAtlas(ctx)
        r1 = atlas.add("same", solid((1, 2, 3, 255)))
        r2 = atlas.add("same", solid((9, 9, 9, 255)))
        assert r1 is r2
        atlas.destroy()

    def test_overflow_creates_new_page(self, ctx):
        atlas = TextureAtlas(ctx)
        big = PAGE_SIZE // 2 + 10
        for i in range(4):
            atlas.add(f"big{i}", solid((255, 255, 255, 255), (big, big)))
        assert len(atlas.pages) >= 2
        atlas.destroy()

    def test_swizzle_string_valid(self):
        s = pygame.Surface((2, 2), pygame.SRCALPHA, 32)
        sw = surface_swizzle(s)
        assert sorted(sw) == ['A', 'B', 'G', 'R']


class TestBatchRender:
    def test_colors_correct_after_swizzle(self, ctx, fbo):
        """Красный спрайт должен отрендериться красным — проверка порядка каналов."""
        atlas = TextureAtlas(ctx)
        batch = SpriteBatch(ctx, atlas, 64, 64)
        region = atlas.add("red", solid((255, 0, 0, 255)))

        batch.draw(region, 32, 32, 20, 20)
        batch.flush()

        px = read_pixel(fbo, 32, 32)
        assert px[0] > 200 and px[1] < 50 and px[2] < 50, f"Ожидался красный, получен {px}"
        batch.destroy()
        atlas.destroy()

    def test_draw_rect_white_pixel(self, ctx, fbo):
        atlas = TextureAtlas(ctx)
        batch = SpriteBatch(ctx, atlas, 64, 64)
        batch.draw_rect(10, 10, 30, 30, (0, 255, 0, 255))
        batch.flush()
        px = read_pixel(fbo, 25, 25)
        assert px[1] > 200 and px[0] < 50, f"Ожидался зелёный, получен {px}"
        batch.destroy()
        atlas.destroy()

    def test_alpha_blending(self, ctx, fbo):
        atlas = TextureAtlas(ctx)
        batch = SpriteBatch(ctx, atlas, 64, 64)
        batch.draw_rect(0, 0, 64, 64, (255, 255, 255, 255))
        batch.draw_rect(0, 0, 64, 64, (0, 0, 255, 128))  # полупрозрачный синий
        batch.flush()
        px = read_pixel(fbo, 32, 32)
        # Белый + 50% синий ≈ (127, 127, 255)
        assert 100 < px[0] < 160 and px[2] > 200, f"Блендинг неверен: {px}"
        batch.destroy()
        atlas.destroy()

    def test_additive_blending(self, ctx, fbo):
        atlas = TextureAtlas(ctx)
        batch = SpriteBatch(ctx, atlas, 64, 64)
        batch.draw_rect(0, 0, 64, 64, (100, 0, 0, 255))
        batch.draw_rect(0, 0, 64, 64, (100, 0, 0, 255), blend=BLEND_ADDITIVE)
        batch.flush()
        px = read_pixel(fbo, 32, 32)
        assert px[0] > 180, f"Аддитивный блендинг не сработал: {px}"
        batch.destroy()
        atlas.destroy()

    def test_rotation_and_growth(self, ctx, fbo):
        """5000 квадов (> стартовой ёмкости) + поворот — не падает."""
        atlas = TextureAtlas(ctx)
        batch = SpriteBatch(ctx, atlas, 64, 64)
        for i in range(5000):
            batch.draw(atlas.white, 32, 32, 4, 4, rotation=i * 7.0)
        batch.flush()
        assert batch._quad_count == 0  # сброшен после flush
        batch.destroy()
        atlas.destroy()

    def test_run_batching(self, ctx, fbo):
        """Подряд идущие квады одной страницы и блендинга образуют один run."""
        atlas = TextureAtlas(ctx)
        batch = SpriteBatch(ctx, atlas, 64, 64)
        for _ in range(100):
            batch.draw_rect(0, 0, 4, 4, (255, 255, 255, 255))
        assert len(batch._runs) == 1
        batch.flush()
        batch.destroy()
        atlas.destroy()
