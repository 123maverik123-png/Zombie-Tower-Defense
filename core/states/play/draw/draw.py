# core/states/play/draw/draw.py
import pygame

from .terrain import TerrainDraw
from .entities import EntitiesDraw
from .effects import EffectsDraw
from .preview import PreviewDraw
from .ui import UIDraw
from .victory import VictoryDraw


class PlayDraw:
    """Главный класс отрисовки игрового состояния.

    draw_scene(renderer) — GPU-батч: карта, декали, сущности, эффекты.
    draw(screen) — pygame-оверлей: превью, HUD, консоль, победа.
    """

    def __init__(self, state):
        self.state = state
        self._debug_printed = False

        self.terrain = TerrainDraw(state)
        self.entities = EntitiesDraw(state)
        self.effects = EffectsDraw(state)
        self.preview = PreviewDraw(state)
        self.ui = UIDraw(state)
        self.victory = VictoryDraw(state)

    def draw_scene(self, renderer):
        """GPU-сцена. Порядок вызовов batch.draw = порядок слоёв."""
        from core.opengl.procedural import ensure_builtins
        ensure_builtins(renderer)

        state = self.state
        ox, oy = state.tile_manager.get_offset()
        screen_w = state.game.render_width
        screen_h = state.game.render_height

        # 1. Карта и декали на земле
        self.terrain.draw_scene(renderer, ox, oy, screen_w, screen_h)

        # 2. Сущности (башни, враги, снаряды, струи, вспышки)
        self.entities.draw_scene(renderer, ox, oy, screen_w, screen_h)

        # 3. Эффекты (попадания, молнии)
        self.effects.draw_scene(renderer, ox, oy)

        # 4. Атмосфера: амбиентное затемнение биома + виньетка
        self._draw_atmosphere(renderer, screen_w, screen_h)

    def _draw_atmosphere(self, renderer, screen_w, screen_h):
        """Тёмно-фэнтезийный тон: цветной полупрозрачный слой + виньетка"""
        from core.graphics_theme import biome_ambient
        cfg = biome_ambient(getattr(self.state, 'biome', 'forest'))

        # Амбиентный тинт всей сцены
        renderer.batch.draw_rect(0, 0, screen_w, screen_h, cfg['ambient'])

        # Виньетка по краям
        vin = renderer.get_region('__vignette__')
        if vin:
            renderer.batch.draw(vin, screen_w * 0.5, screen_h * 0.5,
                                screen_w, screen_h,
                                color=(0, 0, 0, cfg['vignette_alpha']))

    def draw(self, screen):
        """Pygame-оверлей поверх GPU-сцены."""
        state = self.state
        ox, oy = state.tile_manager.get_offset()

        # 1. Фидбек строительства (текст ошибок/успеха)
        self.effects.draw_feedback(screen, ox, oy)

        # 2. Превью строительства
        self.preview.draw(screen)

        # 3. UI (HUD, панель башен, консоль)
        self.ui.draw(screen, ox, oy)

        # 3.5 Подсказки обучения (уровень 1)
        if hasattr(state, 'tutorial'):
            state.tutorial.draw(screen)

        # 4. Экран победы
        if state.wave_manager.is_all_waves_complete() and len(state.enemies) == 0:
            self.victory.draw(screen)
