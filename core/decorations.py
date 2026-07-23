# core/decorations.py
"""Слой декораций на карте.

Два источника:
1. Ручные: в LEVELS[n]['decorations'] — список (имя, клетка_x, клетка_y, масштаб).
2. Автоматические: детерминированный разброс мелочи по травяным клеткам
   (сид = номер уровня, поэтому у всех игроков одинаково).

Декорации чисто визуальные: рисуются поверх тайлов, под сущностями,
и не влияют на постройку.
"""
import os
import random
import pygame

from core.graphics_theme import THEME


class DecorationLayer:
    # Что сыпать автоматически: (имя, вес, мин_масштаб, макс_масштаб)
    AUTO_SETS = {
        'forest': [('tree', 4, 0.9, 1.3), ('bush', 3, 0.5, 0.8),
                   ('bush_small', 3, 0.35, 0.55), ('rock', 2, 0.4, 0.6),
                   ('plant', 2, 0.35, 0.6)],
        'desert': [('cactus', 4, 0.6, 1.0), ('cactus_small', 3, 0.4, 0.6),
                   ('rock', 3, 0.4, 0.7), ('rock_small', 2, 0.3, 0.5),
                   ('crater', 1, 0.7, 1.0)],
        'city':   [('building_a', 2, 0.9, 1.1), ('building_b', 2, 0.9, 1.1),
                   ('building_c', 2, 0.9, 1.1), ('crate', 3, 0.4, 0.6)],
    }
    AUTO_DENSITY = 0.10   # доля травяных клеток с декорацией

    def __init__(self, biome: str, level_number: int, map_data, tile_size: int,
                 manual: list = None):
        self.biome = biome
        self.tile_size = tile_size
        self.sprites = {}
        self.items = []   # (sprite_name, px, py, size_px) в мировых координатах

        self._load_sprites()
        if manual:
            for entry in manual:
                name, cx, cy = entry[0], entry[1], entry[2]
                scale = entry[3] if len(entry) > 3 else 1.0
                self._add(name, cx, cy, scale)
        self._auto_scatter(level_number, map_data, manual or [])

    def _load_sprites(self):
        folder = f"assets/images/decorations/{self.biome}"
        if not os.path.isdir(folder):
            return
        for f in os.listdir(folder):
            if f.endswith('.png'):
                try:
                    self.sprites[f[:-4]] = pygame.image.load(
                        os.path.join(folder, f)).convert_alpha()
                except Exception:
                    pass

    def _add(self, name: str, cell_x: int, cell_y: int, scale: float):
        if name not in self.sprites:
            return
        ts = self.tile_size
        px = cell_x * ts + ts // 2
        py = cell_y * ts + ts // 2
        self.items.append((name, px, py, int(ts * scale)))

    def _auto_scatter(self, level_number: int, map_data, manual):
        if not map_data or not self.sprites:
            return
        rng = random.Random(1000 + level_number)
        manual_cells = {(e[1], e[2]) for e in manual}
        choices = self.AUTO_SETS.get(self.biome, [])
        if not choices:
            return
        names = [c[0] for c in choices]
        weights = [c[1] for c in choices]

        for y in range(len(map_data)):
            for x in range(len(map_data[0])):
                if map_data[y][x] != 'grass' or (x, y) in manual_cells:
                    continue
                if rng.random() > self.AUTO_DENSITY:
                    continue
                name = rng.choices(names, weights)[0]
                cfg = next(c for c in choices if c[0] == name)
                scale = rng.uniform(cfg[2], cfg[3])
                # лёгкое смещение внутри клетки, чтобы не было сетки
                ts = self.tile_size
                px = x * ts + ts // 2 + rng.randint(-ts // 5, ts // 5)
                py = y * ts + ts // 2 + rng.randint(-ts // 5, ts // 5)
                if name in self.sprites:
                    self.items.append((name, px, py, int(ts * scale)))

    # Плоские декорации (лежат на земле — вне y-сортировки)
    FLAT = {'crater', 'plant', 'rock_small', 'bush_small', 'crate'}

    def draw_scene(self, renderer, ox, oy):
        """Рисует ПЛОСКИЕ декорации (в слое земли)"""
        for name, px, py, size in self.items:
            if name in self.FLAT:
                self._draw_one(renderer, name, px, py, size, ox, oy)

    def standing_items(self):
        """Высокие декорации для y-сортировки с сущностями.

        Возвращает [(sort_y, name, px, py, size)].
        """
        return [(py + size * 0.5, name, px, py, size)
                for name, px, py, size in self.items if name not in self.FLAT]

    def draw_one_standing(self, renderer, name, px, py, size, ox, oy):
        self._draw_one(renderer, name, px, py, size, ox, oy)

    def _draw_one(self, renderer, name, px, py, size, ox, oy):
        from core.iso import world_to_screen
        shadow = renderer.get_region('__shadow__')
        atlas_name = f"decor_{self.biome}_{name}"
        if not renderer.has_texture(atlas_name):
            renderer.load_texture(atlas_name, self.sprites[name])
        region = renderer.get_region(atlas_name)
        sx, sy = world_to_screen(px, py)
        x, y = sx + ox, sy + oy
        if shadow:
            renderer.batch.draw(shadow, x + 2, y + size * 0.38,
                                size * 0.8, size * 0.28,
                                color=(255, 255, 255, 70))
        renderer.batch.draw(region, x, y, size, size)
