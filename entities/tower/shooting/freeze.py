# entities/tower/shooting/freeze.py
from typing import List, Optional
from entities.projectile import Projectile
from core.event_bus import EventBus


class FreezeShooting:
    """Замораживающая башня — замедляет врагов"""
    
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
        
        if hasattr(target, 'apply_freeze_effect'):
            target.apply_freeze_effect(tower.slow_duration)
        
        slow_mult = tower.slow_multiplier
        if hasattr(target, 'water_effect_active') and target.water_effect_active:
            slow_mult *= 0.6
        
        if hasattr(target, 'apply_slow'):
            target.apply_slow(slow_mult, tower.slow_duration)
        
        EventBus.emit('tower_shot', {
            'tower_id': tower.id,
            'target': target,
            'damage_type': 'freeze',
            'projectile': None,
            'tower_x': tower.x,
            'tower_y': tower.y,
            'tower_height': tower.height
        })
        
        return None