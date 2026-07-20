# core/states/play/state.py
import pygame
from typing import List
from core.state_manager import State
from core.event_bus import EventBus
from core.audio import AudioManager
from core.level_loader import build_level

from .init import PlayStateInitializer
from .config import PlayStateConfig
from .game_events import PlayStateGameEvents
from .sound_control import PlayStateSoundControl


class PlayState(State):
    """Основное игровое состояние"""
    
    def __init__(self, game, level_number=1, level_data=None):
        super().__init__(game)

        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True

        self.audio = AudioManager()
        self._cleanup_old_entities()

        self.level_number = level_number
        self.total_kills = 0
        self._music_started = False
        self._is_saving = False
        
        self._init_components(game)
        
        self._init = PlayStateInitializer(self)
        self._init.initialize(game, level_number, level_data)
        
        self._game_events = PlayStateGameEvents(self)
        self._sound_control = PlayStateSoundControl(self)
        self._config = PlayStateConfig(self)

    def _init_components(self, game):
        self.level_data = None
        self.map_data = None
        self.wave_data = None
        self.screen_width = game.render_width
        self.screen_height = game.render_height
        
        self.tile_manager = None
        self.path = []          # мировые координаты
        self._raw_path = []     # мировые координаты (резерв)
        
        self.enemies = []
        self.towers = []
        self.projectiles = []
        self.lightning_effects = []
        self.hit_effects = []
        self.decals = []
        self.walls = []
        self.gates = []
        
        self.player = None
        self.selected_tower = 'sniper'
        self.building_mode = False
        self.wall_placement_mode = False
        self.selected_wall_type = 'gate'
        self.mouse_pos = (0, 0)
        self.wave_delay = 0.0
        self.game_speed = 1.0
        self.god_mode = False
        self.frozen = False
        self.level_complete = False
        self.game_over = False
        
        self.build_error = False
        self.build_error_pos = (0, 0)
        self.build_error_timer = 0.0
        self.build_error_msg = ""
        self.build_success = False
        self.build_success_pos = (0, 0)
        self.build_success_timer = 0.0
        
        self.camera_dragging = False
        self.camera_drag_start = (0, 0)
        
        self.enemy_configs = None
        self.wave_manager = None
        
        self.console = None
        self.tower_ui = None
        
        self.font = None
        self.small_font = None
        self.big_font = None
        
        self.input_events = None
        self.bus_events = None
        self.event_handlers = None
        
        self.update_logic = None
        self.draw_logic = None
        self.towers_logic = None
        self.enemies_logic = None
        self.ui_logic = None
        self.decals_logic = None
        self.effects_logic = None
        self.feedback_logic = None
        
        self._ui_surface = None
        self._initialized = True

    def _cleanup_old_entities(self):
        EventBus.clear()
        from utils.sprite_loader import SpriteLoader
        loader = SpriteLoader()
        loader.cache.clear()
        
        if hasattr(self, 'audio'):
            self.audio.flame_reset()
        
        if hasattr(self, 'game') and getattr(self.game, 'renderer', None):
            try:
                self.game.renderer.clear_textures()
            except Exception as e:
                print(f"⚠️ Failed to clear textures: {e}")
        
        self._ui_surface = None
        print("🧹 Cleaned up old entities and cache")

    def _setup_events(self):
        self.bus_events.setup()

    def handle_events(self, events):
        self.input_events.handle(events)

    def update(self, dt):
        self.update_logic.update(dt)

    def draw(self, screen):
        self.draw_logic.draw(screen)

    def draw_scene(self, renderer):
        self.draw_logic.draw_scene(renderer)

    def _get_tower_config(self, tower_type, level=1):
        return self._config.get_tower_config(tower_type, level)

    def _check_game_over(self):
        self._game_events.check_game_over()

    def _check_victory(self):
        self._game_events.check_victory()

    def _check_music(self):
        self._game_events.check_music()

    def reset_all_tower_sounds(self):
        self._sound_control.reset_all_tower_sounds()

    def stop_all_sfx(self):
        self._sound_control.stop_all_sfx()

    def on_resolution_changed(self, screen_w, screen_h):
        """Обновляет разрешение экрана. Путь не меняется (он в мировых координатах)."""
        self.screen_width = screen_w
        self.screen_height = screen_h
        
        if self.tile_manager:
            self.tile_manager.on_resolution_changed(screen_w, screen_h)
            # Путь остаётся в мировых координатах, не пересчитываем
            new_path = self.tile_manager.get_path_from_map()
            if new_path:
                self.path = new_path
                self._raw_path = new_path
                if self.wave_manager:
                    self.wave_manager.path_points = new_path
        
        print(f"🔄 Resolution changed to {screen_w}x{screen_h}")