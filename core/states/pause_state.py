# core/states/pause_state.py
import pygame
from core.state_manager import State
from core.audio import AudioManager 
from core.settings import GameSettings
from ui.settings import Slider
from core.font_loader import load_ui_font, load_title_font
from core.theme import (
    GOLD, GOLD_BRIGHT, GOLD_DIM, STONE_DARK, STONE_MID, STONE_LIGHT,
    PARCHMENT, PARCHMENT_DIM, TEAL_GLOW
)


def _draw_glow(screen, rect, color=TEAL_GLOW, pad=8, alpha=60, radius=10):
    glow = pygame.Surface((rect.width + pad * 2, rect.height + pad * 2), pygame.SRCALPHA)
    pygame.draw.rect(glow, (*color, alpha), glow.get_rect(), border_radius=radius)
    screen.blit(glow, (rect.x - pad, rect.y - pad))


def _draw_button(screen, rect, text, hovered=False, color=STONE_MID, border_color=GOLD):
    shadow_rect = rect.copy()
    shadow_rect.x += 3
    shadow_rect.y += 4
    shadow_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    shadow_surf.fill((0, 0, 0, 100))
    screen.blit(shadow_surf, shadow_rect.topleft)

    base_color = STONE_LIGHT if hovered else color
    btn_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    btn_surf.fill((*base_color, 235))
    screen.blit(btn_surf, rect.topleft)

    if hovered:
        _draw_glow(screen, rect, TEAL_GLOW, pad=8, alpha=55)

    border = GOLD_BRIGHT if hovered else border_color
    pygame.draw.rect(screen, border, rect, 2, border_radius=6)

    text_color = GOLD_BRIGHT if hovered else PARCHMENT
    font = load_ui_font(24)
    text_surf = font.render(text, True, text_color)
    screen.blit(text_surf, (rect.x + (rect.width - text_surf.get_width()) // 2,
                            rect.y + (rect.height - text_surf.get_height()) // 2))


class PauseState(State):
    def __init__(self, game):
        super().__init__(game)
        self.title_font = load_title_font(52)
        self.small_font = load_ui_font(22)
        self.audio = AudioManager()
        self.settings = GameSettings()
        self.click_cooldown = 0.0

        self.master_slider = None
        self.music_slider = None
        self.sfx_slider = None

        self.resume_btn = None
        self.save_btn = None
        self.menu_btn = None

        self._init_ui()
        self._pause_sounds()

    def _pause_sounds(self):
        """Останавливает все звуковые эффекты при входе в паузу"""
        # ✅ Останавливаем звук огнемёта через AudioManager
        self.audio.flame_reset()
        self.audio.stop_all_sfx()
        print("🔇 All SFX paused (music continues)")

    def _resume_sounds(self):
        """Возобновляет звуки при выходе из паузы"""
        # ✅ Сбрасываем счётчик огнемёта
        self.audio.flame_reset()
        
        # Пересчитываем активные огнемёты
        playing_state = self.game.state_manager._states.get('PLAYING')
        if playing_state:
            for tower in playing_state.towers:
                if tower.id == 'flamethrower' and tower.flame_target:
                    self.audio.flame_start()
        
        # Сбрасываем состояния звуков всех башен
        if playing_state and hasattr(playing_state, 'reset_all_tower_sounds'):
            playing_state.reset_all_tower_sounds()
        
        print("🔊 Sounds resumed (states reset)")

    def _init_ui(self):
        screen_w, screen_h = self.game.render_width, self.game.render_height
        center_x = screen_w // 2
        start_y = screen_h // 2 - 160

        slider_width = 320
        slider_x = center_x - slider_width // 2

        self.master_slider = Slider(
            slider_x, start_y + 80, slider_width, 24,
            0.0, 1.0, self.settings.master_volume, "Master"
        )
        self.music_slider = Slider(
            slider_x, start_y + 150, slider_width, 24,
            0.0, 1.0, self.settings.music_volume, "Music"
        )
        self.sfx_slider = Slider(
            slider_x, start_y + 220, slider_width, 24,
            0.0, 1.0, self.settings.sfx_volume, "SFX"
        )

        btn_w = 200
        btn_h = 48
        self.resume_btn = pygame.Rect(center_x - btn_w // 2, start_y + 290, btn_w, btn_h)
        self.save_btn = pygame.Rect(center_x - btn_w // 2, start_y + 350, btn_w, btn_h)
        self.menu_btn = pygame.Rect(center_x - btn_w // 2, start_y + 410, btn_w, btn_h)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._apply_volumes()
                self._resume_sounds()
                self.game.state_manager.change_state('PLAYING')

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.click_cooldown <= 0:
                    pos = event.pos
                    for slider in [self.master_slider, self.music_slider, self.sfx_slider]:
                        if slider.handle_event(pos):
                            self._apply_volumes()
                            return

                    if self.resume_btn and self.resume_btn.collidepoint(pos):
                        self._apply_volumes()
                        self._resume_sounds()
                        self._resume()
                    elif self.save_btn and self.save_btn.collidepoint(pos):
                        self._save_game()
                    elif self.menu_btn and self.menu_btn.collidepoint(pos):
                        self._resume_sounds()
                        self._go_menu()

            elif event.type == pygame.MOUSEMOTION:
                for slider in [self.master_slider, self.music_slider, self.sfx_slider]:
                    if slider.dragging:
                        slider.handle_event(event.pos)
                        self._apply_volumes()
                    slider.handle_hover(event.pos)

            elif event.type == pygame.MOUSEBUTTONUP:
                for slider in [self.master_slider, self.music_slider, self.sfx_slider]:
                    slider.release()

    def _apply_volumes(self):
        self.settings.set("master_volume", self.master_slider.value)
        self.settings.set("music_volume", self.music_slider.value)
        self.settings.set("sfx_volume", self.sfx_slider.value)
        self.audio.update_volumes()

    def update(self, dt):
        if self.click_cooldown > 0:
            self.click_cooldown -= dt

    def draw_scene(self, renderer):
        """Игровая сцена (GPU) остаётся фоном под меню паузы"""
        playing_state = self.game.state_manager._states.get('PLAYING')
        if playing_state and hasattr(playing_state, 'draw_scene'):
            playing_state.draw_scene(renderer)

    def draw(self, screen):
        screen_w, screen_h = self.game.render_width, self.game.render_height

        playing_state = self.game.state_manager._states.get('PLAYING')
        if playing_state:
            playing_state.draw(screen)

        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        title = self.title_font.render("PAUSED", True, GOLD)
        shadow = self.title_font.render("PAUSED", True, (0, 0, 0))
        tx = screen_w // 2 - title.get_width() // 2
        screen.blit(shadow, (tx + 3, screen_h // 2 - 230))
        screen.blit(title, (tx, screen_h // 2 - 233))

        for slider in [self.master_slider, self.music_slider, self.sfx_slider]:
            slider.draw(screen)

        _draw_button(screen, self.resume_btn, "RESUME (ESC)",
                     self.resume_btn and self.resume_btn.collidepoint(pygame.mouse.get_pos()))
        _draw_button(screen, self.save_btn, "SAVE GAME",
                     self.save_btn and self.save_btn.collidepoint(pygame.mouse.get_pos()))
        _draw_button(screen, self.menu_btn, "MAIN MENU",
                     self.menu_btn and self.menu_btn.collidepoint(pygame.mouse.get_pos()))

    def _resume(self):
        self.click_cooldown = 0.5
        self.audio.play_sound("button_click")
        self.game.state_manager.change_state('PLAYING')

    def _save_game(self):
        self.click_cooldown = 0.5
        self.audio.play_sound("button_click")
        from services.save_system import SaveSystem
        save = SaveSystem()
        playing_state = self.game.state_manager._states.get('PLAYING')
        if playing_state and hasattr(playing_state, 'player'):
            save.save_player(playing_state.player)
            print("✅ Game saved!")

    def _go_menu(self):
        self.click_cooldown = 0.5
        self._apply_volumes()
        self.audio.play_sound("button_click")
        
        # Останавливаем все звуковые эффекты перед переходом в меню
        self.audio.flame_force_stop()
        self.audio.stop_all_sfx()
        
        if self.audio.settings.music_enabled:
            self.audio.play_music("menu_theme.wav")
        self.game.state_manager.change_state('MENU')

    def on_resolution_changed(self, screen_w, screen_h):
        self._init_ui()