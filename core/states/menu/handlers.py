# core/states/menu/handlers.py
import pygame
import sys
from core.event_bus import EventBus
from core.audio import AudioManager
from core.level_loader import build_level


class MenuHandlers:
    """Обработчики событий главного меню"""
    
    def __init__(self, state):
        self.state = state
        self.audio = AudioManager()
    
    def handle_events(self, events):
        state = self.state
        
        for event in events:
            if event.type == pygame.MOUSEMOTION:
                self._handle_hover(event.pos)
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state.click_cooldown <= 0:
                    self._handle_click(event.pos)

    def _handle_hover(self, pos):
        state = self.state
        for btn in state.buttons.values():
            btn.handle_hover(pos)

    def _handle_click(self, pos):
        state = self.state
        for key, btn in state.buttons.items():
            if btn.handle_click(pos):
                self._on_button_click(key)
                break

    def _on_button_click(self, key):
        actions = {
            'play': self._start_game,
            'levels': self._go_to_levels,
            'settings': self._go_to_settings,
            'switch': self._switch_profile,
            'editor': self._go_to_editor,
            'exit': self._exit_game,
        }
        action = actions.get(key)
        if action:
            action()

    def _start_game(self):
        state = self.state
        state.click_cooldown = 0.3
        self.audio.play_sound("button_click")
        EventBus.clear()

        profile = state.profile_manager.get_current_profile()

        if not profile:
            print("⚠️ No profile found, showing create profile")
            from ..profile_create_state import ProfileCreateState
            state.game.state_manager.add_state('PROFILE_CREATE', ProfileCreateState(state.game, from_select=False))
            state.game.state_manager.change_state('PROFILE_CREATE')
            return

        # Сложность ещё не выбрана — показываем окно выбора (оно само
        # сохранит выбор в профиль и запустит игру).
        if profile.difficulty is None:
            from ..difficulty_select_state import DifficultySelectState
            state.game.state_manager.add_state('DIFFICULTY_SELECT', DifficultySelectState(state.game))
            state.game.state_manager.change_state('DIFFICULTY_SELECT')
            return

        # Сложность уже выбрана — запускаем бой через интро-сцену
        # (сглаживает резкий переход; сама создаст PLAYING по окончании).
        from ..intro_state import launch_game_with_intro
        launch_game_with_intro(state.game, profile, self.audio)

    def _go_to_levels(self):
        state = self.state
        state.click_cooldown = 0.3
        self.audio.play_sound("button_click")
        from ..level_select_state import LevelSelectState
        state.game.state_manager.add_state('LEVEL_SELECT', LevelSelectState(state.game))
        state.game.state_manager.change_state('LEVEL_SELECT')

    def _go_to_settings(self):
        state = self.state
        state.click_cooldown = 0.3
        self.audio.play_sound("button_click")
        from ..settings_state import SettingsState
        state.game.state_manager.add_state('SETTINGS', SettingsState(state.game))
        state.game.state_manager.change_state('SETTINGS')

    def _switch_profile(self):
        state = self.state
        state.click_cooldown = 0.3
        self.audio.play_sound("button_click")
        from ..profile_select_state import ProfileSelectState
        state.game.state_manager.add_state('PROFILE_SELECT', ProfileSelectState(state.game))
        state.game.state_manager.change_state('PROFILE_SELECT')

    def _go_to_editor(self):
        state = self.state
        state.click_cooldown = 0.3
        self.audio.play_sound("button_click")
        from ..map_editor_state import MapEditorState
        state.game.state_manager.add_state('MAP_EDITOR', MapEditorState(state.game))
        state.game.state_manager.change_state('MAP_EDITOR')

    def _exit_game(self):
        self.audio.play_sound("button_click")
        pygame.quit()
        sys.exit()