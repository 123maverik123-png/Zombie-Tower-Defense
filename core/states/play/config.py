# core/states/play/config.py
import json


class PlayStateConfig:
    """Загрузка конфигураций для PlayState"""
    
    def __init__(self, state):
        self.state = state
    
    def get_tower_config(self, tower_type: str, level: int = 1) -> dict:
        """
        Загружает конфигурацию башни из файла с учётом улучшений.
        """
        state = self.state
        
        try:
            with open('data/configs/towers.json', 'r') as f:
                config = json.load(f).get(tower_type, {})
        except:
            return {}
        
        if not config:
            return {}
        
        config = config.copy()
        tile_size = state.tile_manager.tile_size
        # Сохраняем tile_size — нужен апгрейдам для конвертации range_cells
        config['tile_size'] = tile_size
        
        # Конвертируем клетки в пиксели
        if 'range_cells' in config:
            config['range'] = config['range_cells'] * tile_size
            del config['range_cells']
        
        if 'aoe_radius_cells' in config:
            config['aoe_radius'] = config['aoe_radius_cells'] * tile_size
            del config['aoe_radius_cells']
        
        # Применяем улучшения
        if level > 1:
            stats = config.get('upgrade_stats', {}).get(f'level_{level}', {})
            for key, value in stats.items():
                if key == 'range_cells':
                    config['range'] = value * tile_size
                elif key == 'aoe_radius_cells':
                    config['aoe_radius'] = value * tile_size
                else:
                    config[key] = value
        
        return config