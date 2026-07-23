# entities/tower/shooting/projectile.py
import random
from typing import List, Optional
from entities.projectile import Projectile
from core.event_bus import EventBus


class ProjectileShooting:
    """Обычный выстрел со снарядом"""
    
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
        
        if tower.upgrades.special_effect == 'double_shot_chance_15' and random.random() < 0.15:
            damage *= 2
        
        config = tower.config.copy()
        config['projectile_type'] = tower.id
        config['id'] = tower.id
        
        projectile = Projectile(
            start_pos=tower.get_center(),
            target=target,
            speed=tower.projectile_speed,
            damage=damage,
            damage_type=tower.damage_type,
            config=config
        )
        projectile.aoe_radius = tower.aoe_radius
        
        if tower.slow_duration > 0:
            projectile.slow_duration = tower.slow_duration
            projectile.slow_multiplier = tower.slow_multiplier
        
        EventBus.emit('tower_shot', {
            'tower_id': tower.id,
            'target': target,
            'damage_type': tower.damage_type,
            'projectile': projectile,
            'tower_x': tower.x,
            'tower_y': tower.y,
            'tower_height': tower.height
        })
        
        return projectile