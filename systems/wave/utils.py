# systems/wave/utils.py
"""Вспомогательные функции для работы с волнами"""

import random
from typing import List, Dict, Any


def get_available_enemies(level_number: int) -> List[str]:
    """
    Возвращает список доступных врагов для уровня.
    Использует ENEMY_UNLOCK_LEVELS из config.
    """
    from .config import ENEMY_UNLOCK_LEVELS
    
    available = []
    for enemy_id, unlock_level in ENEMY_UNLOCK_LEVELS.items():
        if level_number >= unlock_level:
            available.append(enemy_id)
    return available


def get_enemy_types_for_wave(level_number: int, max_types: int = 3) -> List[str]:
    """
    Выбирает типы врагов для волны.
    Чем выше уровень, тем больше типов.
    """
    available = get_available_enemies(level_number)
    # Исключаем босса из обычных волн
    normal_enemies = [e for e in available if e != 'zombie_boss']
    
    if not normal_enemies:
        return ['zombie_normal']
    
    # Количество типов зависит от уровня
    num_types = min(len(normal_enemies), 1 + (level_number // 3))
    num_types = min(num_types, max_types)
    
    return random.sample(normal_enemies, num_types)


def distribute_enemy_count(total_count: int, enemy_types: List[str]) -> Dict[str, int]:
    """
    Распределяет общее количество врагов по типам.
    """
    if not enemy_types:
        return {'zombie_normal': total_count}
    
    result = {}
    remaining = total_count
    
    for enemy_type in enemy_types[:-1]:
        # Первые типы получают случайное количество
        max_for_type = remaining // (len(enemy_types) - 1)
        count = random.randint(max(1, max_for_type // 2), max_for_type)
        result[enemy_type] = count
        remaining -= count
    
    # Последний тип получает остаток
    result[enemy_types[-1]] = max(1, remaining)
    
    return result


def calculate_wave_count(level_number: int, wave_index: int) -> int:
    """
    Рассчитывает количество врагов в волне.
    Рост мягче старой формулы (×2 от суммы): в начале волны меньше,
    кап 60 достигается к ~25 уровню, дальше растёт HP врагов.
    """
    from .config import WAVE_CONFIG

    base_count = WAVE_CONFIG['min_enemies_per_wave'] + wave_index * 2 + int(level_number * 1.5)
    return min(base_count, WAVE_CONFIG['max_enemies_per_wave'])


def calculate_spawn_delay(level_number: int, wave_index: int, is_boss: bool = False) -> float:
    """
    Рассчитывает задержку спавна в волне.
    Первые уровни — замедленный темп (см. early_spawn_delays).
    """
    from .config import WAVE_CONFIG

    if is_boss:
        return WAVE_CONFIG['boss_spawn_delay']

    base_delay = WAVE_CONFIG['early_spawn_delays'].get(
        level_number, WAVE_CONFIG['base_spawn_delay'])
    base_delay -= wave_index * 0.03
    return max(WAVE_CONFIG['min_spawn_delay'], base_delay)