# entities/player.py
from typing import Dict, List, Optional

class Player:
    """Игрок — хранит прогресс, инвентарь и характеристики"""
    def __init__(self, name="Player"):
        self.name = name
        self.gold = 100
        self.lives = 20
        self.current_level = 1
        self.experience = 0
        self.level = 1

        # Инвентарь
        self.inventory: Dict[str, int] = {
            "basic_tower": 3,
            "sniper_tower": 0,
            "cannon_tower": 0
        }

        # Разблокированные башни
        self.unlocked_towers: List[str] = ["basic_tower"]

        # Статистика
        self.stats = {
            "total_kills": 0,
            "total_gold_earned": 0,
            "waves_survived": 0
        }

        # Характеристики
        self.characteristics = {
            "attack_speed_multiplier": 1.0,
            "damage_multiplier": 1.0,
            "gold_multiplier": 1.0
        }

    def add_gold(self, amount: int):
        """Добавить золото с учётом множителя"""
        actual_amount = int(amount * self.characteristics["gold_multiplier"])
        self.gold += actual_amount
        self.stats["total_gold_earned"] += actual_amount

    def spend_gold(self, amount: int) -> bool:
        """Потратить золото, если достаточно"""
        if self.gold >= amount:
            self.gold -= amount
            return True
        return False

    def add_tower_to_inventory(self, tower_id: str, count: int = 1):
        """Добавить башню в инвентарь"""
        if tower_id in self.inventory:
            self.inventory[tower_id] += count
        else:
            self.inventory[tower_id] = count

    def use_tower(self, tower_id: str) -> bool:
        """Использовать башню из инвентаря"""
        if self.inventory.get(tower_id, 0) > 0:
            self.inventory[tower_id] -= 1
            return True
        return False

    def add_experience(self, amount: int):
        """Добавить опыт и повысить уровень"""
        self.experience += amount
        while self.experience >= 100 * self.level:
            self.experience -= 100 * self.level
            self.level += 1
            self._on_level_up()

    def _on_level_up(self):
        """Награда за уровень"""
        self.gold += 50
        self.characteristics["damage_multiplier"] += 0.05

    def to_dict(self) -> dict:
        """Сериализация для сохранения"""
        return {
            "name": self.name,
            "gold": self.gold,
            "lives": self.lives,
            "current_level": self.current_level,
            "level": self.level,
            "experience": self.experience,
            "inventory": self.inventory,
            "unlocked_towers": self.unlocked_towers,
            "stats": self.stats,
            "characteristics": self.characteristics
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Player':
        """Десериализация из JSON"""
        player = cls(data.get("name", "Player"))
        player.gold = data.get("gold", 100)
        player.lives = data.get("lives", 20)
        player.current_level = data.get("current_level", 1)
        player.level = data.get("level", 1)
        player.experience = data.get("experience", 0)
        player.inventory = data.get("inventory", {})
        player.unlocked_towers = data.get("unlocked_towers", ["basic_tower"])
        player.stats = data.get("stats", {})
        player.characteristics = data.get("characteristics", {})
        return player