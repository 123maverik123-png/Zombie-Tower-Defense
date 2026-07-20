# systems/wave/factory.py
"""Фабрика для создания волн"""

import random
from typing import List, Dict, Any
from .config import BASE_WAVES
from .utils import (
    get_available_enemies, 
    get_enemy_types_for_wave,
    distribute_enemy_count,
    calculate_wave_count,
    calculate_spawn_delay
)


class WaveFactory:
    """Фабрика для создания волн"""
    
    @classmethod
    def create_wave(cls, level_number: int, wave_index: int, is_boss: bool = False) -> Dict[str, Any]:
        """
        Создает одну волну.
        """
        # Определяем врагов
        if is_boss:
            enemies = cls._create_boss_wave_enemies(level_number)
        else:
            enemies = cls._create_normal_wave_enemies(level_number, wave_index)
        
        total_enemies = sum(enemies.values())
        spawn_delay = calculate_spawn_delay(level_number, wave_index, is_boss)
        
        return {
            'enemies': enemies,
            'total_enemies': total_enemies,
            'spawn_delay': spawn_delay,
            'is_boss_wave': is_boss,
            'wave_number': wave_index + 1
        }
    
    @classmethod
    def _create_normal_wave_enemies(cls, level_number: int, wave_index: int) -> Dict[str, int]:
        """Создает врагов для обычной волны"""
        enemy_types = get_enemy_types_for_wave(level_number)
        total_count = calculate_wave_count(level_number, wave_index)
        
        # Для низких уровней - простой состав
        if level_number <= 3:
            return {'zombie_normal': total_count}
        
        # Для средних уровней - смешанный состав
        return distribute_enemy_count(total_count, enemy_types)
    
    @classmethod
    def _create_boss_wave_enemies(cls, level_number: int) -> Dict[str, int]:
        """Создает врагов для босс-волны"""
        enemies = {'zombie_boss': 1}
        
        # Добавляем свиту
        available = get_available_enemies(level_number)
        normal_enemies = [e for e in available if e != 'zombie_boss']
        
        if normal_enemies:
            escort_count = 2 + (level_number - 5) // 2
            escort_count = min(escort_count, 8)
            
            # Выбираем 1-2 типа для свиты
            num_types = min(len(normal_enemies), 2)
            escort_types = random.sample(normal_enemies, num_types) if normal_enemies else ['zombie_normal']
            
            for enemy_type in escort_types:
                count = max(1, escort_count // len(escort_types))
                enemies[enemy_type] = count
        
        return enemies
    
    @classmethod
    def generate_waves(cls, level_number: int) -> List[Dict[str, Any]]:
        """
        Генерирует все волны для уровня.
        Уровень 1 — обучающий: фиксированные маленькие волны.
        """
        from .config import WAVE_CONFIG, TUTORIAL_WAVES

        if level_number == 1:
            waves = []
            for i, tw in enumerate(TUTORIAL_WAVES):
                waves.append({
                    'enemies': dict(tw['enemies']),
                    'total_enemies': sum(tw['enemies'].values()),
                    'spawn_delay': tw['spawn_delay'],
                    'is_boss_wave': False,
                    'wave_number': i + 1,
                })
            return waves

        # Количество волн
        num_waves = WAVE_CONFIG['min_waves'] + (level_number // 3)
        num_waves = min(num_waves, WAVE_CONFIG['max_waves'])
        
        waves = []
        
        # Обычные волны
        for i in range(num_waves - 1):
            wave = cls.create_wave(level_number, i, is_boss=False)
            waves.append(wave)
        
        # Босс-волна (каждый 5-й уровень)
        if level_number % WAVE_CONFIG['boss_wave_interval'] == 0 and level_number >= 5:
            boss_wave = cls.create_wave(level_number, num_waves - 1, is_boss=True)
            waves.append(boss_wave)
        else:
            # Усиленная волна вместо босса
            wave = cls.create_wave(level_number, num_waves - 1, is_boss=False)
            waves.append(wave)
        
        # Нумеруем волны
        for i, wave in enumerate(waves):
            wave['wave_number'] = i + 1
        
        return waves