# core/tile_manager/draw.py
import pygame
from typing import Dict, List, Tuple


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

        # Все тайлы одним батчем
        for y in range(len(map_data)):
            for x in range(len(map_data[0])):
                tile_name = map_data[y][x]
                if tile_name in tiles:
                    region = renderer.get_region(f"tile_{tile_name}_{self.tile_size}")
                    if region:
                        px = x * self.tile_size + offset_x
                        py = y * self.tile_size + offset_y
                        batch.draw(region, px, py, self.tile_size, self.tile_size, centered=False)

    def set_tile_size(self, tile_size: int):
        """Устанавливает размер тайла"""
        if self.tile_size != tile_size:
            self.tile_size = tile_size
            self._scaled_tile_cache.clear()
