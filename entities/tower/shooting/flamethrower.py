# entities/tower/shooting/flamethrower.py
import math
from typing import List, Optional
from entities.projectile import Projectile
from entities.decals import Decal
from core.event_bus import EventBus
from core.audio import AudioManager


class FlamethrowerShooting:
    """Огнемёт — AOE урон + эффект огня"""
    
    def __init__(self, tower):
        self.tower = tower
    
    def shoot(self, enemies: List) -> Optional[Projectile]:
        tower = self.tower
        target = tower.target
        
        if not target:
            return None
        
        aoe_radius = tower.aoe_radius
        damage = tower.damage
        
        if tower.upgrades.special_effect == 'crit_damage_x2':
            damage *= 2
        
        for enemy in enemies:
            if not enemy.alive:
                continue
            dist = math.hypot(enemy.x - target.x, enemy.y - target.y)
            if dist <= aoe_radius:
                enemy.take_damage(damage, tower.damage_type)
                
                if hasattr(enemy, 'apply_fire_effect'):
                    enemy.apply_fire_effect(tower.fire_dot_duration,
                                            tower.fire_dot_damage,
                                            tower.fire_dot_interval)
                
                # ✅ ЗАКОММЕНТИРОВАН ЭФФЕКТ ОГНЯ НА ДОРОГЕ
                # decal = Decal(enemy.x, enemy.y, 'fire', scale=0.4)
                # if hasattr(tower, 'state') and tower.state:
                #     tower.state.decals.append(decal)
        
        EventBus.emit('tower_shot', {
            'tower_id': tower.id,
            'target': target,
            'damage_type': tower.damage_type,
            'projectile': None,
            'tower_x': tower.x,
            'tower_y': tower.y
        })
        
        return None