# entities/tower/shooting/acid.py
from typing import List, Optional
from entities.projectile import Projectile
from core.event_bus import EventBus


class AcidShooting:
    """Кислотная башня — летящий снаряд (зелёный шарик с хвостом).

    При попадании: прямой урон + AoE, эффект 'кислота' поверх текущего,
    и остаётся лужа на полу (урон наступившим). Вся логика попадания —
    в Projectile._hit_acid (снаряд летит к цели).
    """

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

        config = tower.config.copy()
        config['projectile_type'] = 'acid'
        config['id'] = 'acid'

        projectile = Projectile(
            start_pos=tower.get_center(),
            target=target,
            speed=tower.projectile_speed,
            damage=damage,
            damage_type=tower.damage_type,
            config=config
        )
        projectile.aoe_radius = tower.aoe_radius
        projectile.acid_damage = tower.acid_damage
        projectile.acid_interval = tower.acid_interval
        projectile.acid_duration = tower.acid_duration

        EventBus.emit('tower_shot', {
            'tower_id': tower.id,
            'target': target,
            'damage_type': 'acid',
            'projectile': projectile,
            'tower_x': tower.x,
            'tower_y': tower.y,
            'tower_height': tower.height
        })

        # Снаряд добавляется в state через bus._on_tower_shot (projectile),
        # поэтому из shoot возвращаем None, чтобы не задвоить.
        return None
