# entities/tower/targeting.py
from typing import Optional, List
from entities.base import Entity


def in_square_range(tower, entity) -> bool:
    """Квадратная зона поражения: цель внутри квадрата со стороной 2×range.

    Расстояние Чебышёва — совпадает с сеткой тайлов, поэтому радиус
    "6 клеток" означает ровно квадрат 13×13 клеток вокруг башни.
    """
    return (abs(entity.x - tower.x) <= tower.range
            and abs(entity.y - tower.y) <= tower.range)


class TowerTargeting:
    """Управление поиском цели для башни"""

    def __init__(self, tower):
        self.tower = tower

    def find_target(self, enemies: List[Entity], target_type: str = 'all') -> Optional[Entity]:
        tower = self.tower
        closest = None
        min_distance = float('inf')

        alive_enemies = [e for e in enemies if e.alive]
        if not alive_enemies:
            return None

        for enemy in alive_enemies:
            is_flying = getattr(enemy, 'is_flying', False)
            if target_type == 'ground' and is_flying:
                continue
            if target_type == 'flying' and not is_flying:
                continue

            if not in_square_range(tower, enemy):
                continue

            # Внутри квадрата приоритет — ближайшему (по Чебышёву)
            distance = max(abs(enemy.x - tower.x), abs(enemy.y - tower.y))
            if distance < min_distance:
                closest = enemy
                min_distance = distance

        return closest
