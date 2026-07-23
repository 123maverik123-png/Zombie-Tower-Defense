# entities/tower/shooting/rocket.py
import math
from typing import List, Optional
from entities.projectile import Projectile
from core.event_bus import EventBus


class RocketShooting:
    """Ракетная башня — AOE урон"""
    
    def __init__(self, tower):
        self.tower = tower
    
    def shoot(self, enemies: List) -> Optional[Projectile]:
        tower = self.tower
        target = tower.target
        
        if not target:
            return None
        
        damage = tower.damage
        if tower.upgrades.special_effect == 'crit_damage_x2':
            damage *= 2
        
        target.take_damage(damage, tower.damage_type)
        
        aoe_radius = tower.aoe_radius
        for enemy in enemies:
            if enemy == target or not enemy.alive:
                continue
            dist = math.hypot(enemy.x - target.x, enemy.y - target.y)
            if dist <= aoe_radius:
                aoe_damage = damage * 0.5
                enemy.take_damage(aoe_damage, tower.damage_type)
        
        EventBus.emit('tower_shot', {
            'tower_id': tower.id,
            'target': target,
            'damage_type': 'explosive',
            'projectile': None,
            'tower_x': tower.x,
            'tower_y': tower.y,
            'tower_height': tower.height
        })
        
        EventBus.emit('aoe_damage_request', {
            'center': (target.x, target.y),
            'radius': aoe_radius,
            'damage': damage * 0.5,
            'damage_type': 'explosive'
        })
        
        return None