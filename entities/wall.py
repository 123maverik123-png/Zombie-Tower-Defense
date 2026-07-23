# entities/wall.py
import pygame
import random
from entities.base import Entity
from services.resource_loader import ResourceLoader

WALL_VARIANTS = ('h', 'v', 'tl', 'tr', 'bl', 'br')

_wall_image_cache = {}
_corner_sources = None


def _build_corner_sources():
    """Собирает tl/tr/bl/br из двух половинок wall_v — своих файлов у углов нет.

    wall_v проходит через центр тайла: правая половина картинки — это
    "плечо" к соседу сверху (up), левая — "плечо" к соседу снизу (down).
    Зеркалим их по горизонтали (та же логика, что даёт 'h' из 'v') — получаем
    плечи "влево"/"вправо". Угол — это пара плеч, сходящихся в центре:
    tl=up+left, tr=up+right, bl=down+left, br=down+right (совпадает с
    _wall_variant_at в towers.py).
    """
    base = ResourceLoader().load_image("fortify/wall_v.png")
    w, h = base.get_size()
    half = w // 2

    v_up = base.subsurface((half, 0, w - half, h)).copy()
    v_down = base.subsurface((0, 0, half, h)).copy()

    def blank():
        return pygame.Surface((w, h), pygame.SRCALPHA)

    up_half = blank()
    up_half.blit(v_up, (half, 0))

    down_half = blank()
    down_half.blit(v_down, (0, 0))

    left_half = blank()
    left_half.blit(pygame.transform.flip(v_up, True, False), (0, 0))

    right_half = blank()
    right_half.blit(pygame.transform.flip(v_down, True, False), (half, 0))

    def combine(a, b):
        img = blank()
        img.blit(a, (0, 0))
        img.blit(b, (0, 0))
        return img

    return {
        'tl': combine(up_half, left_half),
        'tr': combine(up_half, right_half),
        'bl': combine(down_half, left_half),
        'br': combine(down_half, right_half),
    }


def load_wall_image(variant: str, size: int) -> pygame.Surface:
    """Спрайт стены по варианту и размеру (с кэшем).

    'h' не имеет отдельного файла — это тот же изо-арт, что 'v', отражённый
    по горизонтали: в проекции core/iso.py стена вдоль X и стена вдоль Y —
    ровно зеркальные отражения друг друга (dx меняет знак, dy тот же).
    Угловые варианты собираются из половинок 'v', см. _build_corner_sources.
    """
    key = (variant, size)
    cached = _wall_image_cache.get(key)
    if cached is not None:
        return cached.copy()

    if variant in ('tl', 'tr', 'bl', 'br'):
        global _corner_sources
        if _corner_sources is None:
            _corner_sources = _build_corner_sources()
        img = pygame.transform.smoothscale(_corner_sources[variant], (size, size))
    else:
        loader = ResourceLoader()
        source_variant = 'v' if variant == 'h' else variant
        img = loader.load_image(f"fortify/wall_{source_variant}.png", scale=(size, size))
        if variant == 'h':
            img = pygame.transform.flip(img, True, False)

    _wall_image_cache[key] = img
    return img.copy()


class FortifyUpgrades:
    """Уровни прочности стены/ворот (совместимо с TowerUI: level/cost/upgrade)."""

    def __init__(self, entity, base_cost, upgrade_cost, hp_add):
        self.entity = entity
        self.level = 1
        self.max_level = 4
        self.cost = base_cost
        self.upgrade_cost = upgrade_cost
        self._hp_add = hp_add
        self.special_effect = None

    def upgrade(self) -> bool:
        if self.level >= self.max_level:
            return False
        e = self.entity
        e.max_health += self._hp_add
        e.health = e.max_health  # апгрейд заодно чинит
        self.level += 1
        self.upgrade_cost = int(self.upgrade_cost * 1.4)
        return True

    def repair_cost(self) -> int:
        """Стоимость ремонта = базовая цена, растёт с уровнем (x1.5/ур)."""
        return int(self.cost * (1.5 ** (self.level - 1)))

    def repair(self) -> bool:
        """Восстанавливает HP до максимума."""
        e = self.entity
        if e.health >= e.max_health:
            return False
        e.health = e.max_health
        return True


class Wall(Entity):
    """Обычная стена — блокирует путь, может быть атакована зомби."""

    def __init__(self, x: float, y: float, hp: int = 200, variant: str = 'h', tile_size: int = 65):
        super().__init__(
            entity_id='wall',
            x=x,
            y=y,
            config={'health': hp, 'width': 40, 'height': 40}
        )
        self.max_health = hp
        self.health = hp
        self.alive = True
        self.width = 40
        self.height = 40
        # Визуальный размер = полный тайл, чтобы стены соприкасались с воротами
        self.draw_size = tile_size
        # Grid-координаты клетки (для автоориентации по соседям)
        self.wx = int(x // tile_size)
        self.wy = int(y // tile_size)
        self.rect = pygame.Rect(x - self.width//2, y - self.height//2, self.width, self.height)
        self.is_gate = False
        self.variant = variant if variant in WALL_VARIANTS else 'h'
        self.upgrades = FortifyUpgrades(self, base_cost=80, upgrade_cost=60, hp_add=150)

        self._create_image()

    def set_variant(self, variant: str):
        """Меняет форму стены и перерисовывает спрайт."""
        if variant in WALL_VARIANTS and variant != self.variant:
            self.variant = variant
            self._create_image()

    def _create_image(self):
        # Готовый спрайт по варианту; при ошибке — процедурный fallback
        try:
            self.image = load_wall_image(self.variant, self.draw_size)
            return
        except Exception:
            pass
        self._create_image_fallback()

    def _create_image_fallback(self):
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # Каменная стена
        pygame.draw.rect(self.image, (140, 130, 120), (0, 0, self.width, self.height))
        pygame.draw.rect(self.image, (100, 90, 80), (0, 0, self.width, self.height), 2)
        # Камни
        for row in range(4):
            for col in range(3):
                x = col * 14 + (7 if row % 2 else 0)
                y = row * 10 + 2
                color = (160 + random.randint(-20, 20), 150 + random.randint(-20, 20), 140 + random.randint(-20, 20))
                pygame.draw.rect(self.image, color, (x, y, 12, 8))
                pygame.draw.rect(self.image, (80, 70, 60), (x, y, 12, 8), 1)
        # Тень сверху
        pygame.draw.rect(self.image, (0, 0, 0, 30), (0, 0, self.width, 3))

    def take_damage(self, amount: int):
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.alive = False

    def update(self, dt: float):
        """Обновление стены (пока ничего не делаем)."""
        pass

    def draw(self, screen, offset_x=0, offset_y=0):
        if not self.alive:
            return
        if self.image:
            iw, ih = self.image.get_size()
            screen.blit(self.image, (self.x + offset_x - iw//2,
                                    self.y + offset_y - ih//2))

        if self.health < self.max_health:
            bar_w = self.width
            bar_h = 4
            x = self.x + offset_x - bar_w//2
            y = self.y + offset_y - self.height//2 - 8
            pygame.draw.rect(screen, (255, 0, 0), (x, y, bar_w, bar_h))
            pygame.draw.rect(screen, (0, 255, 0), (x, y, bar_w * (self.health / self.max_health), bar_h))

    def draw_batch(self, renderer, offset_x=0, offset_y=0):
        """Рисует стену через GPU-батч. Стены уникальны (random-камни) — координаты в имени."""
        if not self.alive:
            return
        batch = renderer.batch
        from core.iso import world_to_screen
        sx, sy = world_to_screen(self.x, self.y)
        cx = sx + offset_x
        cy = sy + offset_y

        name = f"wall_{self.variant}_{int(self.x)}_{int(self.y)}"
        if not renderer.has_texture(name):
            renderer.load_texture(name, self.image)
        ds = getattr(self, 'draw_size', self.width)
        batch.draw(renderer.get_region(name), cx, cy, ds, ds)

        if self.health < self.max_health:
            bar_w = self.width
            bar_h = 4
            x = cx - bar_w // 2
            y = cy - self.height // 2 - 8
            batch.draw_rect(x, y, bar_w, bar_h, (255, 0, 0, 255))
            batch.draw_rect(x, y, bar_w * (self.health / self.max_health), bar_h, (0, 255, 0, 255))