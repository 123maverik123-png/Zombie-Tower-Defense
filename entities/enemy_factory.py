# entities/enemy_factory.py
import json
import os
from typing import Dict, Type, List, Tuple, Optional
from entities.enemy import Enemy
from utils.sprite_loader import SpriteLoader

class EnemyFactory:
    """Фабрика для создания врагов с анимациями"""
    _registry: Dict[str, Type[Enemy]] = {}
    _animations_cache: Dict[str, dict] = {}
    
    @classmethod
    def register(cls, enemy_type: str, enemy_class: Type[Enemy]):
        """Регистрирует новый тип врага"""
        cls._registry[enemy_type] = enemy_class
    
    @classmethod
    def load_enemy_configs(cls, config_path: str = "data/configs/enemies.json") -> dict:
        """Загружает конфигурации врагов из JSON"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except:
            print(f"⚠️ Could not load enemy configs from {config_path}")
            return {}
    
    @classmethod
    def get_animations(cls, config: dict) -> dict:
        """Загружает анимации для врага на основе конфига"""
        loader = SpriteLoader()
        
        sprite_folder = config.get('sprite_folder')
        if sprite_folder:
            from core.graphics_theme import enemy_sprite_folder
            sprite_folder = enemy_sprite_folder(sprite_folder)
            frames_per_anim = config.get('frames_per_anim', 4)
            cache_key = f"folder_{sprite_folder}_{frames_per_anim}_{loader.scale_factor:.3f}"
            
            if cache_key in cls._animations_cache:
                return cls._animations_cache[cache_key]
            
            animations = loader.load_animations_from_folder(sprite_folder, frames_per_anim)
            cls._animations_cache[cache_key] = animations
            return animations
        
        sheet_name = config.get('sprite_sheet')
        if sheet_name:
            sprite_size = config.get('sprite_size', 256)
            cols = config.get('cols', 4)
            rows = config.get('rows', 4)
            
            cache_key = f"sheet_{sheet_name}_{sprite_size}_{cols}_{rows}_{loader.scale_factor:.3f}"
            
            if cache_key in cls._animations_cache:
                return cls._animations_cache[cache_key]
            
            animations = loader.load_zombie_animations(sheet_name, sprite_size, cols, rows)
            cls._animations_cache[cache_key] = animations
            return animations
        
        print(f"⚠️ No sprite source defined for enemy type")
        return loader._create_fallback_animations(85)
    
    @classmethod
    def create(cls, config: dict, path_points: List[Tuple[float, float]], state=None) -> Enemy:
        """Создаёт врага с анимациями"""
        enemy_type = config.get('id', 'zombie_normal')
        animations = cls.get_animations(config)
        
        enemy_class = cls._registry.get(enemy_type)
        if enemy_class:
            return enemy_class(config, path_points, animations, state)
        
        print(f"⚠️ Enemy type '{enemy_type}' not registered, using base Enemy")
        return Enemy(config, path_points, animations, state)
    
    @classmethod
    def get_available_types(cls) -> List[str]:
        return list(cls._registry.keys())


# === РЕГИСТРИРУЕМ ВСЕХ ВРАГОВ ===
EnemyFactory.register('zombie', Enemy)
EnemyFactory.register('zombie_light', Enemy)
EnemyFactory.register('zombie_heavy', Enemy)
EnemyFactory.register('zombie_fast', Enemy)
EnemyFactory.register('zombie_normal', Enemy)
EnemyFactory.register('zombie_tank', Enemy)
EnemyFactory.register('zombie_night', Enemy)
EnemyFactory.register('zombie_boss', Enemy)
EnemyFactory.register('zombie_flying', Enemy)  # ✅ ДОБАВЛЕНО