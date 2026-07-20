# core/states/game_over_state.py
import pygame
import os
from core.state_manager import State
from core.audio import AudioManager
from core.level_loader import build_level
from .play.state import PlayState
from core.font_loader import load_ui_font, load_title_font
from core.theme import (
    GOLD, GOLD_BRIGHT, STONE_DARK, STONE_MID, STONE_LIGHT,
    PARCHMENT, PARCHMENT_DIM, TEAL_GLOW, DANGER, DANGER_BRIGHT
)


def _draw_glow(screen, rect, color, pad=8, alpha=60, radius=10):
    glow = pygame.Surface((rect.width + pad * 2, rect.height + pad * 2), pygame.SRCALPHA)
    pygame.draw.rect(glow, (*color, alpha), glow.get_rect(), border_radius=radius)
    screen.blit(glow, (rect.x - pad, rect.y - pad))


class GameOverState(State):
    def __init__(self, game):
        super().__init__(game)
        
        # Останавливаем все звуковые эффекты при входе в Game Over
        self.audio = AudioManager()
        self.audio.stop_all_sfx()
        
        try:
            self.title_font = load_title_font(70)
        except:
            self.title_font = pygame.font.Font(None, 70)
        
        try:
            self.small_font = load_ui_font(32)
        except:
            self.small_font = pygame.font.Font(None, 32)

        self._music_started = False

        self.click_cooldown = 0.0

        self.restart_btn = None
        self.menu_btn = None
        self.exit_btn = None
        self.hovered = None

        self.background = None
        self._load_background()

        game_over_data = getattr(self.game, '_game_over_data', {})

        if game_over_data:
            self.level = game_over_data.get('level', 1)
            self.waves = game_over_data.get('waves', 0)
            self.kills = game_over_data.get('kills', 0)
            self.gold = game_over_data.get('gold', 0)
        else:
            playing = self.game.state_manager._states.get('PLAYING')
            if playing:
                self.level = getattr(playing, 'level_number', 1)
                self.waves = playing.player.stats.get('waves_survived', 0)
                self.kills = playing.player.stats.get('total_kills', 0)
                self.gold = playing.player.gold
            else:
                self.level = 1
                self.waves = 0
                self.kills = 0
                self.gold = 0

        self._retry_level = self.level
        self.last_screen_w = 0
        self.last_screen_h = 0

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
            if event.type == pygame.MOUSEMOTION:
                self.hovered = None
                for key, rect in [('restart', self.restart_btn),
                                   ('menu', self.menu_btn),
                                   ('exit', self.exit_btn)]:
                    if rect and rect.collidepoint(event.pos):
                        self.hovered = key
                        break

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.click_cooldown <= 0:
                    if self.restart_btn and self.restart_btn.collidepoint(event.pos):
                        self._restart()
                    elif self.menu_btn and self.menu_btn.collidepoint(event.pos):
                        self._go_levels()
                    elif self.exit_btn and self.exit_btn.collidepoint(event.pos):
                        self._exit_game()

    def update(self, dt):
        if self.click_cooldown > 0:
            self.click_cooldown -= dt

        if not self._music_started and self.audio.settings.music_enabled:
            self._music_started = True
            self.audio.play_music("game_over_theme.wav")

    def draw(self, screen):
        screen_w, screen_h = self.game.render_width, self.game.render_height

        if screen_w != self.last_screen_w or screen_h != self.last_screen_h:
            self.last_screen_w = screen_w
            self.last_screen_h = screen_h
            self._update_buttons(screen_w, screen_h)

        self._draw_background(screen, screen_w, screen_h)

        title_font_size = max(50, int(70 * (screen_w / 1920)))
        try:
            title_font = load_title_font(title_font_size)
        except:
            title_font = pygame.font.Font(None, title_font_size)
        
        text = title_font.render("YOU HAVE FALLEN", True, DANGER_BRIGHT)
        text_shadow = title_font.render("YOU HAVE FALLEN", True, (0, 0, 0))
        tx = screen_w // 2 - text.get_width() // 2
        ty = int(140 * (screen_h / 1080))
        screen.blit(text_shadow, (tx + 3, ty + 3))
        screen.blit(text, (tx, ty))

        panel_w = min(560, screen_w - 100)
        panel_rect = pygame.Rect(screen_w // 2 - panel_w // 2, ty + 100, panel_w, 200)
        panel_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel_surf.fill((*STONE_DARK, 210))
        screen.blit(panel_surf, panel_rect.topleft)
        pygame.draw.rect(screen, GOLD, panel_rect, 2, border_radius=8)

        mid_font_size = max(22, int(32 * (screen_w / 1920)))
        try:
            mid_font = load_ui_font(mid_font_size)
        except:
            mid_font = pygame.font.Font(None, mid_font_size)
        
        texts = [
            f"Level: {self.level}",
            f"Waves survived: {self.waves}",
            f"Enemies killed: {self.kills}",
            f"Gold earned: ${self.gold}"
        ]
        start_y = panel_rect.y + 20
        line_h = (panel_rect.height - 40) // len(texts)
        for i, t in enumerate(texts):
            txt = mid_font.render(t, True, PARCHMENT)
            screen.blit(txt, (screen_w // 2 - txt.get_width() // 2, start_y + i * line_h))

        self._draw_button(screen, self.restart_btn, self.hovered == 'restart', "RETRY LEVEL")
        self._draw_button(screen, self.menu_btn, self.hovered == 'menu', "LEVEL SELECT")
        self._draw_button(screen, self.exit_btn, self.hovered == 'exit', "EXIT TO MENU")

    def _draw_background(self, screen, screen_w, screen_h):
        screen.fill((15, 8, 8))
        if self.background:
            bg_scaled = pygame.transform.scale(self.background, (screen_w, screen_h))
            screen.blit(bg_scaled, (0, 0))

        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((40, 0, 0, 190))
        screen.blit(overlay, (0, 0))

    def _update_buttons(self, screen_w, screen_h):
        btn_width = int(300 * (screen_w / 1920))
        btn_height = int(55 * (screen_h / 1080))
        spacing = int(70 * (screen_h / 1080))

        center_x = screen_w // 2 - btn_width // 2
        start_y = int(500 * (screen_h / 1080))

        self.restart_btn = pygame.Rect(center_x, start_y, btn_width, btn_height)
        self.menu_btn = pygame.Rect(center_x, start_y + spacing, btn_width, btn_height)
        self.exit_btn = pygame.Rect(center_x, start_y + spacing * 2, btn_width, btn_height)

    def _draw_button(self, screen, rect, hovered, text):
        if rect is None:
            return

        shadow_rect = rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 4
        shadow_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 110))
        screen.blit(shadow_surf, shadow_rect.topleft)

        base_color = STONE_LIGHT if hovered else STONE_MID
        btn_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        btn_surf.fill((*base_color, 235))
        screen.blit(btn_surf, rect.topleft)

        if hovered:
            _draw_glow(screen, rect, TEAL_GLOW, pad=8, alpha=55, radius=10)

        border_color = GOLD_BRIGHT if hovered else GOLD
        pygame.draw.rect(screen, border_color, rect, 2, border_radius=6)

        font_size = max(18, int(30 * (rect.width / 300)))
        try:
            btn_font = load_ui_font(font_size)
        except:
            btn_font = pygame.font.Font(None, font_size)
        
        text_color = GOLD_BRIGHT if hovered else PARCHMENT
        btn_text = btn_font.render(text, True, text_color)
        screen.blit(btn_text, (rect.x + (rect.width - btn_text.get_width()) // 2,
                                rect.y + (rect.height - btn_text.get_height()) // 2))

    def _restart(self):
        level = self._retry_level
        self.click_cooldown = 0.5
        self.audio.play_sound("button_click")
        level_data = build_level(level)
        
        # ✅ Убираем старый PlayState, если он существует
        if 'PLAYING' in self.game.state_manager._states:
            del self.game.state_manager._states['PLAYING']
        
        play_state = PlayState(self.game, level, level_data)
        self.game.state_manager.add_state('PLAYING', play_state)
        self.game.state_manager.change_state('PLAYING')

    def _go_levels(self):
        self.click_cooldown = 0.5
        self.audio.play_sound("button_click")
        
        self.audio.stop_all_sfx()

        if self.audio.settings.music_enabled:
            self.audio.play_music("menu_theme.wav")

        self.game.state_manager.change_state('LEVEL_SELECT')

    def _exit_game(self):
        self.click_cooldown = 0.5
        self.audio.play_sound("button_click")
        
        self.audio.stop_all_sfx()

        if self.audio.settings.music_enabled:
            self.audio.play_music("menu_theme.wav")

        self.game.state_manager.change_state('MENU')

    def on_resolution_changed(self, screen_w, screen_h):
        pass