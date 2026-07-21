# entities/gate.py
import pygame
import random
from entities.base import Entity
from services.resource_loader import ResourceLoader
from entities.wall import FortifyUpgrades

class Gate(Entity):
    """Ворота — блокируют путь, не ближе 10 клеток к порталу."""

    def __init__(self, x: float, y: float, hp: int = 500, orientation: str = 'h', tile_size: int = 65):
        super().__init__(
            entity_id='gate',
            x=x,
            y=y,
            config={'health': hp, 'width': 50, 'height': 50}
        )
        self.max_health = hp
        self.health = hp
        self.alive = True
        self.width = 50
        self.height = 50
        # Визуальный размер = полный тайл, чтобы стены/ворота соприкасались
        self.draw_size = tile_size
        # Grid-координаты клетки (для соседства со стенами)
        self.wx = int(x // tile_size)
        self.wy = int(y // tile_size)
        self.rect = pygame.Rect(x - self.width//2, y - self.height//2, self.width, self.height)
        self.is_gate = True
        self.orientation = orientation if orientation in ('h', 'v') else 'h'
        self.upgrades = FortifyUpgrades(self, base_cost=150, upgrade_cost=120, hp_add=350)

        self._create_image()

    def _create_image(self):
        # Готовый спрайт по ориентации; при ошибке — процедурный fallback
        try:
            loader = ResourceLoader()
            self.image = loader.load_image(
                f"fortify/gate_{self.orientation}.png",
                scale=(self.draw_size, self.draw_size))
            return
        except Exception:
            pass
        self._create_image_fallback()

    def _create_image_fallback(self):
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # Деревянные ворота
        pygame.draw.rect(self.image, (120, 80, 40), (0, 0, self.width, self.height))
        pygame.draw.rect(self.image, (80, 50, 20), (0, 0, self.width, self.height), 3)
        # Доски
        for i in range(4):
            x = i * 12 + 3
            color = (160 + random.randint(-20, 20), 110 + random.randint(-20, 20), 60 + random.randint(-20, 20))
            pygame.draw.rect(self.image, color, (x, 3, 8, self.height-6))
            pygame.draw.rect(self.image, (80, 50, 20), (x, 3, 8, self.height-6), 1)
        # Ручка
        pygame.draw.circle(self.image, (200, 180, 100), (self.width-10, self.height//2), 4)
        # Петли
        pygame.draw.rect(self.image, (100, 100, 100), (2, 6, 6, 8))
        pygame.draw.rect(self.image, (100, 100, 100), (2, self.height-14, 6, 8))
        # Тень сверху
        pygame.draw.rect(self.image, (0, 0, 0, 40), (0, 0, self.width, 4))
        # Железная окантовка
        pygame.draw.rect(self.image, (100, 100, 100), (0, 0, self.width, self.height), 2)

    def take_damage(self, amount: int):
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.alive = False

    def update(self, dt: float):
        """Обновление ворот (пока ничего не делаем)."""
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
            bar_h = 5
            x = self.x + offset_x - bar_w//2
            y = self.y + offset_y - self.height//2 - 10
            pygame.draw.rect(screen, (255, 0, 0), (x, y, bar_w, bar_h))
            pygame.draw.rect(screen, (255, 215, 0), (x, y, bar_w * (self.health / self.max_health), bar_h))
            pygame.draw.rect(screen, (255, 255, 255), (x, y, bar_w, bar_h), 1)

    def draw_batch(self, renderer, offset_x=0, offset_y=0):
        """Рисует ворота через GPU-батч. Каждые ворота уникальны (random-доски) — id в имени."""
        if not self.alive:
            return
        batch = renderer.batch
        cx = self.x + offset_x
        cy = self.y + offset_y

        name = f"gate_{self.orientation}_{int(self.x)}_{int(self.y)}"
        if not renderer.has_texture(name):
            renderer.load_texture(name, self.image)
        ds = getattr(self, 'draw_size', self.width)
        batch.draw(renderer.get_region(name), cx, cy, ds, ds)

        if self.health < self.max_health:
            bar_w = self.width
            bar_h = 5
            x = cx - bar_w // 2
            y = cy - self.height // 2 - 10
            batch.draw_rect(x, y, bar_w, bar_h, (255, 0, 0, 255))
            batch.draw_rect(x, y, bar_w * (self.health / self.max_health), bar_h, (255, 215, 0, 255))