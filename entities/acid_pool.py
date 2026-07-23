# entities/acid_pool.py
import pygame
import random
import math


class AcidPool:
    """Лужа кислоты на полу — остаётся после попадания кислотного снаряда.

    Наносит эффект 'кислота на полу' врагам, наступившим в радиус.
    Форма — клякса (не круг/квадрат): 3 разных процедурных спрайта,
    выбираются случайно. Рисуется на земле (в слое декалей).
    """

    # Кэш 3 обликов кляксы на весь класс (в атлас попадают один раз)
    _sprite_cache = None

    def __init__(self, x: float, y: float, ground_damage: int,
                 interval: float, duration: float, radius: float = 34):
        self.x = x
        self.y = y
        self.ground_damage = ground_damage
        self.interval = interval
        self.duration = duration
        self.max_duration = duration
        self.radius = radius

        self.alive = True
        self.variant = random.randint(0, 2)
        self.rotation = random.uniform(0, 360)
        self._ensure_sprites()

        # Троттлинг тика урона по наступившим
        self._tick_timer = 0.0

    @classmethod
    def _ensure_sprites(cls):
        if cls._sprite_cache is not None:
            return
        cls._sprite_cache = [cls._make_blob(seed) for seed in range(3)]

    @staticmethod
    def _make_blob(seed: int) -> pygame.Surface:
        """Процедурная клякса: рваный контур из лепестков + пузыри."""
        rnd = random.Random(seed * 977 + 13)
        size = 96
        c = size // 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)

        # Кляксовый контур: низкочастотные «доли» + рваный шум по радиусу.
        # Несколько синусов разной частоты дают асимметричную органику,
        # а не симметричную звезду.
        n = 48
        base_r = size * 0.32
        f1 = rnd.choice([2, 3])
        f2 = rnd.choice([3, 4, 5])
        a1 = rnd.uniform(0.10, 0.18)
        a2 = rnd.uniform(0.05, 0.10)
        p1 = rnd.uniform(0, math.tau)
        p2 = rnd.uniform(0, math.tau)
        pts = []
        for i in range(n):
            a = math.tau * i / n
            r = base_r * (1.0
                          + a1 * math.sin(f1 * a + p1)
                          + a2 * math.sin(f2 * a + p2)
                          + rnd.uniform(-0.05, 0.05))
            pts.append((c + math.cos(a) * r, c + math.sin(a) * r))

        # Тело кляксы (тёмно-зелёное) + светлая сердцевина
        pygame.draw.polygon(surf, (46, 120, 40, 190), pts)
        inner = [((px - c) * 0.7 + c, (py - c) * 0.7 + c) for px, py in pts]
        pygame.draw.polygon(surf, (80, 190, 60, 200), inner)

        # Пузыри
        for _ in range(rnd.randint(5, 9)):
            a = rnd.uniform(0, math.tau)
            dist = rnd.uniform(0, base_r * 0.8)
            bx = c + math.cos(a) * dist
            by = c + math.sin(a) * dist
            br = rnd.randint(3, 7)
            pygame.draw.circle(surf, (150, 240, 110, 180), (int(bx), int(by)), br)
            pygame.draw.circle(surf, (60, 160, 45, 160), (int(bx), int(by)), br, 1)

        return surf

    def get_texture_name(self) -> str:
        return f"acid_pool_{self.variant}"

    def update(self, dt: float):
        self.duration -= dt
        if self.duration <= 0:
            self.alive = False

    def affect(self, enemies, dt: float):
        """Накладывает эффект кислоты на полу всем врагам в радиусе лужи."""
        self._tick_timer += dt
        if self._tick_timer < self.interval:
            return
        self._tick_timer = 0.0
        for enemy in enemies:
            if not enemy.alive or getattr(enemy, 'is_flying', False):
                continue
            dist = math.hypot(enemy.x - self.x, enemy.y - self.y)
            if dist <= self.radius:
                if hasattr(enemy, 'apply_acid_ground_effect'):
                    # Освежаем эффект на короткий срок, пока стоит в луже
                    enemy.apply_acid_ground_effect(
                        self.ground_damage, self.interval, self.interval * 2)

    def draw_batch(self, renderer, offset_x: int = 0, offset_y: int = 0):
        if not self.alive:
            return
        name = self.get_texture_name()
        if not renderer.has_texture(name):
            renderer.load_texture(name, self._sprite_cache[self.variant])
        region = renderer.get_region(name)

        # Затухание к концу жизни
        progress = self.duration / self.max_duration if self.max_duration else 1
        alpha = int(220 * min(1.0, progress * 1.8))
        from core.iso import world_to_screen
        sx, sy = world_to_screen(self.x, self.y)
        draw = self.radius * 2.2
        renderer.batch.draw(region, sx + offset_x, sy + offset_y,
                            draw, draw, rotation=self.rotation,
                            color=(255, 255, 255, alpha))
