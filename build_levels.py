# build_levels.py
import json
import os
from typing import List, Tuple

# === Конфигурация карты ===
MAP_WIDTH = 28
MAP_HEIGHT = 18
TILE_SIZE = 65

def build_map_from_path(path: List[Tuple[int, int]]) -> List[List[str]]:
    """Строит карту из пути (аналог level_generator._build_map_from_path)."""
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

def generate_path(start: Tuple[int, int], segments: List[Tuple[int, int, int]]) -> List[Tuple[int, int]]:
    """
    Генерирует путь из начальной точки и списка сегментов (dx, dy, length).
    """
    path = [start]
    x, y = start
    for dx, dy, length in segments:
        for _ in range(length):
            x += dx
            y += dy
            # Проверка границ (на всякий случай)
            if not (0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT):
                raise ValueError(f"Path out of bounds at ({x}, {y})")
            path.append((x, y))
    return path

def generate_waves(level_number: int) -> List[dict]:
    """Генерирует простые волны для уровня."""
    # Можно сделать более сложные, но для первых 10 уровней достаточно.
    num_waves = 3 + (level_number // 3)  # 3-6 волн
    waves = []
    for i in range(num_waves):
        count = 5 + i * 2 + level_number
        waves.append({
            'enemies': [{'id': 'zombie_normal', 'weight': 1}],
            'count': min(count, 30),
            'spawn_delay': max(0.5, 1.0 - i * 0.05)
        })
    # Босс на каждом 5-м уровне (начиная с 5)
    if level_number % 5 == 0 and level_number >= 5:
        waves.append({
            'enemies': [{'id': 'zombie_boss', 'weight': 1}],
            'count': 1,
            'spawn_delay': 1.5
        })
    return waves

# === Определения уровней ===
# Каждый уровень: список сегментов (dx, dy, length)
LEVEL_SEGMENTS = {
    1: [(1, 0, 10)],  # простой прямой путь
    2: [(1, 0, 5), (0, 1, 5), (1, 0, 8)],
    3: [(1, 0, 5), (0, 1, 5), (1, 0, 8), (0, -1, 6)],
    4: [(1, 0, 5), (0, 1, 5), (1, 0, 8), (0, -1, 6), (-1, 0, 9)],
    5: [(1, 0, 5), (0, 1, 5), (1, 0, 8), (0, -1, 6), (-1, 0, 9), (0, 1, 6)],
    6: [(1, 0, 4), (0, 1, 4), (1, 0, 5), (0, -1, 4), (1, 0, 6), (0, 1, 5), (1, 0, 4)],
    7: [(1, 0, 3), (0, 1, 6), (1, 0, 4), (0, -1, 5), (1, 0, 5), (0, 1, 4), (1, 0, 6), (0, -1, 3)],
    8: [(1, 0, 5), (0, 1, 3), (1, 0, 4), (0, -1, 4), (1, 0, 5), (0, 1, 5), (1, 0, 3), (0, -1, 6), (1, 0, 4)],
    9: [(1, 0, 4), (0, 1, 5), (1, 0, 3), (0, -1, 4), (1, 0, 5), (0, 1, 4), (1, 0, 6), (0, -1, 5), (1, 0, 3), (0, 1, 2)],
    10: [(1, 0, 3), (0, 1, 4), (1, 0, 5), (0, -1, 3), (1, 0, 4), (0, 1, 5), (1, 0, 3), (0, -1, 4), (1, 0, 6), (0, 1, 5), (1, 0, 3)],
}

def build_level(level_number: int):
    start = (2, 9)
    segments = LEVEL_SEGMENTS.get(level_number)
    if segments is None:
        raise ValueError(f"No segments defined for level {level_number}")

    path = generate_path(start, segments)
    map_data = build_map_from_path(path)

    # Путь в пикселях
    path_pixels = [(x * TILE_SIZE + TILE_SIZE//2, y * TILE_SIZE + TILE_SIZE//2) for x, y in path]

    waves = generate_waves(level_number)

    level_data = {
        "name": f"Level {level_number}",
        "tile_size": TILE_SIZE,
        "map": map_data,
        "path": path_pixels,
        "waves": waves,
        "start_x": path_pixels[0][0],
        "start_y": path_pixels[0][1],
        "end_x": path_pixels[-1][0],
        "end_y": path_pixels[-1][1]
    }
    return level_data

def main():
    # Создаём папку
    os.makedirs("data/levels", exist_ok=True)

    for i in range(1, 11):
        print(f"Generating level {i}...")
        level_data = build_level(i)
        with open(f"data/levels/level_{i}.json", 'w', encoding='utf-8') as f:
            json.dump(level_data, f, indent=2, ensure_ascii=False)
        print(f"  -> Saved level_{i}.json")

    print("All levels generated successfully!")

if __name__ == "__main__":
    main()