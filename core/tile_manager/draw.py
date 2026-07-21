# core/tile_manager/draw.py
import math
import pygame
from typing import Dict, List, Tuple

from core.opengl.batch import BLEND_ADDITIVE


class TileDraw:
    """Отрисовка карты через GPU-батч"""

    def __init__(self):
        self.tile_size = 65
        self._scaled_tile_cache: Dict[str, pygame.Surface] = {}
        self._last_tile_size = 0

    def draw_opengl(self, renderer, map_data: List[List[str]],
                    tiles: Dict[str, pygame.Surface], camera_offset: Tuple[int, int],
                    screen_width: int, available_height: int, background: pygame.Surface = None):
        """Отрисовывает карту через GPU-батч"""
        if renderer is None:
            return

        offset_x, offset_y = camera_offset
        batch = renderer.batch

        # Фон
        if background:
            if not renderer.has_texture("background"):
                renderer.load_texture("background", background)
            bg = renderer.get_region("background")
            batch.draw(bg, 0, 0, screen_width, available_height, centered=False)

        # Обновляем кэш
        if self._last_tile_size != self.tile_size:
            self._scaled_tile_cache.clear()
            self._last_tile_size = self.tile_size

        # Прогрев атласа (масштабированные тайлы)
        for tile_name, tile_surface in tiles.items():
            atlas_name = f"tile_{tile_name}_{self.tile_size}"
            if not renderer.has_texture(atlas_name):
                if tile_surface.get_width() != self.tile_size:
                    scaled = pygame.transform.scale(tile_surface, (self.tile_size, self.tile_size))
                else:
                    scaled = tile_surface
                renderer.load_texture(atlas_name, scaled)

        # Все тайлы одним батчем.
        # Сначала базовый слой травы под КАЖДОЙ клеткой — дорожные/портальные
        # тайлы имеют полупрозрачные края (сглаженные углы, тени), и без
        # подложки сквозь них виден фон. Трава закрывает эти просветы.
        grass_region = None
        if 'grass' in tiles:
            grass_region = renderer.get_region(f"tile_grass_{self.tile_size}")

        for y in range(len(map_data)):
            for x in range(len(map_data[0])):
                tile_name = map_data[y][x]
                px = x * self.tile_size + offset_x
                py = y * self.tile_size + offset_y
                # подложка травой под всё, кроме самой травы
                if grass_region is not None and tile_name != 'grass':
                    batch.draw(grass_region, px, py, self.tile_size, self.tile_size, centered=False)
                if tile_name in tiles:
                    region = renderer.get_region(f"tile_{tile_name}_{self.tile_size}")
                    if region:
                        batch.draw(region, px, py, self.tile_size, self.tile_size, centered=False)

        self._draw_glows(renderer, map_data, offset_x, offset_y)

    def _draw_glows(self, renderer, map_data, offset_x, offset_y):
        """Мягкое пульсирующее свечение поверх портала и кристалла.

        Портал — красно-фиолетовое, кристалл (castle) — бело-лазурное.
        Аддитивные мягкие круги, амплитуда лёгкая (не навязчиво).
        """
        soft = renderer.get_region('__soft__')
        if not soft:
            return
        batch = renderer.batch
        ts = self.tile_size
        t = pygame.time.get_ticks() / 1000.0
        pulse = 0.85 + 0.15 * math.sin(t * 2.2)  # 0.7..1.0

        glow_map = {
            'portal': [(190, 40, 120), (255, 90, 110)],   # фиолет + красно-розовый
            'castle': [(120, 200, 245), (210, 245, 255)],  # лазурь + бело-голубой
        }
        for y in range(len(map_data)):
            row = map_data[y]
            for x in range(len(row)):
                cols = glow_map.get(row[x])
                if not cols:
                    continue
                cx = x * ts + offset_x + ts // 2
                cy = y * ts + offset_y + ts // 2
                outer, inner = cols
                a_out = int(70 * pulse)
                a_in = int(120 * pulse)
                batch.draw(soft, cx, cy, ts * 1.7, ts * 1.7,
                           color=(*outer, a_out), blend=BLEND_ADDITIVE)
                batch.draw(soft, cx, cy, ts * 0.95, ts * 0.95,
                           color=(*inner, a_in), blend=BLEND_ADDITIVE)

    def set_tile_size(self, tile_size: int):
        """Устанавливает размер тайла"""
        if self.tile_size != tile_size:
            self.tile_size = tile_size
            self._scaled_tile_cache.clear()
