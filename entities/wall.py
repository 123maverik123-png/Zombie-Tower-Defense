# entities/wall.py
import pygame
import random
from entities.base import Entity
from services.resource_loader import ResourceLoader

WALL_VARIANTS = ('h', 'v', 'tl', 'tr', 'bl', 'br')


class Wall(Entity):
    """Обычная стена — блокирует путь, может быть атакована зомби."""

    def __init__(self, x: float, y: float, hp: int = 200, variant: str = 'h'):
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
        self.rect = pygame.Rect(x - self.width//2, y - self.height//2, self.width, self.height)
        self.is_gate = False
        self.variant = variant if variant in WALL_VARIANTS else 'h'

        self._create_image()

    def _create_image(self):
        # Готовый спрайт по варианту; при ошибке — процедурный fallback
        try:
            loader = ResourceLoader()
            self.image = loader.load_image(
                f"fortify/wall_{self.variant}.png",
                scale=(self.width, self.height))
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
            screen.blit(self.image, (self.x + offset_x - self.width//2,
                                    self.y + offset_y - self.height//2))

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
        cx = self.x + offset_x
        cy = self.y + offset_y

        name = f"wall_{self.variant}_{int(self.x)}_{int(self.y)}"
        if not renderer.has_texture(name):
            renderer.load_texture(name, self.image)
        batch.draw(renderer.get_region(name), cx, cy, self.width, self.height)

        if self.health < self.max_health:
            bar_w = self.width
            bar_h = 4
            x = cx - bar_w // 2
            y = cy - self.height // 2 - 8
            batch.draw_rect(x, y, bar_w, bar_h, (255, 0, 0, 255))
            batch.draw_rect(x, y, bar_w * (self.health / self.max_health), bar_h, (0, 255, 0, 255))