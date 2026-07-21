# core/balance_editor/model.py
"""Слой доступа к данным баланса: чтение и запись JSON-конфигов.

Правки пишутся прямо в data/configs/*.json. Новые сущности читают
конфиг с диска при создании, поэтому изменения применяются сразу.
"""
import json
import os
import shutil

TOWERS_PATH = "data/configs/towers.json"
ENEMIES_PATH = "data/configs/enemies.json"
WAVES_OVERRIDE_PATH = "data/configs/waves_override.json"

# Числовые поля WAVE_CONFIG, которые имеет смысл крутить в редакторе
# (dict/list-поля вроде base_enemies/early_spawn_delays не трогаем).
WAVE_FIELDS = [
    "min_waves", "max_waves",
    "min_enemies_per_wave", "max_enemies_per_wave",
    "base_spawn_delay", "min_spawn_delay",
    "boss_wave_interval", "boss_spawn_delay",
    "hp_growth_per_level",
    "boss_base_hp", "boss_hp_per_level",
]

# Поля башен верхнего уровня, которые имеет смысл крутить (числовые).
TOWER_FIELDS = [
    "cost", "damage", "fire_rate", "range_cells", "upgrade_cost",
    "aoe_radius_cells", "projectile_speed",
    "fire_dot_damage", "fire_dot_interval", "fire_dot_duration",
    "acid_damage", "acid_interval", "acid_duration",
]

# Поля врагов, которые имеет смысл крутить.
ENEMY_FIELDS = [
    "health", "speed", "reward_gold", "reward_exp", "base_damage",
    "slow_resistance",
]

# Спецификация ползунка для каждого поля: (min, max, step, is_int).
# Шаг у каждого пункта свой. Диапазоны щедрые — можно потом подвинуть.
FIELD_SPEC = {
    # --- Башни ---
    "cost":              (0, 500, 5, True),
    "damage":            (0, 300, 0.5, False),
    "fire_rate":         (0.05, 3.0, 0.05, False),
    "range_cells":       (1, 12, 0.5, False),
    "upgrade_cost":      (0, 800, 10, True),
    "aoe_radius_cells":  (0, 6, 0.1, False),
    "projectile_speed":  (50, 600, 10, True),
    "fire_dot_damage":   (0, 40, 0.5, False),
    "fire_dot_interval": (0.1, 2.0, 0.1, False),
    "fire_dot_duration": (0.5, 12, 0.5, False),
    "acid_damage":       (0, 50, 0.5, False),
    "acid_interval":     (0.1, 2.0, 0.1, False),
    "acid_duration":     (0.5, 15, 0.5, False),
    # --- Враги ---
    "health":            (0, 3000, 10, True),
    "speed":             (0, 400, 5, True),
    "reward_gold":       (0, 300, 1, True),
    "reward_exp":        (0, 150, 1, True),
    "base_damage":       (0, 30, 1, True),
    "slow_resistance":   (0, 1, 0.05, False),
    # --- Волны ---
    "min_waves":              (1, 20, 1, True),
    "max_waves":              (1, 30, 1, True),
    "min_enemies_per_wave":   (1, 50, 1, True),
    "max_enemies_per_wave":   (5, 300, 5, True),
    "base_spawn_delay":       (0.1, 2.0, 0.05, False),
    "min_spawn_delay":        (0.05, 1.5, 0.05, False),
    "boss_wave_interval":     (1, 15, 1, True),
    "boss_spawn_delay":       (0.2, 4.0, 0.1, False),
    "hp_growth_per_level":    (0.0, 0.5, 0.01, False),
    "boss_base_hp":           (100, 5000, 50, True),
    "boss_hp_per_level":      (0, 1000, 10, True),
}


def snap(value, field):
    """Приводит значение к шагу поля и его типу (int/float)."""
    spec = FIELD_SPEC.get(field)
    if not spec:
        return value
    lo, hi, step, is_int = spec
    value = max(lo, min(hi, value))
    snapped = round(value / step) * step
    if is_int:
        return int(round(snapped))
    return round(snapped, 4)



class BalanceModel:
    """Загрузка/сохранение конфигов баланса с бэкапом оригиналов."""

    def __init__(self):
        self.towers = {}
        self.enemies = {}
        self.error = ""
        self.reload()

    # --- Загрузка ---

    def reload(self):
        """Перечитывает конфиги с диска (отбрасывает несохранённое)."""
        self.error = ""
        self.towers = self._load(TOWERS_PATH)
        self.enemies = self._load(ENEMIES_PATH)

    def _load(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.error = f"load {path}: {e}"
            return {}

    # --- Бэкап ---

    def ensure_backup(self):
        """Создаёт *.json.bak один раз, чтобы можно было откатить правки."""
        for path in (TOWERS_PATH, ENEMIES_PATH):
            bak = path + ".bak"
            if not os.path.exists(bak) and os.path.exists(path):
                try:
                    shutil.copyfile(path, bak)
                except Exception as e:
                    self.error = f"backup {path}: {e}"

    # --- Доступ к значениям ---

    def tower_ids(self):
        return list(self.towers.keys())

    def enemy_ids(self):
        return list(self.enemies.keys())

    def get_tower_value(self, tower_id, field):
        return self.towers.get(tower_id, {}).get(field)

    def get_enemy_value(self, enemy_id, field):
        return self.enemies.get(enemy_id, {}).get(field)

    def get_wave_value(self, field):
        """Читает значение прямо из живого WAVE_CONFIG."""
        from systems.wave.config import WAVE_CONFIG
        return WAVE_CONFIG.get(field)

    def set_tower_value(self, tower_id, field, value):
        if tower_id in self.towers:
            self.towers[tower_id][field] = value
            self._save(TOWERS_PATH, self.towers)

    def set_enemy_value(self, enemy_id, field, value):
        if enemy_id in self.enemies:
            self.enemies[enemy_id][field] = value
            self._save(ENEMIES_PATH, self.enemies)

    def set_wave_value(self, field, value):
        """Мутирует живой WAVE_CONFIG (сразу видно следующей генерации волн)
        и пишет оверрайд-файл для персистентности между запусками."""
        from systems.wave.config import WAVE_CONFIG
        WAVE_CONFIG[field] = value
        self._save_waves_override()

    def _save_waves_override(self):
        """Сохраняет только редактируемые числовые поля WAVE_CONFIG в оверрайд."""
        from systems.wave.config import WAVE_CONFIG
        data = {f: WAVE_CONFIG[f] for f in WAVE_FIELDS if f in WAVE_CONFIG}
        try:
            with open(WAVES_OVERRIDE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.error = f"save {WAVES_OVERRIDE_PATH}: {e}"

    # --- Сохранение ---

    def _save(self, path, data):
        self.ensure_backup()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.error = f"save {path}: {e}"
