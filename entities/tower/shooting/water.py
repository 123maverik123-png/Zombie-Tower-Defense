# entities/tower/shooting/water.py
from typing import List, Optional
from entities.projectile import Projectile
from core.event_bus import EventBus
from core.audio import AudioManager


class WaterShooting:
    """Водяная башня — накладывает эффект 'Вода' (снимает огонь)"""
    
    def __init__(self, tower):
        self.tower = tower
    
    def shoot(self, enemies: List) -> Optional[Projectile]:
        tower = self.tower
        target = tower.target
        
        if not target:
            return None
        
        if hasattr(target, 'apply_water_effect'):
            target.apply_water_effect(tower.effect_duration)
        
        EventBus.emit('tower_shot', {
            'tower_id': tower.id,
            'target': target,
            'damage_type': 'water',
            'projectile': None,
            'tower_x': tower.x,
            'tower_y': tower.y
        })
        
        audio = AudioManager()
        audio.play_sound("water_shoot", volume_override=0.25)
        
        return None