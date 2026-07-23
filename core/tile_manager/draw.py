# core/tile_manager/draw.py
import math
import os
import pygame
from typing import Dict, List, Tuple

from core.opengl.batch import BLEND_ADDITIVE
from core.iso import world_to_screen

# Тайлы с отдельной изо-декорацией поверх базового ромба
_DECO_TILES = {'castle': 'crystal', 'portal': 'portal'}


class TileDraw:
    """Отрисовка карты через GPU-батч (изометрический режим)"""

    def __init__(self):
        self.tile_size = 65
        self._last_tile_size = 0
        # iso-тайл: ромб шириной ts, высотой ts//2
        self._iso_w = 0
        self._iso_h = 0

    def _iso_dims(self):
        return self.tile_size, self.tile_size // 2

    def draw_opengl(self, renderer, map_data: List[List[str]],
                    tiles: Dict[str, pygame.Surface], camera_offset: Tuple[int, int],
                    screen_width: int, available_height: int, background: pygame.Surface = None,
                    biome: str = 'forest'):
        if renderer is None:
            return

        offset_x, offset_y = camera_offset
        batch = renderer.batch
        ts = self.tile_size
        iso_w = ts
        iso_h = ts * 0.5

        # Инвалидация кэша при смене tile_size
        if self._last_tile_size != ts:
            renderer.clear_textures()
            self._last_tile_size = ts

        if background:
            if not renderer.has_texture("background"):
                renderer.load_texture("background", background)
            batch.draw(renderer.get_region("background"), 0, 0,
                       screen_width, available_height, centered=False)

        # Прогрев атласа: iso-тайлы
        iso_dir = f"assets/images/tiles_iso/{biome}"
        deco_dir = f"assets/images/decorations_iso/{biome}"
        tile_map = {
            'grass': 'tile_grass', 'castle': 'tile_castle', 'portal': 'tile_portal',
            'road_cross': 'tile_road_cross', 'road_h': 'tile_road_straight_h',
            'road_v': 'tile_road_straight_v', 'road_bl': 'tile_road_turn_bottom_left',
            'road_br': 'tile_road_turn_bottom_right', 'road_tl': 'tile_road_turn_top_left',
            'road_tr': 'tile_road_turn_top_right',
        }
        for name, filename in tile_map.items():
            key = f"iso_{name}"
            if not renderer.has_texture(key):
                path = os.path.join(iso_dir, f"{filename}.png")
                if os.path.exists(path):
                    surf = pygame.image.load(path).convert_alpha()
                    surf = pygame.transform.scale(surf, (iso_w, iso_h))
                    renderer.load_texture(key, surf)

        for deco_name in ('crystal', 'portal'):
            key = f"iso_deco_{deco_name}"
            if not renderer.has_texture(key):
                path = os.path.join(deco_dir, f"{deco_name}.png")
                if os.path.exists(path):
                    surf = pygame.image.load(path).convert_alpha()
                    deco_h = int(iso_h * 2.5)
                    surf = pygame.transform.scale(surf, (iso_w, deco_h))
                    renderer.load_texture(key, surf)

        grass_region = renderer.get_region("iso_grass")

        # Рисуем в порядке глубины (y-sort): строки сверху вниз
        for y in range(len(map_data)):
            for x in range(len(map_data[0])):
                tile_name = map_data[y][x]
                # Мировые пиксели — центр клетки
                wx = (x + 0.5) * ts
                wy = (y + 0.5) * ts
                sx, sy = world_to_screen(wx, wy)
                # Позиция верхнего-левого угла ромба на экране (float — без накопленного сдвига)
                px = sx + offset_x - iso_w / 2
                py = sy + offset_y - iso_h / 2

                if grass_region and tile_name != 'grass':
                    batch.draw(grass_region, px - 0.5, py - 0.5, iso_w + 1, iso_h + 1, centered=False)

                region = renderer.get_region(f"iso_{tile_name}")
                if region:
                    batch.draw(region, px - 0.5, py - 0.5, iso_w + 1, iso_h + 1, centered=False)

                deco_key = _DECO_TILES.get(tile_name)
                if deco_key:
                    deco = renderer.get_region(f"iso_deco_{deco_key}")
                    if deco:
                        deco_h = int(iso_h * 2.5)
                        batch.draw(deco, px, py - deco_h + iso_h, iso_w, deco_h, centered=False)

        self._draw_glows(renderer, map_data, offset_x, offset_y)

    def _draw_glows(self, renderer, map_data, offset_x, offset_y):
        soft = renderer.get_region('__soft__')
        if not soft:
            return
        batch = renderer.batch
        ts = self.tile_size
        iso_w, iso_h = self._iso_dims()
        t = pygame.time.get_ticks() / 1000.0
        pulse = 0.85 + 0.15 * math.sin(t * 2.2)

        glow_map = {
            'portal': [(190, 40, 120), (255, 90, 110)],
            'castle': [(120, 200, 245), (210, 245, 255)],
        }
        for y in range(len(map_data)):
            for x in range(len(map_data[0])):
                cols = glow_map.get(map_data[y][x])
                if not cols:
                    continue
                wx = (x + 0.5) * ts
                wy = (y + 0.5) * ts
                sx, sy = world_to_screen(wx, wy)
                cx = int(sx + offset_x)
                cy = int(sy + offset_y)
                outer, inner = cols
                batch.draw(soft, cx, cy, iso_w * 1.7, iso_h * 1.7,
                           color=(*outer, int(70 * pulse)), blend=BLEND_ADDITIVE)
                batch.draw(soft, cx, cy, iso_w * 0.95, iso_h * 0.95,
                           color=(*inner, int(120 * pulse)), blend=BLEND_ADDITIVE)

    def set_tile_size(self, tile_size: int):
        if self.tile_size != tile_size:
            self.tile_size = tile_size
