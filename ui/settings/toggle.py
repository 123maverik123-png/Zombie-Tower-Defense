# ui/settings/toggle.py
import pygame
from core.font_loader import load_ui_font
from core.theme import GOLD, GOLD_DIM, STONE_DARK, STONE_MID, PARCHMENT, PARCHMENT_DIM


class ToggleButton:
    """Кнопка-переключатель вкл/выкл"""
    
    def __init__(self, x, y, label="", initial=True):
        self.x = x
        self.y = y
        self.width = 58
        self.height = 30
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.label = label
        self.is_on = initial
        self.font = load_ui_font(24)
        self.click_cooldown = 0.0
        self.hovered = False

    def handle_click(self, pos):
        if self.click_cooldown <= 0 and self.rect.collidepoint(pos):
            self.is_on = not self.is_on
            self.click_cooldown = 0.3
            return True
        return False

    def handle_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def update(self, dt):
        if self.click_cooldown > 0:
            self.click_cooldown -= dt

    def draw(self, screen):
        # Подпись
        label_text = self.font.render(self.label, True, PARCHMENT)
        screen.blit(label_text, (self.x - label_text.get_width() - 16, self.y + 3))

        # Трек
        track_color = GOLD_DIM if self.is_on else STONE_MID
        pygame.draw.rect(screen, track_color, self.rect, border_radius=15)
        border_color = GOLD if self.is_on else GOLD
        pygame.draw.rect(screen, border_color, self.rect, 2, border_radius=15)

        # Ручка
        knob_x = self.rect.x + self.width - 25 if self.is_on else self.rect.x + 5
        knob_center = (int(knob_x + 10), int(self.rect.y + self.rect.height / 2))
        pygame.draw.circle(screen, GOLD if self.is_on else PARCHMENT_DIM, knob_center, 10)
        pygame.draw.circle(screen, STONE_DARK, knob_center, 10, 2)