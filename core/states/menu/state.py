# core/states/menu/state.py
import pygame
import sys  # ✅ Добавлен импорт sys
from core.state_manager import State
from core.audio import AudioManager
from core.event_bus import EventBus  # ✅ ДОБАВЛЕН ИМПОРТ
from core.level_loader import build_level  # ✅ ДОБАВЛЕН ИМПОРТ
from services.profile_manager import ProfileManager
from .button import MenuButton
from .draw import MenuDraw
from .handlers import MenuHandlers
from .utils import load_background, load_icons


class MenuState(State):
    """Состояние главного меню"""
    
    def __init__(self, game, profile_manager=None, skip_check=False):
        super().__init__(game)

        # Останавливаем все звуковые эффекты при входе в меню
        self.audio = AudioManager()
        self.audio.stop_all_sfx()
        
        self._music_started = False
        self.click_cooldown = 0.0
        self._checked_profiles = False
        self._skip_check = skip_check

        self.last_screen_w = 0
        self.last_screen_h = 0
        self.background = load_background()
        self.icons = load_icons()

        self.buttons = {}
        self.panel_rect = None
        self._update_buttons(game.render_width, game.render_height)

        self.profile_manager = profile_manager if profile_manager else ProfileManager()

        if self._skip_check:
            self._checked_profiles = True

        # Подсистемы
        self.drawer = MenuDraw(self)
        self.handlers = MenuHandlers(self)

    def _update_buttons(self, screen_w, screen_h):
        """Создает кнопки меню"""
        btn_width = 500
        btn_height = 100
        spacing = 20
        panel_x = 80

        specs = [
            ('play', "PLAY", "Continue your campaign"),
            ('levels', "LEVELS", "Choose any unlocked stage"),
            ('settings', "SETTINGS", "Audio, video, controls"),
            ('switch', "SWITCH PROFILE", "Change save file"),
            ('editor', "MAP EDITOR", "Design your own path"),
            ('exit', "EXIT", "Leave the realm"),
        ]
        
        total_height = len(specs) * (btn_height + spacing) - spacing
        top_y = (screen_h - total_height) // 2

        self.buttons = {}
        for i, (key, title, subtitle) in enumerate(specs):
            rect = pygame.Rect(panel_x, top_y + i * (btn_height + spacing), btn_width, btn_height)
            self.buttons[key] = MenuButton(rect, self.icons.get(key), title, subtitle)

        self.panel_rect = pygame.Rect(
            panel_x - 30, 
            top_y - 40,
            btn_width + 60, 
            len(specs) * (btn_height + spacing) + 80
        )

    def _check_profiles(self):
        """Проверяет наличие профилей"""
        if self._checked_profiles:
            return
        self._checked_profiles = True

        if self.profile_manager.get_current_profile():
            return

        if not self.profile_manager.has_profile():
            from ..profile_create_state import ProfileCreateState
            self.game.state_manager.add_state('PROFILE_CREATE', ProfileCreateState(self.game, from_select=False))
            self.game.state_manager.change_state('PROFILE_CREATE')
            return

        if self.profile_manager.get_profiles_count() == 1:
            profiles = self.profile_manager.get_all_profiles()
            self.profile_manager.load_profile(profiles[0].name)
            return

        from ..profile_select_state import ProfileSelectState
        self.game.state_manager.add_state('PROFILE_SELECT', ProfileSelectState(self.game))
        self.game.state_manager.change_state('PROFILE_SELECT')

    def handle_events(self, events):
        self.handlers.handle_events(events)

    def update(self, dt):
        if self.click_cooldown > 0:
            self.click_cooldown -= dt

        self._check_profiles()

        # Музыка
        if not self._music_started and self.audio.settings.music_enabled:
            self._music_started = True
            self.audio.play_music("menu_theme.wav")

        if not self.audio.is_music_playing() and self.audio.settings.music_enabled:
            self.audio.play_music("menu_theme.wav")

    def draw(self, screen):
        screen_w, screen_h = self.game.render_width, self.game.render_height

        if self.last_screen_w != screen_w or self.last_screen_h != screen_h:
            self._update_buttons(screen_w, screen_h)
            self.last_screen_w = screen_w
            self.last_screen_h = screen_h

        self.drawer.draw(screen)

    def on_resolution_changed(self, screen_w, screen_h):
        pass
    
    # ===== ОБРАБОТЧИКИ КНОПОК =====
    
    def _start_game(self):
        self.click_cooldown = 0.3
        self.audio.play_sound("button_click")
        EventBus.clear()

        profile = self.profile_manager.get_current_profile()

        if not profile:
            print("⚠️ No profile found, showing create profile")
            from ..profile_create_state import ProfileCreateState
            self.game.state_manager.add_state('PROFILE_CREATE', ProfileCreateState(self.game, from_select=False))
            self.game.state_manager.change_state('PROFILE_CREATE')
            return

        level = profile.current_level
        level_data = build_level(level)

        if self.audio.settings.music_enabled:
            self.audio.play_music("game_theme.wav")

        # ✅ Убираем старый PlayState, если он существует
        if 'PLAYING' in self.game.state_manager._states:
            del self.game.state_manager._states['PLAYING']
        
        from ..play.state import PlayState
        self.game.state_manager.add_state('PLAYING', PlayState(self.game, level, level_data))
        self.game.state_manager.change_state('PLAYING')

    def _go_to_levels(self):
        self.click_cooldown = 0.3
        self.audio.play_sound("button_click")
        from ..level_select_state import LevelSelectState
        self.game.state_manager.add_state('LEVEL_SELECT', LevelSelectState(self.game))
        self.game.state_manager.change_state('LEVEL_SELECT')

    def _go_to_settings(self):
        self.click_cooldown = 0.3
        self.audio.play_sound("button_click")
        from ..settings_state import SettingsState
        self.game.state_manager.add_state('SETTINGS', SettingsState(self.game))
        self.game.state_manager.change_state('SETTINGS')

    def _switch_profile(self):
        self.click_cooldown = 0.3
        self.audio.play_sound("button_click")
        from ..profile_select_state import ProfileSelectState
        self.game.state_manager.add_state('PROFILE_SELECT', ProfileSelectState(self.game))
        self.game.state_manager.change_state('PROFILE_SELECT')

    def _go_to_editor(self):
        self.click_cooldown = 0.3
        self.audio.play_sound("button_click")
        from ..map_editor_state import MapEditorState
        self.game.state_manager.add_state('MAP_EDITOR', MapEditorState(self.game))
        self.game.state_manager.change_state('MAP_EDITOR')

    def _exit_game(self):
        self.audio.play_sound("button_click")
        pygame.quit()
        sys.exit()