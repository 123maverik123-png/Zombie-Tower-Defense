# core/level_loader.py
from typing import List, Tuple, Dict, Any
from systems.wave import WaveFactory

MAP_WIDTH = 28
MAP_HEIGHT = 18
TILE_SIZE = 65


def build_map_from_path(path: List[Tuple[int, int]]) -> List[List[str]]:
    """Строит карту из пути."""
    map_data = [['grass' for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    path_set = set(path)

    for idx, (x, y) in enumerate(path):
        up = (x, y-1) in path_set
        down = (x, y+1) in path_set
        left = (x-1, y) in path_set
        right = (x+1, y) in path_set
        neighbors = sum([up, down, left, right])

        if idx == 0:
            map_data[y][x] = 'portal'
        elif idx == len(path) - 1:
            map_data[y][x] = 'castle'
        elif neighbors == 2:
            if up and down:
                map_data[y][x] = 'road_v'
            elif left and right:
                map_data[y][x] = 'road_h'
            elif up and right:
                map_data[y][x] = 'road_tr'
            elif up and left:
                map_data[y][x] = 'road_tl'
            elif down and right:
                map_data[y][x] = 'road_br'
            elif down and left:
                map_data[y][x] = 'road_bl'
            else:
                map_data[y][x] = 'road_h' if (left or right) else 'road_v'
        elif neighbors >= 3:
            map_data[y][x] = 'road_cross'
        else:
            map_data[y][x] = 'road_h' if (left or right) else 'road_v'
    return map_data


def build_level(level_number: int) -> Dict[str, Any]:
    """Собирает уровень из waypoints."""
    from data.levels_data import LEVELS

    if level_number not in LEVELS:
        raise ValueError(f"Level {level_number} not found in levels_data.py")

    level_info = LEVELS[level_number]
    waypoints = level_info["waypoints"]
    name = level_info.get("name", f"Level {level_number}")

    map_data = build_map_from_path(waypoints)
    path_pixels = [(x * TILE_SIZE + TILE_SIZE//2, y * TILE_SIZE + TILE_SIZE//2) for x, y in waypoints]
    
    # ✅ Используем WaveFactory для генерации волн
    waves = WaveFactory.generate_waves(level_number)

    return {
        "name": name,
        "tile_size": TILE_SIZE,
        "map": map_data,
        "path": path_pixels,
        "waves": waves,
        "decorations": level_info.get("decorations"),
        "start_x": path_pixels[0][0],
        "start_y": path_pixels[0][1],
        "end_x": path_pixels[-1][0],
        "end_y": path_pixels[-1][1]
    }


def level_exists(level_number: int) -> bool:
    """Проверяет, существует ли уровень."""
    try:
        from data.levels_data import LEVELS
        return level_number in LEVELS
    except:
        return False