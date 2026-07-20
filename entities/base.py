# entities/base.py
import pygame
from abc import ABC, abstractmethod
from typing import Optional, Tuple, List, Any
import math

class Entity(ABC, pygame.sprite.Sprite):
    """Базовый класс для всех игровых сущностей"""

    def __init__(self, entity_id: str, x: float, y: float, config: dict):
        super().__init__()
        self.id = entity_id
        self.x = x
        self.y = y
        self.config = config

        # Базовые характеристики
        self.health = config.get('health', 100)
        self.max_health = self.health
        self.alive = True

        # Позиция и размер для коллизий
        self.width = config.get('width', 32)
        self.height = config.get('height', 32)
        self.rect = pygame.Rect(x, y, self.width, self.height)

        # Визуальные параметры
        self.image = None
        self.angle = 0
        self.scale = 1.0

    @abstractmethod
    def update(self, dt: float, *args, **kwargs):
        """Обновление состояния сущности"""
        pass

    def take_damage(self, amount: int, damage_type: str = 'physical') -> int:
        """Нанести урон, возвращает реально нанесённый урон"""
        actual_damage = self._calculate_damage(amount, damage_type)
        self.health -= actual_damage

        if self.health <= 0:
            self.health = 0
            self.alive = False
            self.on_death()

        return actual_damage

    def _calculate_damage(self, amount: int, damage_type: str) -> int:
        """Расчёт урона с учётом сопротивлений"""
        return amount

    def on_death(self):
        """Событие при смерти"""
        pass

    def get_center(self) -> Tuple[float, float]:
        """Возвращает центр сущности"""
        return (self.x + self.width / 2, self.y + self.height / 2)

    def distance_to(self, other: 'Entity') -> float:
        """Расстояние до другой сущности"""
        x1, y1 = self.get_center()
        x2, y2 = other.get_center()
        return math.hypot(x2 - x1, y2 - y1)

    def draw(self, screen: pygame.Surface, offset_x: int = 0, offset_y: int = 0):
        """Отрисовка сущности"""
        if self.image:
            screen.blit(self.image, (self.x + offset_x, self.y + offset_y))
        else:
            # Заглушка
            pygame.draw.rect(screen, (200, 50, 50),
                           (self.x + offset_x, self.y + offset_y, self.width, self.height))
            self.draw_health_bar(screen, offset_x, offset_y)

# entities/base.py — исправленный метод draw_health_bar

def draw_health_bar(self, screen: pygame.Surface, offset_x: int = 0, offset_y: int = 0):
    """Рисует полоску здоровья над сущностью (центрированную)"""
    if self.health >= self.max_health:
        return
    
    bar_width = self.width
    bar_height = 4
    health_percent = self.health / self.max_health
    
    # Центрируем над сущностью
    x = self.x + offset_x - bar_width // 2
    y = self.y + offset_y - self.height // 2 - 8
    
    pygame.draw.rect(screen, (255, 0, 0), (x, y, bar_width, bar_height))
    pygame.draw.rect(screen, (0, 255, 0), (x, y, bar_width * health_percent, bar_height))