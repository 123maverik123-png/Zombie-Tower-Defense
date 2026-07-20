# ui/settings/slider.py
import pygame
from core.font_loader import load_ui_font
from core.theme import GOLD, GOLD_BRIGHT, GOLD_DIM, STONE_DARK, PARCHMENT, TEAL_GLOW
from .draw import draw_glow


class Slider:
    """Ползунок громкости"""
    
    def __init__(self, x, y, width, height, min_val=0.0, max_val=1.0, initial=0.5, label=""):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial
        self.label = label
        self.dragging = False
        self.hovered = False
        self.font = load_ui_font(24)
        self.value_font = load_ui_font(22)
        self.knob_radius = 11
        self.knob_x = self._value_to_x(initial)

    def _value_to_x(self, value):
        t = (value - self.min_val) / (self.max_val - self.min_val)
        return self.rect.x + t * self.rect.width

    def _x_to_value(self, x):
        t = max(0, min(1, (x - self.rect.x) / self.rect.width))
        return self.min_val + t * (self.max_val - self.min_val)

    def handle_event(self, pos):
        if self.rect.collidepoint(pos) or self.dragging:
            self.dragging = True
            self.value = self._x_to_value(pos[0])
            self.knob_x = self._value_to_x(self.value)
            return True
        return False

    def handle_hover(self, pos):
        hit = self.rect.inflate(0, 16)
        self.hovered = hit.collidepoint(pos)

    def release(self):
        self.dragging = False

    def draw(self, screen):
        # Трек
        pygame.draw.rect(screen, STONE_DARK, self.rect, border_radius=4)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y,
                                 max(0, self.knob_x - self.rect.x), self.rect.height)
        pygame.draw.rect(screen, GOLD_DIM, fill_rect, border_radius=4)
        border_color = GOLD_BRIGHT if (self.hovered or self.dragging) else GOLD
        pygame.draw.rect(screen, border_color, self.rect, 2, border_radius=4)

        # Ручка
        knob_center = (int(self.knob_x), int(self.rect.y + self.rect.height / 2))
        if self.dragging:
            draw_glow(screen, pygame.Rect(knob_center[0] - 12, knob_center[1] - 12, 24, 24),
                      TEAL_GLOW, pad=6, alpha=90, radius=16)
        pygame.draw.circle(screen, GOLD_BRIGHT, knob_center, self.knob_radius)
        pygame.draw.circle(screen, STONE_DARK, knob_center, self.knob_radius, 2)

        # Подписи
        label_text = self.font.render(self.label, True, PARCHMENT)
        value_text = self.value_font.render(f"{int(self.value * 100)}%", True, GOLD_BRIGHT)
        screen.blit(label_text, (self.rect.x, self.rect.y - 30))
        screen.blit(value_text, (self.rect.right - value_text.get_width(), self.rect.y - 29))