# core/tile_manager/manager.py
import pygame
from typing import List, Tuple, Dict

from .map_loader import MapLoader
from .camera import Camera
from .draw import TileDraw
from .utils import get_path_from_map, is_on_path, can_build
from utils.debug import dprint


class TileManager:
    """Управление тайлами и картой"""
    
    def __init__(self, screen_width: int = 2560, screen_height: int = 1440,
                 bottom_offset: int = 100, biome: str = 'forest'):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.bottom_offset = bottom_offset
        self.available_height = screen_height - bottom_offset
        self.biome = biome

        self.map_loader = MapLoader()
        self.camera = Camera(screen_width, screen_height, self.available_height)
        self.drawer = TileDraw()

        self.tiles: Dict[str, pygame.Surface] = {}
        self.map_data: List[List[str]] = []
        self.map_width = 0
        self.map_height = 0
        self.path_pixels: List[Tuple[int, int]] = []
        self.camera_x = 0
        self.camera_y = 0

        self.background = None
        self._load_background()

        self.tiles = self.map_loader.load_tiles(biome)
        
        self._tile_size = 65
        self.original_tile_size = 65
        self.drawer.set_tile_size(self._tile_size)
        self.map_loader.tile_size = self._tile_size
    
    def _load_background(self):
        import os
        bg_path = "assets/images/menu_bg.jpg"
        if os.path.exists(bg_path):
            try:
                self.background = pygame.image.load(bg_path).convert()
                dprint("✅ Background loaded")
            except Exception as e:
                print(f"⚠️ Error loading background: {e}")
                self.background = None
        else:
            self.background = None
            print("⚠️ Background not found")
    
    @property
    def tile_size(self):
        return self._tile_size
    
    @tile_size.setter
    def tile_size(self, value):
        if self._tile_size != value:
            self._tile_size = value
            self.drawer.set_tile_size(value)
            self.map_loader.tile_size = value
    
    def set_map(self, map_data: List[List[str]]):
        self.map_data = map_data
        self.map_width = len(map_data[0]) if map_data else 0
        self.map_height = len(map_data)

        self._calculate_tile_size()
        
        self.map_loader.set_map(map_data, self.tile_size)
        self.path_pixels = self.map_loader.get_path()
        
        
        self._center_camera()
        
        print(f"📍 Map set: {self.map_width}x{self.map_height}, Camera: ({self.camera.x}, {self.camera.y})")
    
    def _calculate_tile_size(self):
        if self.map_width == 0 or self.map_height == 0:
            self.tile_size = self.original_tile_size
            return
        
        margin = 20
        available_width = self.screen_width - margin * 2
        available_height = self.available_height - margin * 2
        
        tile_from_width = available_width // self.map_width
        tile_from_height = available_height // self.map_height
        
        new_tile_size = min(tile_from_width, tile_from_height, self.original_tile_size)
        new_tile_size = max(30, new_tile_size)
        
        if new_tile_size != self.tile_size:
            self.tile_size = new_tile_size
            print(f"📐 Tile size calculated: {self.tile_size}px (from {self.map_width}x{self.map_height})")
    
    def _center_camera(self):
        self.camera.center(self.map_width, self.map_height, self.tile_size)
        self.camera_x = self.camera.x
        self.camera_y = self.camera.y
    
    def get_offset(self) -> Tuple[int, int]:
        return self.camera.get_offset()
    
    def get_path_from_map(self) -> List[Tuple[int, int]]:
        """Возвращает путь в мировых координатах (без смещения камеры)"""
        return self.path_pixels
    
    def get_path_cells(self) -> List[Tuple[int, int]]:
        return self.map_loader.get_path_cells()
    
    def is_on_path(self, x: int, y: int) -> bool:
        return is_on_path(self.map_data, x, y)
    
    def can_build(self, x: int, y: int) -> bool:
        return can_build(self.map_data, x, y)
    
    def draw_opengl(self, renderer):
        offset_x, offset_y = self.get_offset()
        self.drawer.draw_opengl(
            renderer, self.map_data, self.tiles,
            (offset_x, offset_y),
            self.screen_width, self.available_height,
            self.background
        )
    
    def get_grid_position(self, pixel_x: float, pixel_y: float) -> Tuple[int, int]:
        """Конвертирует экранные координаты в клетки (мировые)"""
        offset_x, offset_y = self.get_offset()
        world_x = pixel_x - offset_x
        world_y = pixel_y - offset_y
        grid_x = int(world_x // self.tile_size)
        grid_y = int(world_y // self.tile_size)
        return (grid_x, grid_y)
    
    def get_pixel_position(self, grid_x: int, grid_y: int) -> Tuple[int, int]:
        """Конвертирует клетки в мировые координаты"""
        return (
            grid_x * self.tile_size + self.tile_size // 2,
            grid_y * self.tile_size + self.tile_size // 2
        )
    
    def on_resolution_changed(self, screen_width: int, screen_height: int):
        dprint(f"🔄 TileManager resolution changed: {screen_width}x{screen_height}")
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.available_height = screen_height - self.bottom_offset
        
        self.camera.on_resize(screen_width, screen_height, self.available_height)
        
        if self.map_width > 0:
            self._calculate_tile_size()
            self.map_loader.set_map(self.map_data, self.tile_size)
            self.path_pixels = self.map_loader.get_path()
            self._center_camera()
        
        # Путь не пересчитываем, он всегда в мировых координатах
        # self.path_pixels уже есть, он не меняется при смене разрешения