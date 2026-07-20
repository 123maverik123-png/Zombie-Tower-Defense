# entities/tower/shooting/acid.py
from typing import List, Optional
from entities.projectile import Projectile
from core.event_bus import EventBus


class AcidShooting:
    """Кислотная башня — DoT урон"""
    
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
        
        if hasattr(target, 'apply_acid_effect'):
            target.apply_acid_effect(tower.acid_damage, tower.acid_interval, tower.acid_duration)
        
        EventBus.emit('tower_shot', {
            'tower_id': tower.id,
            'target': target,
            'damage_type': 'acid',
            'projectile': None,
            'tower_x': tower.x,
            'tower_y': tower.y
        })
        
        return None