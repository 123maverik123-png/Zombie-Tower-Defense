# systems/wave/config.py
"""Конфигурация волн и врагов"""

# Пороги открытия врагов
ENEMY_UNLOCK_LEVELS = {
    'zombie_normal': 1,
    'zombie_fast': 3,
    'zombie_boss': 5,
    'zombie_tank': 7,
    'zombie_night': 11,
    'zombie_flying': 15,
}

# Базовые настройки волн
WAVE_CONFIG = {
    'base_enemies': ['zombie_normal'],
    'min_waves': 3,
    'max_waves': 12,
    'min_enemies_per_wave': 5,
    'max_enemies_per_wave': 70,
    'base_spawn_delay': 0.5,
    'min_spawn_delay': 0.3,
    'boss_wave_interval': 5,   # Каждый 5-й уровень
    'boss_spawn_delay': 1.5,

    # Рост здоровья врагов по уровням: HP × (1 + hp_growth_per_level × (level-1)).
    # После того как количество врагов упирается в max_enemies_per_wave,
    # сложность продолжает расти за счёт "толщины" врагов.
    'hp_growth_per_level': 0.05,

    # Босс: HP = boss_base_hp + boss_hp_per_level × level
    'boss_base_hp': 500,
    'boss_hp_per_level': 220,

    # Мягкий старт: интервал спавна на первых уровнях
    # {уровень: базовая задержка}
    'early_spawn_delays': {1: 1.0, 2: 0.9, 3: 0.8},
}

# Обучающий уровень 1: фиксированные маленькие волны
TUTORIAL_WAVES = [
    {'enemies': {'zombie_normal': 6}, 'spawn_delay': 1.0},
    {'enemies': {'zombie_normal': 8}, 'spawn_delay': 1.0},
    {'enemies': {'zombie_normal': 10}, 'spawn_delay': 0.9},
]

# Базовые волны (для простых уровней)
BASE_WAVES = [
    {"enemies": {"zombie_normal": 5}, "spawn_delay": 0.8},
    {"enemies": {"zombie_normal": 8, "zombie_fast": 2}, "spawn_delay": 0.7},
    {"enemies": {"zombie_normal": 10, "zombie_fast": 4}, "spawn_delay": 0.6},
    {"enemies": {"zombie_normal": 12, "zombie_tank": 2}, "spawn_delay": 0.5},
    {"enemies": {"zombie_normal": 15, "zombie_fast": 5, "zombie_tank": 3}, "spawn_delay": 0.4},
]


# --- Оверрайд баланса волн (dev-редактор) ---
# Файл data/configs/waves_override.json (если есть) накладывается поверх
# WAVE_CONFIG при загрузке. Так правки из редактора баланса сохраняются
# между запусками, а формулы в этом .py остаются нетронутыми.
WAVES_OVERRIDE_PATH = "data/configs/waves_override.json"


def _apply_waves_override():
    import json
    import os
    if not os.path.exists(WAVES_OVERRIDE_PATH):
        return
    try:
        with open(WAVES_OVERRIDE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return
    for key, value in data.items():
        if key in WAVE_CONFIG:
            WAVE_CONFIG[key] = value


_apply_waves_override()
