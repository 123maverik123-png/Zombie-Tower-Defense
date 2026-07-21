# systems/wave/manager.py
"""Менеджер волн - управляет процессом спавна"""

import random
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
from entities.enemy_factory import EnemyFactory
from core.event_bus import EventBus

if TYPE_CHECKING:
    from entities.enemy import Enemy


class WaveManager:
    """Управляет процессом спавна врагов по волнам"""
    
    def __init__(self, wave_data: List[Dict[str, Any]], path_points: List[Tuple[float, float]]):
        self.wave_data = wave_data
        self.path_points = path_points
        self.current_wave_index = 0
        self.current_wave: Optional[Dict[str, Any]] = None
        self.current_level = 1
        
        self.enemies_spawned = 0
        self.enemies_in_wave = 0
        self.enemies_killed_in_wave = 0
        self.spawn_timer = 0.0
        self.wave_active = False
        self.wave_complete = False
        self.all_waves_complete = False
        self.difficulty_multiplier = 1.0
        self.enemy_configs: Dict[str, Any] = {}
        
        self.total_hp_on_level = 0
        self.boss_spawned = False
        self.state = None
    
    def set_level(self, level: int):
        self.current_level = max(1, level)
    
    def set_state(self, state):
        self.state = state
    
    def calculate_total_hp(self, wave_data: List[Dict[str, Any]]) -> int:
        total_hp = 0
        for wave in wave_data:
            enemies = wave.get('enemies', {})
            for enemy_id, count in enemies.items():
                config = self.enemy_configs.get(enemy_id, {})
                base_hp = config.get('health', 100)
                if self.difficulty_multiplier > 1.0:
                    base_hp = int(base_hp * self.difficulty_multiplier)
                total_hp += base_hp * count
        self.total_hp_on_level = total_hp
        return total_hp
    
    def start_next_wave(self) -> bool:
        if self.current_wave_index >= len(self.wave_data):
            self.all_waves_complete = True
            self.wave_active = False
            self.wave_complete = True
            return False
        
        self.current_wave = self.wave_data[self.current_wave_index]
        self.enemies_spawned = 0
        self.enemies_killed_in_wave = 0
        self.enemies_in_wave = self.current_wave.get('total_enemies', 0)
        self.boss_spawned = False
        
        if self.enemies_in_wave <= 0:
            self.wave_active = False
            self.wave_complete = True
            self.current_wave_index += 1
            return self.start_next_wave()
        
        self.spawn_timer = 0.0
        self.wave_active = True
        self.wave_complete = False
        
        is_boss = self.current_wave.get('is_boss_wave', False)
        
        EventBus.emit('wave_started', {
            'wave_number': self.current_wave_index + 1,
            'total_waves': len(self.wave_data),
            'wave_data': self.current_wave,
            'is_boss': is_boss
        })
        
        return True
    
    def update(self, dt: float) -> Optional["Enemy"]:
        if self.wave_complete or self.all_waves_complete:
            return None
        
        if not self.wave_active:
            return None
        
        if self.enemies_spawned >= self.enemies_in_wave:
            return None
        
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            base_delay = self.current_wave.get('spawn_delay', 0.35)
            variation = self.current_wave.get('spawn_variation', 1.0)
            actual_delay = base_delay * variation
            actual_delay *= random.uniform(0.8, 1.2)
            actual_delay = max(0.1, actual_delay)
            
            self.spawn_timer = actual_delay
            self.enemies_spawned += 1
            
            enemy_config = self._get_enemy_config()
            enemy = self._create_enemy(enemy_config)
            
            is_boss = self.current_wave.get('is_boss_wave', False)
            
            EventBus.emit('enemy_spawned', {
                'enemy': enemy,
                'total_spawned': self.enemies_spawned,
                'total_in_wave': self.enemies_in_wave,
                'wave_number': self.current_wave_index + 1,
                'is_boss': is_boss
            })
            
            return enemy
        
        return None
    
    def on_enemy_killed(self):
        self.enemies_killed_in_wave += 1
        
        if self.enemies_killed_in_wave >= self.enemies_in_wave and self.enemies_spawned >= self.enemies_in_wave:
            self.wave_active = False
            self.wave_complete = True
            is_boss = self.current_wave.get('is_boss_wave', False) if self.current_wave else False
            
            EventBus.emit('wave_complete', {
                'wave_number': self.current_wave_index + 1,
                'total_waves': len(self.wave_data),
                'enemies_killed': self.enemies_killed_in_wave,
                'is_boss': is_boss
            })
    
    def _get_enemy_config(self) -> Dict[str, Any]:
        if not self.current_wave:
            return {}
        
        enemies_dict = self.current_wave.get('enemies', {})
        if not enemies_dict:
            return {'id': 'zombie_normal'}
        
        is_boss_wave = self.current_wave.get('is_boss_wave', False)
        
        if is_boss_wave and not self.boss_spawned:
            if 'zombie_boss' in enemies_dict and enemies_dict['zombie_boss'] > 0:
                self.boss_spawned = True
                selected_id = 'zombie_boss'
                base_config = self.enemy_configs.get(selected_id, {})

                from .config import WAVE_CONFIG
                boss_hp = WAVE_CONFIG['boss_base_hp'] + WAVE_CONFIG['boss_hp_per_level'] * self.current_level

                base_config = base_config.copy()
                base_config['health'] = boss_hp
                base_config['speed'] = base_config.get('speed', 45) * (0.9 + self.current_level * 0.002)
                base_config['reward_gold'] = int(base_config.get('reward_gold', 50) * (1 + self.current_level * 0.1))
                base_config['is_boss'] = True

                return {'id': selected_id, **base_config}
        
        enemy_list = []
        for enemy_id, count in enemies_dict.items():
            if is_boss_wave and enemy_id == 'zombie_boss' and self.boss_spawned:
                continue
            enemy_list.extend([enemy_id] * count)
        
        if not enemy_list:
            return {'id': 'zombie_normal'}
        
        selected_id = random.choice(enemy_list)
        base_config = self.enemy_configs.get(selected_id, {})
        
        return {'id': selected_id, **base_config}
    
    def _create_enemy(self, config: Dict[str, Any]) -> "Enemy":
        config = config.copy()

        # Рост HP по уровням: единственный источник сложности после капа
        # количества врагов (боссу HP уже задан в _get_enemy_config)
        if self.current_level > 1 and not config.get('is_boss', False):
            from .config import WAVE_CONFIG
            hp_scale = 1.0 + WAVE_CONFIG['hp_growth_per_level'] * (self.current_level - 1)
            config['health'] = int(config.get('health', 100) * hp_scale)
            # Награда растёт вдвое медленнее HP, чтобы экономика не взлетала
            gold_scale = 1.0 + WAVE_CONFIG['hp_growth_per_level'] * 0.5 * (self.current_level - 1)
            config['reward_gold'] = max(1, int(config.get('reward_gold', 5) * gold_scale))

        if self.difficulty_multiplier > 1.0:
            hp_multiplier = 1.0 + (self.difficulty_multiplier - 1.0) * 0.7
            config['health'] = int(config.get('health', 100) * hp_multiplier)
            speed_multiplier = 1.0 + (self.difficulty_multiplier - 1.0) * 0.05
            config['speed'] = config.get('speed', 90) * speed_multiplier
            config['reward_gold'] = int(config.get('reward_gold', 5) * (1 + (self.difficulty_multiplier - 1.0) * 0.3))

        return EnemyFactory.create(config, self.path_points, self.state)
    
    def set_difficulty(self, multiplier: float):
        self.difficulty_multiplier = max(1.0, multiplier)
    
    def get_wave_progress(self) -> float:
        if self.enemies_in_wave == 0:
            return 1.0
        return self.enemies_spawned / self.enemies_in_wave
    
    def get_wave_kill_progress(self) -> float:
        if self.enemies_in_wave == 0:
            return 1.0
        return self.enemies_killed_in_wave / self.enemies_in_wave
    
    def is_wave_active(self) -> bool:
        return self.wave_active
    
    def is_wave_complete(self) -> bool:
        return self.wave_complete
    
    def is_all_waves_complete(self) -> bool:
        return self.all_waves_complete
    
    def get_current_wave_number(self) -> int:
        return self.current_wave_index + 1
    
    def get_total_waves(self) -> int:
        return len(self.wave_data)
    
    def get_current_wave(self) -> Optional[Dict[str, Any]]:
        return self.current_wave
    
    def get_enemies_in_wave(self) -> int:
        return self.enemies_in_wave
    
    def get_enemies_killed_in_wave(self) -> int:
        return self.enemies_killed_in_wave
    
    def get_enemies_spawned_in_wave(self) -> int:
        return self.enemies_spawned
    
    def is_last_wave(self) -> bool:
        return self.current_wave_index >= len(self.wave_data) - 1