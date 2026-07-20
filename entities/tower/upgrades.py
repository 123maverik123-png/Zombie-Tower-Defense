# entities/tower/upgrades.py
from core.event_bus import EventBus

class TowerUpgrades:
    """Управление улучшениями башни"""
    
    def __init__(self, tower):
        self.tower = tower
        self.level = 1
        self.max_level = tower.config.get('max_level', 4)
        self.cost = tower.config.get('cost', 100)
        self.upgrade_cost = tower.config.get('upgrade_cost', 150)
        self.upgrade_stats = tower.config.get('upgrade_stats', {})
        self.special_effect = None

    def upgrade(self) -> bool:
        """Улучшает башню"""
        tower = self.tower

        if self.level >= self.max_level:
            return False

        stats = self.upgrade_stats.get(f'level_{self.level + 1}', {})
        tile_size = tower.config.get('tile_size', 65)

        # Мультипликативные улучшения
        tower.damage *= stats.get('damage_mult', 1.0)
        tower.fire_rate *= stats.get('fire_rate_mult', 1.0)
        tower.attack_cooldown = tower.fire_rate

        # Абсолютные значения (перезаписывают текущие)
        if 'range_cells' in stats:
            tower.range = stats['range_cells'] * tile_size
        if 'aoe_radius_cells' in stats:
            tower.aoe_radius = stats['aoe_radius_cells'] * tile_size
        for key in ('chain_count', 'slow_multiplier', 'slow_duration',
                    'effect_duration', 'bonus_multiplier',
                    'acid_damage', 'acid_duration',
                    'fire_dot_damage', 'fire_dot_duration'):
            if key in stats:
                setattr(tower, key, stats[key])

        self.level += 1
        self.upgrade_cost = int(self.upgrade_cost * 1.4)

        # Спецэффект
        if self.level == self.max_level and 'special' in stats:
            self.special_effect = stats['special']
            tower.special_effect = self.special_effect

        # Перезагружаем изображение
        tower.visuals.load_image()

        EventBus.emit('tower_upgraded', {'tower': tower, 'level': self.level})
        return True
    
    def get_stats(self) -> dict:
        """Возвращает статистику башни"""
        tower = self.tower
        return {
            'level': self.level,
            'max_level': self.max_level,
            'damage': tower.damage,
            'range': tower.range,
            'fire_rate': tower.fire_rate,
            'cost': self.cost,
            'upgrade_cost': self.upgrade_cost,
            'is_max_level': self.level >= self.max_level,
            'special_effect': self.special_effect
        }