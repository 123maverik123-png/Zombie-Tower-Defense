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

    def set_tower_value(self, tower_id, field, value):
        if tower_id in self.towers:
            self.towers[tower_id][field] = value
            self._save(TOWERS_PATH, self.towers)

    def set_enemy_value(self, enemy_id, field, value):
        if enemy_id in self.enemies:
            self.enemies[enemy_id][field] = value
            self._save(ENEMIES_PATH, self.enemies)

    # --- Сохранение ---

    def _save(self, path, data):
        self.ensure_backup()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.error = f"save {path}: {e}"
