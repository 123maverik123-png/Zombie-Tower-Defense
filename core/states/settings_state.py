# core/states/settings_state.py
import pygame
import os
from core.state_manager import State
from core.audio import AudioManager
from core.settings import GameSettings
from ui.settings import SettingsUI
from core.font_loader import load_font, load_ui_font
from core.theme import GOLD, GOLD_BRIGHT, STONE_MID, STONE_LIGHT, PARCHMENT, TEAL_GLOW


class SettingsState(State):
    def __init__(self, game):
        super().__init__(game)
        
        # Останавливаем все звуковые эффекты при входе в настройки
        self.audio = AudioManager()
        self.audio.stop_all_sfx()
        
        self.settings_ui = SettingsUI(game)
        self.font = load_font(50)
        self.small_font = load_ui_font(24)
        self.click_cooldown = 0.0
        self._music_started = False
        self.settings = GameSettings()
        self.background = None
        self.back_btn = pygame.Rect(20, 20, 130, 44)
        self.back_hovered = False
        self._load_background()

    def _load_background(self):
        bg_path = "assets/images/menu_bg.jpg"
        if os.path.exists(bg_path):
            try:
                self.background = pygame.image.load(bg_path).convert()
            except Exception:
                self.background = None
        else:
            self.background = None

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.click_cooldown <= 0:
                    if self.back_btn and self.back_btn.collidepoint(event.pos):
                        self._go_back()
                    self.settings_ui.handle_click(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                self.back_hovered = self.back_btn.collidepoint(event.pos)
                self.settings_ui.handle_mouse_move(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                self.settings_ui.handle_mouse_release()
            elif event.type == pygame.USEREVENT and event.code == 1:
                self.game.apply_display_mode()

    def update(self, dt):
        if self.click_cooldown > 0:
            self.click_cooldown -= dt
        self.settings_ui.update(dt)

        if not self._music_started and self.audio.settings.music_enabled:
            self._music_started = True
            self.audio.play_music("menu_theme.wav")

        if not self.audio.is_music_playing() and self.audio.settings.music_enabled:
            self.audio.play_music("menu_theme.wav")

    def draw(self, screen):
        screen_w, screen_h = self.game.render_width, self.game.render_height

        self._draw_background(screen, screen_w, screen_h)

        self.settings_ui.draw(screen)

        self._draw_back_button(screen)

    def _draw_background(self, screen, screen_w, screen_h):
        screen.fill((15, 14, 12))

        if self.background:
            bg_scaled = pygame.transform.scale(self.background, (screen_w, screen_h))
            screen.blit(bg_scaled, (0, 0))
        else:
            self._draw_fallback_background(screen)

        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        screen.blit(overlay, (0, 0))

        vignette = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        pad = 220
        for i in range(pad):
            alpha = int(120 * (1 - i / pad))
            pygame.draw.rect(vignette, (0, 0, 0, alpha),
                              (i, i, screen_w - i * 2, screen_h - i * 2), 2)
        screen.blit(vignette, (0, 0))

    def _draw_fallback_background(self, screen):
        screen_w, screen_h = self.game.render_width, self.game.render_height
        for i in range(screen_h):
            t = i / screen_h
            r = int(15 + 25 * t)
            g = int(14 + 18 * t)
            b = int(18 + 30 * t)
            pygame.draw.line(screen, (r, g, b), (0, i), (screen_w, i))

    def _draw_back_button(self, screen):
        rect = self.back_btn

        shadow_rect = rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 3
        shadow_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 100))
        screen.blit(shadow_surf, shadow_rect.topleft)

        base_color = STONE_LIGHT if self.back_hovered else STONE_MID
        btn_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        btn_surf.fill((*base_color, 235))
        screen.blit(btn_surf, rect.topleft)

        if self.back_hovered:
            glow = pygame.Surface((rect.width + 16, rect.height + 16), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*TEAL_GLOW, 55), glow.get_rect(), border_radius=10)
            screen.blit(glow, (rect.x - 8, rect.y - 8))

        border_color = GOLD_BRIGHT if self.back_hovered else GOLD
        pygame.draw.rect(screen, border_color, rect, 2, border_radius=6)

        text_color = GOLD_BRIGHT if self.back_hovered else PARCHMENT
        btn_text = self.small_font.render("BACK", True, text_color)
        screen.blit(btn_text, (rect.x + (rect.width - btn_text.get_width()) // 2,
                                rect.y + (rect.height - btn_text.get_height()) // 2))

    def _go_back(self):
        self.click_cooldown = 0.3
        self.audio.play_sound("button_click")
        
        # Останавливаем все звуковые эффекты перед переходом в меню
        self.audio.stop_all_sfx()

        if self.audio.settings.music_enabled:
            self.audio.play_music("menu_theme.wav")

        self.game.state_manager.change_state('MENU')