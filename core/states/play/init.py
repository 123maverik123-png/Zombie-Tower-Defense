# core/states/play/init.py
import pygame
from core.tile_manager import TileManager
from core.console import DevConsole
from ui.tower_ui import TowerUI
from entities.player import Player
from entities.enemy_factory import EnemyFactory
from systems.wave import WaveManager
from core.event_bus import EventBus
from core.audio import AudioManager
from core.level_loader import build_level

from .events import InputEvents, BusEvents, EventHandlers
from .update import PlayUpdate
from .draw import PlayDraw
from .towers import PlayTowers
from .enemies import PlayEnemies
from .ui import PlayUI
from .decals import PlayDecals
from .effects import PlayEffects
from .feedback import PlayFeedback


class PlayStateInitializer:
    """Инициализация игрового состояния"""
    
    def __init__(self, state):
        self.state = state
    
    def initialize(self, game, level_number, level_data):
        """Инициализирует все компоненты PlayState"""
        state = self.state
        
        if level_data is None:
            level_data = build_level(level_number)
        
        state.level_data = level_data
        state.map_data = level_data['map']
        state.wave_data = level_data.get('waves', [])
        
        state.screen_width = game.render_width
        state.screen_height = game.render_height
        
        # Карта (биом зависит от номера уровня: лес → пустыня → город)
        from core.graphics_theme import biome_for_level
        state.biome = biome_for_level(level_number)
        state.tile_manager = TileManager(state.screen_width, state.screen_height,
                                         bottom_offset=100, biome=state.biome)
        state.tile_manager.set_map(state.map_data)

        # Декорации: ручные из level_data + авторазброс по сиду уровня
        from core.decorations import DecorationLayer
        state.decoration_layer = DecorationLayer(
            state.biome, level_number,
            state.map_data, state.tile_manager.tile_size,
            manual=level_data.get('decorations'),
        )

        # Факелы вдоль дороги (атмосфера тёмного фэнтези)
        from core.torches import TorchLayer
        state.torch_layer = TorchLayer(level_number, state.map_data,
                                       state.tile_manager.tile_size)

        # ✅ Путь в МИРОВЫХ координатах (без смещения камеры)
        state.path = state.tile_manager.get_path_from_map()
        state._raw_path = state.path  # для сохранения
        
        if not state.path:
            state.path = level_data.get('path', [])
        
        # Сущности
        state.enemies = []
        state.towers = []
        state.projectiles = []
        state.lightning_effects = []
        state.hit_effects = []
        state.decals = []
        state.walls = []
        state.gates = []
        
        # Игрок
        state.player = Player()
        state.player.gold = 300
        # Обучающий уровень — больше права на ошибку
        state.player.lives = 10 if level_number == 1 else 5
        state.is_tutorial = (level_number == 1)
        
        # Состояния
        state.selected_tower = 'sniper'
        state.building_mode = False
        state.wall_placement_mode = False
        state.selected_wall_type = 'gate'
        state.mouse_pos = (0, 0)
        state.wave_delay = 0.0
        state.game_speed = 1.0
        state.god_mode = False
        state.frozen = False
        
        state.level_complete = False
        state.game_over = False
        
        # Обратная связь
        state.build_error = False
        state.build_error_pos = (0, 0)
        state.build_error_timer = 0.0
        state.build_error_msg = ""
        state.build_success = False
        state.build_success_pos = (0, 0)
        state.build_success_timer = 0.0
        
        # Камера
        state.camera_dragging = False
        state.camera_drag_start = (0, 0)
        
        # Конфиги
        state.enemy_configs = EnemyFactory.load_enemy_configs()
        
        # Менеджер волн — путь в мировых координатах
        state.wave_manager = WaveManager(state.wave_data, state.path)
        state.wave_manager.enemy_configs = state.enemy_configs
        state.wave_manager.set_level(level_number)
        state.wave_manager.set_state(state)
        state.wave_manager.calculate_total_hp(state.wave_data)
        state.wave_manager.start_next_wave()
        
        # Аудио (музыка)
        if state.audio.settings.music_enabled:
            state.audio.play_music("game_theme.wav")
        
        # Консоль
        state.console = DevConsole(game)
        
        # UI
        state.tower_ui = TowerUI()
        
        # Шрифты
        state.font = pygame.font.Font(None, 30)
        state.small_font = pygame.font.Font(None, 24)
        state.big_font = pygame.font.Font(None, 48)
        
        # Модули
        state.input_events = InputEvents(state)
        state.bus_events = BusEvents(state)
        state.event_handlers = EventHandlers(state)
        
        state.update_logic = PlayUpdate(state)
        state.draw_logic = PlayDraw(state)
        state.towers_logic = PlayTowers(state)
        state.enemies_logic = PlayEnemies(state)
        state.ui_logic = PlayUI(state)
        state.decals_logic = PlayDecals(state)
        state.effects_logic = PlayEffects(state)
        state.feedback_logic = PlayFeedback(state)
        
        state._setup_events()

        # Подсказки обучения (активны только на уровне 1);
        # создаётся после _setup_events, т.к. подписывается на EventBus
        from .tutorial import TutorialHints
        state.tutorial = TutorialHints(state)

        state._ui_surface = None

        print(f"✅ PlayState initialized with {len(state.path)} path points (world coordinates)")