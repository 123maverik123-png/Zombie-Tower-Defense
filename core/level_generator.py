# core/level_generator.py
import random
from typing import List, Dict, Any, Tuple

class LevelGenerator:
    def __init__(self):
        self.all_enemy_types = ['zombie_normal', 'zombie_fast', 'zombie_tank', 'zombie_night']
        self.tile_size = 65
        self.width = 28
        self.height = 18
    
    def get_available_enemies(self, level_number: int) -> List[str]:
        if level_number <= 5:
            return ['zombie_normal']
        elif level_number <= 10:
            return ['zombie_normal', 'zombie_fast']
        elif level_number <= 15:
            return ['zombie_normal', 'zombie_fast', 'zombie_tank']
        else:
            return ['zombie_normal', 'zombie_fast', 'zombie_tank', 'zombie_night']
    
    def generate_level(self, level_number: int, tile_size: int = 65) -> Dict[str, Any]:
        self.tile_size = tile_size
        print("\n" + "=" * 60)
        print(f"🔄 GENERATING LEVEL {level_number}")
        print("=" * 60)
        
        path_cells = self._generate_path(level_number)
        print(f"📍 Path cells: {len(path_cells)}")
        
        map_data = self._build_map_from_path(path_cells)
        
        path_pixels = []
        for x, y in path_cells:
            px = x * self.tile_size + self.tile_size // 2
            py = y * self.tile_size + self.tile_size // 2
            path_pixels.append((px, py))
        
        waves = self._generate_waves(level_number)
        
        return {
            'name': f"Level {level_number}",
            'tile_size': self.tile_size,
            'map': map_data,
            'path': path_pixels,
            'waves': waves,
            'start_x': path_pixels[0][0] if path_pixels else 100,
            'start_y': path_pixels[0][1] if path_pixels else 100,
            'end_x': path_pixels[-1][0] if path_pixels else 100,
            'end_y': path_pixels[-1][1] if path_pixels else 100
        }
    
    def _generate_path(self, level_number: int) -> List[Tuple[int, int]]:
        width = self.width
        height = self.height
        
        start_x = 2
        start_y = height // 2
        end_x = width - 3
        end_y = height // 2
        
        path = [(start_x, start_y)]
        x, y = start_x, start_y
        visited = set(path)
        
        num_turns = random.randint(10, 30)
        min_len = 2
        max_len = 5
        direction = 0
        failed_attempts = 0
        max_attempts = 200
        
        for _ in range(num_turns):
            if failed_attempts > max_attempts:
                break
            
            if direction == 0:
                possible = [2, 3]
            elif direction == 1:
                possible = [2, 3]
            elif direction == 2:
                possible = [0, 1]
            else:
                possible = [0, 1]
            
            random.shuffle(possible)
            found = False
            
            for new_dir in possible:
                dx, dy = 0, 0
                if new_dir == 0:
                    dx = 1
                elif new_dir == 1:
                    dx = -1
                elif new_dir == 2:
                    dy = 1
                else:
                    dy = -1
                
                length = random.randint(min_len, max_len)
                nx, ny = x, y
                valid = True
                temp_path = []
                
                for step in range(length):
                    nx += dx
                    ny += dy
                    
                    if nx < 2 or nx >= width - 2 or ny < 2 or ny >= height - 2:
                        valid = False
                        break
                    
                    if (nx, ny) in visited:
                        valid = False
                        break
                    
                    too_close = False
                    for check_dx, check_dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                        check_pos = (nx + check_dx, ny + check_dy)
                        if check_pos in visited and check_pos != (nx - dx, ny - dy):
                            too_close = True
                            break
                    
                    if too_close:
                        valid = False
                        break
                    
                    temp_path.append((nx, ny))
                
                if valid and len(temp_path) >= 1:
                    for cell in temp_path:
                        path.append(cell)
                        visited.add(cell)
                    x, y = nx, ny
                    direction = new_dir
                    found = True
                    failed_attempts = 0
                    break
            
            if not found:
                failed_attempts += 1
                if max_len > 2:
                    max_len -= 1
                for test_dir in range(4):
                    if test_dir == direction:
                        continue
                    dx, dy = 0, 0
                    if test_dir == 0:
                        dx = 1
                    elif test_dir == 1:
                        dx = -1
                    elif test_dir == 2:
                        dy = 1
                    else:
                        dy = -1
                    
                    nx, ny = x + dx, y + dy
                    if (nx, ny) not in visited and 2 <= nx < width - 2 and 2 <= ny < height - 2:
                        x, y = nx, ny
                        path.append((x, y))
                        visited.add((x, y))
                        direction = test_dir
                        found = True
                        failed_attempts = 0
                        break
        
        while x < end_x:
            nx = x + 1
            if (nx, y) not in visited:
                x = nx
                path.append((x, y))
                visited.add((x, y))
            else:
                break
        
        while y != end_y:
            ny = y + (1 if y < end_y else -1)
            if (x, ny) not in visited:
                y = ny
                path.append((x, y))
                visited.add((x, y))
            else:
                break
        
        if (end_x, end_y) not in path:
            while x < end_x:
                x += 1
                if (x, y) not in path:
                    path.append((x, y))
            while x > end_x:
                x -= 1
                if (x, y) not in path:
                    path.append((x, y))
            while y < end_y:
                y += 1
                if (x, y) not in path:
                    path.append((x, y))
            while y > end_y:
                y -= 1
                if (x, y) not in path:
                    path.append((x, y))
        
        if (end_x, end_y) not in path:
            path.append((end_x, end_y))
        
        unique_path = []
        for cell in path:
            if cell not in unique_path:
                unique_path.append(cell)
        
        return unique_path
    
    def _build_map_from_path(self, path: List[Tuple[int, int]]) -> List[List[str]]:
        """
        Строит карту из пути. Только клетки пути получают дорожные тайлы.
        Все остальные клетки — трава.
        """
        width = self.width
        height = self.height
        
        # Создаём карту из травы
        map_data = [['grass' for _ in range(width)] for _ in range(height)]
        path_set = set(path)
        
        print(f"   🛤️ Building map from {len(path_set)} path cells")
        
        # Проходим по ВСЕМ клеткам пути
        for idx, (x, y) in enumerate(path):
            # Проверяем соседей (только среди клеток пути)
            up = (x, y-1) in path_set
            down = (x, y+1) in path_set
            left = (x-1, y) in path_set
            right = (x+1, y) in path_set
            
            neighbors = sum([up, down, left, right])
            
            # Определяем тип клетки
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
                    if up or down:
                        map_data[y][x] = 'road_v'
                    else:
                        map_data[y][x] = 'road_h'
            elif neighbors >= 3:
                map_data[y][x] = 'road_cross'
            else:
                if up or down:
                    map_data[y][x] = 'road_v'
                else:
                    map_data[y][x] = 'road_h'
        
        # Проверяем, что портал и замок на месте
        portal_count = sum(1 for row in map_data for cell in row if cell == 'portal')
        castle_count = sum(1 for row in map_data for cell in row if cell == 'castle')
        road_count = sum(1 for row in map_data for cell in row if cell.startswith('road_'))
        
        if portal_count == 0 and path:
            x, y = path[0]
            map_data[y][x] = 'portal'
            portal_count = 1
        
        if castle_count == 0 and path:
            x, y = path[-1]
            map_data[y][x] = 'castle'
            castle_count = 1
        
        print(f"   🛤️ Road tiles: {road_count}, Portal: {portal_count}, Castle: {castle_count}")
        print(f"   📊 Total path cells: {len(path)}, Total road tiles: {road_count}")
        
        return map_data
    
    def _generate_waves(self, level_number: int) -> List[Dict[str, Any]]:
        difficulty = level_number / 50.0
        num_waves = random.randint(4, 9)
        
        available_enemies = self.get_available_enemies(level_number)
        
        waves = []
        for wave_num in range(num_waves):
            base_count = random.randint(6, 12)
            count = int(base_count * (1 + wave_num / num_waves) * (1 + difficulty * 0.4))
            count = min(count, 55)
            
            num_types = min(len(available_enemies), 1 + int(difficulty * 2))
            selected_types = random.sample(available_enemies, min(num_types, len(available_enemies)))
            
            enemies = []
            for enemy_type in selected_types:
                weight = random.randint(1, 5) * (1 + int(difficulty * 2))
                enemies.append({'id': enemy_type, 'weight': weight})
            
            spawn_delay = max(0.3, random.uniform(0.6, 1.8) - difficulty * 0.4)
            
            waves.append({
                'enemies': enemies,
                'count': count,
                'spawn_delay': round(spawn_delay, 2)
            })
        
        if level_number % 5 == 0 and 'zombie_tank' in available_enemies:
            waves.append({
                'enemies': [
                    {'id': 'zombie_tank', 'weight': 3},
                    {'id': 'zombie_normal', 'weight': 1}
                ],
                'count': 5 + int(difficulty * 5),
                'spawn_delay': 1.5
            })
        
        return waves


class LevelData:
    def __init__(self):
        self.completed_levels = set()
        self.unlocked_level = 1
        self.total_levels = 50
    
    def is_completed(self, level: int) -> bool:
        return level in self.completed_levels
    
    def is_unlocked(self, level: int) -> bool:
        return level <= self.unlocked_level
    
    def complete_level(self, level: int):
        self.completed_levels.add(level)
        if level >= self.unlocked_level:
            self.unlocked_level = min(level + 1, self.total_levels)
    
    def to_dict(self) -> dict:
        return {
            'completed_levels': list(self.completed_levels),
            'unlocked_level': self.unlocked_level,
            'total_levels': self.total_levels
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LevelData':
        level_data = cls()
        level_data.completed_levels = set(data.get('completed_levels', []))
        level_data.unlocked_level = data.get('unlocked_level', 1)
        level_data.total_levels = data.get('total_levels', 50)
        return level_data