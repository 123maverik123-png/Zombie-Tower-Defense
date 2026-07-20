# ui/settings/resolution.py
import pygame
from core.settings import GameSettings
from core.audio import AudioManager
from core.font_loader import load_ui_font
from core.theme import GOLD, GOLD_BRIGHT, STONE_DARK, STONE_MID, STONE_LIGHT, PARCHMENT


class ResolutionSelector:
    """Выбор разрешения экрана"""
    
    def __init__(self, x, y, label="Resolution", game=None):
        self.x = x
        self.y = y
        self.label = label
        self.game = game
        self.font = load_ui_font(24)
        self.small_font = load_ui_font(20)

        self.resolutions = ["1280x720", "1920x1080", "2560x1440"]
        self.current_index = 0
        self.pending_index = 0

        self.prev_btn = None
        self.next_btn = None
        self.value_rect = None
        self.prev_hovered = False
        self.next_hovered = False

        self.settings = GameSettings()
        self.audio = AudioManager()

        current_res = self.settings.resolution
        if current_res in self.resolutions:
            self.current_index = self.resolutions.index(current_res)
            self.pending_index = self.current_index

        self._create_buttons(x, y)

    def _create_buttons(self, x, y):
        self.prev_btn = pygame.Rect(x + 160, y, 40, 40)
        self.next_btn = pygame.Rect(x + 380, y, 40, 40)
        self.value_rect = pygame.Rect(x + 210, y, 160, 40)

    def handle_click(self, pos):
        if self.prev_btn and self.prev_btn.collidepoint(pos):
            self.pending_index = (self.pending_index - 1) % len(self.resolutions)
            self.audio.play_sound("button_click", volume_override=0.3)
            return True
        elif self.next_btn and self.next_btn.collidepoint(pos):
            self.pending_index = (self.pending_index + 1) % len(self.resolutions)
            self.audio.play_sound("button_click", volume_override=0.3)
            return True
        return False

    def handle_hover(self, pos):
        self.prev_hovered = bool(self.prev_btn and self.prev_btn.collidepoint(pos))
        self.next_hovered = bool(self.next_btn and self.next_btn.collidepoint(pos))

    def get_pending_resolution(self):
        return self.resolutions[self.pending_index]

    def draw(self, screen):
        self._create_buttons(self.x, self.y)

        label_text = self.font.render(f"{self.label}", True, PARCHMENT)
        screen.blit(label_text, (self.x, self.y + 8))

        for rect, hovered, arrow in [(self.prev_btn, self.prev_hovered, "<"),
                                      (self.next_btn, self.next_hovered, ">")]:
            pygame.draw.rect(screen, STONE_LIGHT if hovered else STONE_MID, rect, border_radius=5)
            pygame.draw.rect(screen, GOLD_BRIGHT if hovered else GOLD, rect, 2, border_radius=5)
            t = self.small_font.render(arrow, True, PARCHMENT)
            screen.blit(t, (rect.x + (rect.width - t.get_width()) // 2, rect.y + 8))

        pygame.draw.rect(screen, STONE_DARK, self.value_rect, border_radius=5)
        pygame.draw.rect(screen, GOLD, self.value_rect, 2, border_radius=5)
        res_text = self.small_font.render(self.resolutions[self.pending_index], True, GOLD_BRIGHT)
        screen.blit(res_text, (self.value_rect.x + (self.value_rect.width - res_text.get_width()) // 2,
                                self.value_rect.y + 9))