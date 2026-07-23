# entities/tower/shooting/electric.py
import math
from typing import List, Optional
from entities.projectile import Projectile
from core.event_bus import EventBus


class ElectricShooting:
    """Электрическая башня — цепной урон"""
    
    def __init__(self, tower):
        self.tower = tower
    
    def shoot(self, enemies: List) -> Optional[Projectile]:
        tower = self.tower
        target = tower.target
        
        if not target:
            return None
        
        damage = tower.damage
        if hasattr(target, 'water_effect_active') and target.water_effect_active:
            damage *= tower.bonus_multiplier
        
        chain_count = tower.chain_count
        hit_enemies = [target]
        
        target.take_damage(damage, tower.damage_type)
        
        if not getattr(target, 'is_flying', False):
            if hasattr(target, 'apply_electric_effect'):
                target.apply_electric_effect(0.5)
            if tower.slow_duration > 0 and hasattr(target, 'apply_slow'):
                target.apply_slow(0.5, tower.slow_duration)
        
        EventBus.emit('lightning_effect', {
            'from': tower.get_center(),
            'to': target.get_center(),
            'damage': damage
        })
        
        EventBus.emit('tower_shot', {
            'tower_id': tower.id,
            'target': target,
            'damage_type': tower.damage_type,
            'projectile': None,
            'tower_x': tower.x,
            'tower_y': tower.y,
            'tower_height': tower.height
        })
        
        for _ in range(chain_count - 1):
            last_enemy = hit_enemies[-1]
            
            nearest = None
            min_dist = float('inf')
            
            for enemy in enemies:
                if not enemy.alive:
                    continue
                if enemy in hit_enemies:
                    continue
                
                dist = math.hypot(enemy.x - last_enemy.x, enemy.y - last_enemy.y)
                if dist < 250 and dist < min_dist:
                    nearest = enemy
                    min_dist = dist
            
            if nearest:
                hit_enemies.append(nearest)
                nearest_damage = damage * 0.7
                nearest.take_damage(nearest_damage, tower.damage_type)
                
                if not getattr(nearest, 'is_flying', False):
                    if hasattr(nearest, 'apply_electric_effect'):
                        nearest.apply_electric_effect(0.5)
                    if tower.slow_duration > 0 and hasattr(nearest, 'apply_slow'):
                        nearest.apply_slow(0.5, tower.slow_duration)
                
                EventBus.emit('chain_lightning_effect', {
                    'from': last_enemy,
                    'to': nearest,
                    'damage': nearest_damage
                })
            else:
                break
        
        return None