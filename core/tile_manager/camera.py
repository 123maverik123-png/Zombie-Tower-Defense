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
        """Центрирует камеру на изометрической карте по bounding box ромба."""
        if map_width == 0 or map_height == 0:
            self.x = 0
            self.y = 0
            return

        # Изо bounding box: ромб (W+H)*ts*0.5 wide, (W+H)*ts*0.25 tall
        # Левый край ромба в экранных координатах (до offset): -H*ts*0.5
        iso_w = (map_width + map_height) * tile_size * 0.5
        iso_h = (map_width + map_height) * tile_size * 0.25
        left_edge = -map_height * tile_size * 0.5

        offset_x = (self.screen_width - iso_w) / 2 - left_edge
        offset_y = max((self.available_height - iso_h) / 2, 0)

        self.x = -int(offset_x)
        self.y = -int(offset_y)

        print(f"Camera iso centered: ({self.x}, {self.y}), iso_box={int(iso_w)}x{int(iso_h)}")
    
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