# entities/tower/shooting/base.py

from typing import List, Optional
from entities.projectile import Projectile
from core.audio import AudioManager


class TowerShooting:
    def __init__(self, tower):
        self.tower = tower
    
    def shoot(self, enemies: List) -> Optional[Projectile]:
        tower = self.tower
        
        # Огнемёт — звук управляется отдельно
        if tower.id == 'flamethrower':
            from .flamethrower import FlamethrowerShooting
            return FlamethrowerShooting(tower).shoot(enemies)
        
        if tower.id == 'pvo':
            from .pvo import PVOShooting
            return PVOShooting(tower).shoot(enemies)
        
        if tower.id == 'water':
            from .water import WaterShooting
            return WaterShooting(tower).shoot(enemies)
        
        if tower.id == 'freeze':
            from .freeze import FreezeShooting
            return FreezeShooting(tower).shoot(enemies)
        
        if tower.id == 'acid':
            from .acid import AcidShooting
            return AcidShooting(tower).shoot(enemies)
        
        if tower.id == 'rocket':
            from .rocket import RocketShooting
            return RocketShooting(tower).shoot(enemies)
        
        if tower.id == 'electric':
            from .electric import ElectricShooting
            return ElectricShooting(tower).shoot(enemies)
        
        if tower.id in ['sniper', 'turret']:
            from .instant import InstantShooting
            return InstantShooting(tower).shoot(enemies)
        
        # По умолчанию — снаряд
        from .projectile import ProjectileShooting
        return ProjectileShooting(tower).shoot(enemies)
    
    def update_burning_grounds(self, dt: float, enemies: List):
        tower = self.tower
        if tower.upgrades.special_effect != 'burning_ground_duration_2':
            return
        
        import math
        for ground in tower.burning_grounds[:]:
            ground['timer'] -= dt
            if ground['timer'] <= 0:
                tower.burning_grounds.remove(ground)
            else:
                for enemy in enemies:
                    if not enemy.alive:
                        continue
                    dist = math.hypot(enemy.x - ground['pos'][0], enemy.y - ground['pos'][1])
                    if dist < tower.aoe_radius:
                        enemy.take_damage(5, 'fire')
                        if hasattr(enemy, 'apply_fire_effect'):
                            enemy.apply_fire_effect(1.0)