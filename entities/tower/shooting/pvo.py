# entities/tower/shooting/pvo.py
from typing import List, Optional
from entities.projectile import Projectile
from core.event_bus import EventBus


class PVOShooting:
    """ПВО — стреляет только по летающим"""
    
    def __init__(self, tower):
        self.tower = tower
    
    def shoot(self, enemies: List) -> Optional[Projectile]:
        tower = self.tower
        target = tower.target
        
        if not target:
            return None
        
        if not getattr(target, 'is_flying', False):
            return None
        
        damage = tower.damage
        if tower.upgrades.special_effect == 'crit_damage_x2':
            damage *= 2
        
        target.take_damage(damage, tower.damage_type)
        
        EventBus.emit('tower_shot', {
            'tower_id': tower.id,
            'target': target,
            'damage_type': tower.damage_type,
            'projectile': None,
            'tower_x': tower.x,
            'tower_y': tower.y,
            'tower_height': tower.height
        })
        
        return None