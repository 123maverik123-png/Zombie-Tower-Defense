# entities/tower/shooting/water.py
import math
from typing import List, Optional
from entities.projectile import Projectile
from core.event_bus import EventBus


class WaterShooting:
    """Водяная башня — струя как у огнемёта: AOE-зона, урон 0, мокрый эффект.

    Накладывает эффект 'Вода' всем врагам в радиусе струи (тушит огонь,
    даёт бонус-множитель к урону других башен). Урона не наносит.
    """

    def __init__(self, tower):
        self.tower = tower

    def shoot(self, enemies: List) -> Optional[Projectile]:
        tower = self.tower
        target = tower.target

        if not target:
            return None

        aoe_radius = tower.aoe_radius

        for enemy in enemies:
            if not enemy.alive:
                continue
            dist = math.hypot(enemy.x - target.x, enemy.y - target.y)
            if dist <= aoe_radius:
                if hasattr(enemy, 'apply_water_effect'):
                    enemy.apply_water_effect(tower.effect_duration)

        EventBus.emit('tower_shot', {
            'tower_id': tower.id,
            'target': target,
            'damage_type': 'water',
            'projectile': None,
            'tower_x': tower.x,
            'tower_y': tower.y
        })

        return None
