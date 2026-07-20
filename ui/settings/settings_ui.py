# ui/settings/settings_ui.py
import pygame
from core.settings import GameSettings
from core.audio import AudioManager
from core.font_loader import load_ui_font, load_title_font
from core.theme import GOLD, GOLD_BRIGHT, STONE_DARK, STONE_MID, STONE_LIGHT, PARCHMENT, TEAL_GLOW
from .slider import Slider
from .toggle import ToggleButton
from .display_mode import DisplayModeSelector
from .resolution import ResolutionSelector
from .draw import draw_glow


class SettingsUI:
    """Основной UI для страницы настроек"""
    
    def __init__(self, game):
        self.game = game
        self.settings = GameSettings()
        self.audio = AudioManager()

        self.sliders = []
        self.toggles = []
        self.selectors = []

        self.dragging_slider = None
        self.apply_btn = None
        self.apply_hovered = False

        self.initialized = False
        self._last_screen_w = 0
        self._last_screen_h = 0
        
        # ✅ Флаг для предотвращения множественных событий
        self._applying = False

    def _init_elements(self, screen_w, screen_h):
        """Инициализирует все элементы UI"""
        self.initialized = True

        center_x = screen_w // 2
        start_y = 130

        self.sliders = []
        self.toggles = []
        self.selectors = []

        slider_width = 440
        slider_x = center_x - slider_width // 2

        self.master_slider = Slider(slider_x, start_y, slider_width, 24, 0.0, 1.0,
                                     self.settings.master_volume, "Master Volume")
        self.music_slider = Slider(slider_x, start_y + 90, slider_width, 24, 0.0, 1.0,
                                    self.settings.music_volume, "Music Volume")
        self.sfx_slider = Slider(slider_x, start_y + 180, slider_width, 24, 0.0, 1.0,
                                  self.settings.sfx_volume, "SFX Volume")

        self.sliders.extend([self.master_slider, self.music_slider, self.sfx_slider])

        toggle_x = center_x - 60
        toggle_y = start_y + 270

        self.sound_toggle = ToggleButton(toggle_x, toggle_y, "Sound", self.settings.sound_enabled)
        self.music_toggle = ToggleButton(toggle_x + 260, toggle_y, "Music", self.settings.music_enabled)
        self.fps_toggle = ToggleButton(toggle_x, toggle_y + 50, "Show FPS", self.settings.show_fps)

        self.toggles.extend([self.sound_toggle, self.music_toggle, self.fps_toggle])

        self.display_selector = DisplayModeSelector(center_x - 200, start_y + 370, "Display Mode", self.game)
        self.selectors.append(self.display_selector)

        self.resolution_selector = ResolutionSelector(center_x - 200, start_y + 460, "Resolution", self.game)
        self.selectors.append(self.resolution_selector)

        self.apply_btn = pygame.Rect(center_x - 110, start_y + 550, 220, 52)

    def _apply_settings(self):
        """Применяет все настройки"""
        # ✅ Предотвращаем повторный вызов
        if self._applying:
            return
        self._applying = True
        
        try:
            self.settings.set("master_volume", self.master_slider.value)
            self.settings.set("music_volume", self.music_slider.value)
            self.settings.set("sfx_volume", self.sfx_slider.value)
            self.settings.set("sound_enabled", self.sound_toggle.is_on)
            self.settings.set("music_enabled", self.music_toggle.is_on)
            self.settings.set("show_fps", self.fps_toggle.is_on)

            self.audio.update_volumes()

            if not self.music_toggle.is_on:
                self.audio.stop_music()
            else:
                if not pygame.mixer.music.get_busy():
                    self.audio.play_music("menu_theme.wav")

            new_res = self.resolution_selector.get_pending_resolution()
            new_mode = self.display_selector.get_pending_mode()

            self.settings.set("resolution", new_res)
            self.settings.set("display_mode", new_mode)
            
            # ✅ Сохраняем настройки в файл
            self.settings.save()

            print(f"✅ Applied: Resolution={new_res}, DisplayMode={new_mode}")
            
            # ✅ Отправляем ОДНО событие для смены разрешения
            pygame.event.post(pygame.event.Event(pygame.USEREVENT, code=1))
            
        finally:
            self._applying = False

    def handle_click(self, pos):
        """Обрабатывает клики по UI"""
        for slider in self.sliders:
            if slider.handle_event(pos):
                self.dragging_slider = slider
                return

        for toggle in self.toggles:
            if toggle.handle_click(pos):
                return

        for selector in self.selectors:
            if selector.handle_click(pos):
                return

        if self.apply_btn and self.apply_btn.collidepoint(pos):
            self._apply_settings()
            self.audio.play_sound("button_click")
            return True

        return False

    def handle_mouse_move(self, pos):
        """Обрабатывает движение мыши"""
        if self.dragging_slider:
            self.dragging_slider.handle_event(pos)

        for slider in self.sliders:
            slider.handle_hover(pos)
        for toggle in self.toggles:
            toggle.handle_hover(pos)
        for selector in self.selectors:
            selector.handle_hover(pos)

        self.apply_hovered = bool(self.apply_btn and self.apply_btn.collidepoint(pos))

    def handle_mouse_release(self):
        """Обрабатывает отпускание кнопки мыши"""
        if self.dragging_slider:
            self.dragging_slider.release()
            self.dragging_slider = None

    def draw(self, screen):
        """Отрисовывает UI настроек"""
        screen_w, screen_h = self.game.render_width, self.game.render_height

        if not self.initialized:
            self._init_elements(screen_w, screen_h)

        if self._last_screen_w != screen_w or self._last_screen_h != screen_h:
            self._init_elements(screen_w, screen_h)
            self._last_screen_w = screen_w
            self._last_screen_h = screen_h

        # Панель-подложка
        panel_rect = pygame.Rect(
            screen_w // 2 - 380,
            50,
            760,
            min(screen_h - 100, 720)
        )
        panel_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel_surface.fill((10, 9, 8, 180))
        screen.blit(panel_surface, (panel_rect.x, panel_rect.y))
        pygame.draw.rect(screen, GOLD, panel_rect, 2, border_radius=8)

        # Заголовок
        title_font = load_title_font(46)
        title = title_font.render("SETTINGS", True, GOLD)
        title_shadow = title_font.render("SETTINGS", True, (0, 0, 0))
        tx = screen_w // 2 - title.get_width() // 2
        screen.blit(title_shadow, (tx + 2, 74))
        screen.blit(title, (tx, 72))

        # Рисуем все элементы
        for slider in self.sliders:
            slider.draw(screen)

        for toggle in self.toggles:
            toggle.draw(screen)

        for selector in self.selectors:
            selector.draw(screen)

        # Кнопка APPLY
        if self.apply_btn:
            shadow_rect = self.apply_btn.copy()
            shadow_rect.x += 3
            shadow_rect.y += 4
            shadow_surf = pygame.Surface((self.apply_btn.width, self.apply_btn.height), pygame.SRCALPHA)
            shadow_surf.fill((0, 0, 0, 100))
            screen.blit(shadow_surf, shadow_rect.topleft)

            base_color = STONE_LIGHT if self.apply_hovered else STONE_MID
            btn_surf = pygame.Surface((self.apply_btn.width, self.apply_btn.height), pygame.SRCALPHA)
            btn_surf.fill((*base_color, 235))
            screen.blit(btn_surf, self.apply_btn.topleft)

            if self.apply_hovered:
                draw_glow(screen, self.apply_btn, TEAL_GLOW, pad=8, alpha=60, radius=10)

            border_color = GOLD_BRIGHT if self.apply_hovered else GOLD
            pygame.draw.rect(screen, border_color, self.apply_btn, 2, border_radius=6)

            btn_font = load_ui_font(28)
            text_color = GOLD_BRIGHT if self.apply_hovered else PARCHMENT
            btn_text = btn_font.render("APPLY", True, text_color)
            screen.blit(btn_text, (self.apply_btn.x + (self.apply_btn.width - btn_text.get_width()) // 2,
                                    self.apply_btn.y + (self.apply_btn.height - btn_text.get_height()) // 2))

    def update(self, dt):
        """Обновляет состояние UI"""
        for toggle in self.toggles:
            toggle.update(dt)