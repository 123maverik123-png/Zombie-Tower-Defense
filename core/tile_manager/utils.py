# core/tile_manager/utils.py
from typing import List, Tuple


def get_path_from_map(map_data: List[List[str]], tile_size: int) -> List[Tuple[int, int]]:
    """
    Находит путь по карте от портала к замку.
    
    Args:
        map_data: Двумерный массив с типами тайлов
        tile_size: Размер тайла в пикселях
    
    Returns:
        Список координат пути в пикселях
    """
    map_height = len(map_data)
    map_width = len(map_data[0]) if map_height > 0 else 0
    
    # Находим портал (начало пути)
    start = None
    for y in range(map_height):
        for x in range(map_width):
            if map_data[y][x] == 'portal':
                start = (x, y)
                break
        if start:
            break
    
    if not start:
        print("❌ Portal not found!")
        return []
    
    # Находим замок (конец пути)
    end = None
    for y in range(map_height):
        for x in range(map_width):
            if map_data[y][x] == 'castle':
                end = (x, y)
                break
        if end:
            break
    
    if not end:
        print("❌ Castle not found!")
        return []
    
    # Построение пути
    path = [start]
    current = start
    visited = set([start])
    max_steps = 500
    
    while current != end and len(path) < max_steps:
        x, y = current
        found = False
        
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = x + dx, y + dy
            if (nx, ny) in visited:
                continue
            if 0 <= nx < map_width and 0 <= ny < map_height:
                tile = map_data[ny][nx]
                if tile.startswith('road_') or tile == 'castle' or tile == 'portal':
                    visited.add((nx, ny))
                    path.append((nx, ny))
                    current = (nx, ny)
                    found = True
                    break
        
        if not found:
            if len(path) > 1:
                path.pop()
                current = path[-1]
            else:
                break
    
    if current != end:
        if end not in path:
            path.append(end)
    
    # Убираем дубликаты
    unique_path = []
    for cell in path:
        if cell not in unique_path:
            unique_path.append(cell)
    path = unique_path
    
    # Конвертируем в пиксели
    path_pixels = []
    for x, y in path:
        px = x * tile_size + tile_size // 2
        py = y * tile_size + tile_size // 2
        path_pixels.append((px, py))
    
    return path_pixels


def is_on_path(map_data: List[List[str]], x: int, y: int) -> bool:
    """Проверяет, находится ли клетка на пути"""
    if 0 <= x < len(map_data[0]) and 0 <= y < len(map_data):
        tile = map_data[y][x]
        return tile.startswith('road_') or tile == 'portal' or tile == 'castle'
    return False


def can_build(map_data: List[List[str]], x: int, y: int) -> bool:
    """Проверяет, можно ли строить на клетке"""
    if 0 <= x < len(map_data[0]) and 0 <= y < len(map_data):
        tile = map_data[y][x]
        return not (tile.startswith('road_') or tile == 'portal' or tile == 'castle')
    return False


def get_map_statistics(map_data: List[List[str]]) -> dict:
    """Возвращает статистику карты"""
    stats = {
        'width': len(map_data[0]) if map_data else 0,
        'height': len(map_data),
        'road_count': 0,
        'portal_count': 0,
        'castle_count': 0,
        'grass_count': 0
    }
    
    for row in map_data:
        for cell in row:
            if cell.startswith('road_'):
                stats['road_count'] += 1
            elif cell == 'portal':
                stats['portal_count'] += 1
            elif cell == 'castle':
                stats['castle_count'] += 1
            elif cell == 'grass':
                stats['grass_count'] += 1
    
    return stats