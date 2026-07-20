# core/opengl/renderer.py
"""Фасад GPU-рендера: контекст + атлас + батч + UI-оверлей."""
import pygame

from .context import GLContext
from .atlas import TextureAtlas
from .batch import SpriteBatch, BLEND_ALPHA, BLEND_ADDITIVE


class Renderer:
    """Создаётся после pygame.display.set_mode(OPENGL). Один на игру."""

    def __init__(self, width: int, height: int):
        self.gl = GLContext()
        self.ctx = self.gl.init(width, height)
        self.atlas = TextureAtlas(self.ctx)
        self.batch = SpriteBatch(self.ctx, self.atlas, width, height)

        from .ui_overlay import UIOverlay
        self.overlay = UIOverlay(self.ctx, width, height)

        self.width = width
        self.height = height

    # ===== Кадр =====

    def begin_frame(self, clear_color=(0.04, 0.04, 0.06, 1.0)) -> pygame.Surface:
        """Очищает экран и UI-поверхность. Возвращает поверхность для pygame-UI."""
        self.gl.clear(clear_color)
        return self.overlay.begin_frame()

    def end_frame(self):
        """Дорисовывает батч сцены, затем UI поверх."""
        self.batch.flush()
        self.overlay.render()

    # ===== Текстуры =====

    def load_texture(self, name: str, surface: pygame.Surface):
        """Кладёт поверхность в атлас под именем name (идемпотентно)."""
        return self.atlas.add(name, surface)

    def has_texture(self, name: str) -> bool:
        return self.atlas.has(name)

    def get_region(self, name: str):
        return self.atlas.get(name)

    def clear_textures(self):
        self.atlas.clear()

    # ===== Управление =====

    def resize(self, width: int, height: int):
        self.width = width
        self.height = height
        self.gl.resize(width, height)
        self.batch.set_screen_size(width, height)
        self.overlay.resize(width, height)

    def destroy(self):
        self.overlay.destroy()
        self.batch.destroy()
        self.atlas.destroy()
        self.gl.destroy()
