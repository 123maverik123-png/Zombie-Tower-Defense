# ui/settings/display_mode.py
import pygame
from core.settings import GameSettings
from core.audio import AudioManager
from core.font_loader import load_ui_font
from core.theme import GOLD, GOLD_DIM, STONE_MID, STONE_LIGHT, PARCHMENT, PARCHMENT_DIM, TEAL_GLOW
from .draw import draw_glow


class DisplayModeSelector:
    """Выбор режима отображения (окно/полный экран/без рамки)"""
    
    def __init__(self, x, y, label="Display Mode", game=None):
        self.x = x
        self.y = y
        self.label = label
        self.game = game
        self.font = load_ui_font(24)
        self.small_font = load_ui_font(20)

        self.modes = ["window", "fullscreen", "borderless"]
        self.mode_labels = ["Window", "Fullscreen", "Borderless"]

        self.settings = GameSettings()
        self.audio = AudioManager()

        self.current_mode = self.settings.display_mode
        if self.current_mode not in self.modes:
            self.current_mode = "window"

        self.pending_mode = self.current_mode
        self.hover_index = -1

        self._create_buttons(self.x, self.y)

    def _create_buttons(self, x, y):
        btn_width = 140
        btn_height = 42
        spacing = 12
        total_width = btn_width * 3 + spacing * 2
        start_x = x + (400 - total_width) // 2

        self.buttons = []
        for i, mode in enumerate(self.modes):
            btn_rect = pygame.Rect(
                start_x + i * (btn_width + spacing),
                y + 36,
                btn_width,
                btn_height
            )
            self.buttons.append({'rect': btn_rect, 'mode': mode, 'label': self.mode_labels[i]})

    def handle_click(self, pos):
        for btn in self.buttons:
            if btn['rect'].collidepoint(pos):
                if btn['mode'] != self.pending_mode:
                    self.pending_mode = btn['mode']
                    self.audio.play_sound("button_click", volume_override=0.3)
                    return True
        return False

    def handle_hover(self, pos):
        self.hover_index = -1
        for i, btn in enumerate(self.buttons):
            if btn['rect'].collidepoint(pos):
                self.hover_index = i
                break

    def get_pending_mode(self):
        return self.pending_mode

    def draw(self, screen):
        self._create_buttons(self.x, self.y)

        label_text = self.font.render(f"{self.label}", True, PARCHMENT)
        screen.blit(label_text, (self.x, self.y + 6))

        for i, btn in enumerate(self.buttons):
            rect = btn['rect']
            is_selected = btn['mode'] == self.pending_mode
            is_hovered = i == self.hover_index

            if is_selected:
                draw_glow(screen, rect, TEAL_GLOW, pad=6, alpha=55, radius=8)
                color = STONE_LIGHT
                border_color = GOLD
            elif is_hovered:
                color = STONE_LIGHT
                border_color = GOLD
            else:
                color = STONE_MID
                border_color = GOLD_DIM

            pygame.draw.rect(screen, color, rect, border_radius=6)
            pygame.draw.rect(screen, border_color, rect, 2, border_radius=6)

            text_color = GOLD if is_selected else PARCHMENT_DIM
            text = self.small_font.render(btn['label'], True, text_color)
            screen.blit(text, (rect.x + (rect.width - text.get_width()) // 2, rect.y + 12))

            if is_selected:
                check = self.small_font.render("✓", True, GOLD)
                screen.blit(check, (rect.x + 6, rect.y + 4))