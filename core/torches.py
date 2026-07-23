# core/torches.py
"""Факелы вдоль дороги: столб + анимированное пламя + аддитивное свечение.

Расставляются детерминированно (сид = номер уровня) на травяных клетках,
прилегающих к дороге. Чисто визуальный слой.
"""
import os
import math
import random
import pygame


def _make_post() -> pygame.Surface:
    """Деревянный столб факела (процедурный, 24x64)."""
    surf = pygame.Surface((24, 64), pygame.SRCALPHA, 32)
    d = pygame.draw
    # столб
    d.rect(surf, (52, 38, 26), (9, 12, 6, 50))
    d.rect(surf, (70, 52, 34), (10, 12, 2, 50))
    # чаша
    d.ellipse(surf, (60, 56, 52), (4, 6, 16, 10))
    d.ellipse(surf, (40, 36, 34), (6, 8, 12, 6))
    return surf


class TorchLayer:
    SPACING = 5          # каждая ~N-я подходящая клетка
    FIRE_ANIM_SPEED = 10  # кадров пламени в секунду

    def __init__(self, level_number: int, map_data, tile_size: int):
        self.tile_size = tile_size
        self.items = []       # (px, py) позиции факелов (мир, основание столба)
        self._time = 0.0
        self._fire_frames = self._load_fire_frames()
        self._post = _make_post()
        self._place(level_number, map_data)

    def _load_fire_frames(self):
        frames = []
        folder = "assets/sprites/fire_sheet"
        if not os.path.isdir(folder):
            return frames
        for f in sorted(os.listdir(folder)):
            if f.endswith('.png'):
                try:
                    frames.append(pygame.image.load(os.path.join(folder, f)).convert_alpha())
                except Exception:
                    pass
        return frames

    def _place(self, level_number: int, map_data):
        if not map_data:
            return
        rng = random.Random(2000 + level_number)
        h, w = len(map_data), len(map_data[0])
        ts = self.tile_size
        counter = 0
        for y in range(h):
            for x in range(w):
                if map_data[y][x] != 'grass':
                    continue
                # клетка рядом с дорогой?
                near_road = any(
                    0 <= y+dy < h and 0 <= x+dx < w and (
                        map_data[y+dy][x+dx].startswith('road_'))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                )
                if not near_road:
                    continue
                counter += 1
                if counter % self.SPACING != 0:
                    continue
                px = x * ts + ts // 2 + rng.randint(-6, 6)
                py = y * ts + ts // 2 + rng.randint(-6, 6)
                self.items.append((px, py))

    def update(self, dt: float):
        self._time += dt

    def standing_items(self):
        """Для y-сортировки с сущностями: [(sort_y, px, py)]."""
        return [(py + 20, px, py) for px, py in self.items]

    def draw_one(self, renderer, px, py, ox, oy):
        from core.opengl.batch import BLEND_ADDITIVE
        from core.iso import world_to_screen
        batch = renderer.batch
        ts = self.tile_size
        sx, sy = world_to_screen(px, py)
        x, y = sx + ox, sy + oy

        # Столб
        if not renderer.has_texture('__torch_post__'):
            renderer.load_texture('__torch_post__', self._post)
        post = renderer.get_region('__torch_post__')
        post_h = ts * 0.9
        post_w = post_h * 24 / 64
        batch.draw(post, x, y - post_h * 0.25, post_w, post_h)

        # Пламя (общая анимация, чуть рассинхронена по позиции)
        if self._fire_frames:
            idx = int(self._time * self.FIRE_ANIM_SPEED + (px * 7 + py) // 13) % len(self._fire_frames)
            name = f'__fire_{idx}'
            if not renderer.has_texture(name):
                renderer.load_texture(name, self._fire_frames[idx])
            fire = renderer.get_region(name)
            fh = ts * 0.55
            fw = fh * fire.w / fire.h
            fy = y - post_h * 0.68
            batch.draw(fire, x, fy, fw, fh)

            # Тёплое свечение (дышит)
            soft = renderer.get_region('__soft__')
            if soft:
                pulse = 1.0 + 0.08 * math.sin(self._time * 5 + px)
                glow = ts * 1.9 * pulse
                batch.draw(soft, x, fy, glow, glow,
                           color=(255, 150, 60, 70), blend=BLEND_ADDITIVE)
                batch.draw(soft, x, fy, glow * 0.45, glow * 0.45,
                           color=(255, 220, 140, 60), blend=BLEND_ADDITIVE)
