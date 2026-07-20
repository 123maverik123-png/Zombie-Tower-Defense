# core/tile_manager/camera.py
from typing import Tuple


class Camera:
    """Управление камерой"""
    
    def __init__(self, screen_width: int, screen_height: int, available_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.available_height = available_height
        self.x = 0
        self.y = 0
    
    def center(self, map_width: int, map_height: int, tile_size: int):
        """
        Центрирует камеру на карте.
        camera.x и camera.y — отрицательные отступы (позиция камеры в мире).
        """
        if map_width == 0 or map_height == 0:
            self.x = 0
            self.y = 0
            return
        
        map_pixel_width = map_width * tile_size
        map_pixel_height = map_height * tile_size
        
        if map_pixel_width < self.screen_width:
            self.x = -(self.screen_width - map_pixel_width) // 2
        else:
            self.x = 0
        
        if map_pixel_height < self.available_height:
            self.y = -(self.available_height - map_pixel_height) // 2
        else:
            self.y = 0
        
        self.x = int(self.x)
        self.y = int(self.y)
        
        print(f"🎯 Camera centered: ({self.x}, {self.y})")
        print(f"   Map: {map_pixel_width}x{map_pixel_height}, Screen: {self.screen_width}x{self.available_height}")
    
    def get_offset(self) -> Tuple[int, int]:
        """Возвращает смещение для отрисовки (положительные значения). offset = -camera_position"""
        return -self.x, -self.y
    
    def move(self, dx: int, dy: int):
        self.x += dx
        self.y += dy
    
    def set_position(self, x: int, y: int):
        self.x = x
        self.y = y
    
    def on_resize(self, screen_width: int, screen_height: int, available_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.available_height = available_height