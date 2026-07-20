# entities/tower/shooting/instant.py
import random
from typing import List, Optional
from entities.projectile import Projectile
from core.event_bus import EventBus


class InstantShooting:
    """Мгновенный выстрел (снайпер, пулемёт)"""
    
    def __init__(self, tower):
        self.tower = tower
    
    def shoot(self, enemies: List) -> Optional[Projectile]:
        tower = self.tower
        target = tower.target
        
        if not target or not target.alive:
            return None
        
        damage = tower.damage
        
        if tower.upgrades.special_effect == 'crit_damage_x2':
            damage *= 2
        
        if tower.upgrades.special_effect == 'double_shot_chance_15' and random.random() < 0.15:
            damage *= 2
        
        target.take_damage(damage, tower.damage_type)
        
        EventBus.emit('tower_shot', {
            'tower_id': tower.id,
            'target': target,
            'damage_type': tower.damage_type,
            'projectile': None,
            'tower_x': tower.x,
            'tower_y': tower.y
        })
        
        return None