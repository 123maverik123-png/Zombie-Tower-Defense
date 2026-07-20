# core/tile_manager/map_loader.py
import pygame
import os
from typing import Dict, List, Tuple

from .utils import get_path_from_map, get_map_statistics


class MapLoader:
    """Загрузка карты и тайлов"""
    
    def __init__(self):
        self.tiles: Dict[str, pygame.Surface] = {}
        self.map_data: List[List[str]] = []
        self.map_width = 0
        self.map_height = 0
        self.path_pixels: List[Tuple[int, int]] = []
        self.tile_size = 65
    
    def load_tiles(self, biome: str = None) -> Dict[str, pygame.Surface]:
        """Загружает все тайлы из папки (биом — подпапка новой темы)"""
        from core.graphics_theme import THEME
        if THEME == 'kenney' and biome:
            tile_folder = f"assets/images/tiles/{biome}"
        else:
            tile_folder = "assets/images/tiles"
        
        tile_names = {
            'grass': 'tile_grass.png',
            'castle': 'tile_castle.png',
            'portal': 'tile_portal.png',
            'road_cross': 'tile_road_cross.png',
            'road_h': 'tile_road_straight_h.png',
            'road_v': 'tile_road_straight_v.png',
            'road_bl': 'tile_road_turn_bottom_left.png',
            'road_br': 'tile_road_turn_bottom_right.png',
            'road_tl': 'tile_road_turn_top_left.png',
            'road_tr': 'tile_road_turn_top_right.png'
        }
        
        loaded_tiles = {}
        for name, filename in tile_names.items():
            path = os.path.join(tile_folder, filename)
            if os.path.exists(path):
                try:
                    tile = pygame.image.load(path).convert_alpha()
                    loaded_tiles[name] = tile
                except Exception as e:
                    print(f"⚠️ Error loading {name}: {e}")
            else:
                print(f"⚠️ Tile not found: {filename}")
        
        self.tiles = loaded_tiles
        print(f"✅ Loaded {len(self.tiles)}/10 tiles")
        return loaded_tiles
    
    def set_map(self, map_data: List[List[str]], tile_size: int):
        """Устанавливает карту"""
        self.map_data = map_data
        self.map_height = len(map_data)
        self.map_width = len(map_data[0]) if self.map_height > 0 else 0
        self.tile_size = tile_size
        
        stats = get_map_statistics(map_data)
        print(f"🗺️ Map set: {self.map_width}x{self.map_height}")
        print(f"   🛤️ Road tiles: {stats['road_count']}, Portal: {stats['portal_count']}, Castle: {stats['castle_count']}")
        
        # Обновляем путь
        self.path_pixels = get_path_from_map(map_data, tile_size)
    
    def get_path(self) -> List[Tuple[int, int]]:
        """Возвращает путь в пикселях"""
        return self.path_pixels
    
    def get_path_cells(self) -> List[Tuple[int, int]]:
        """Возвращает путь в клетках"""
        if not self.path_pixels:
            return []
        
        path_cells = []
        for px, py in self.path_pixels:
            x = px // self.tile_size
            y = py // self.tile_size
            path_cells.append((x, y))
        
        return path_cells
    
    def get_map_size(self) -> Tuple[int, int]:
        return (self.map_width, self.map_height)