# entities/enemy/movement.py
import math

# Полуширина «полосы»: макс. смещение врага вбок от центра дороги (px).
# Дорога — 1 тайл (65px), поэтому 18 держит толпу в пределах дороги.
LANE_HALF_WIDTH = 18


class EnemyMovement:
    """Управление движением и коллизиями врага"""

    def __init__(self, enemy):
        self.enemy = enemy
        self.move_distance = 0
        self.stuck_timer = 0
        self.stuck_threshold = 0.5

    def _offset_target(self, target_x, target_y, seg_x, seg_y):
        """Сдвигает целевую точку вбок перпендикулярно сегменту дороги.

        Перпендикуляр берётся от направления сегмента (пред. waypoint ->
        текущий), а НЕ от вектора враг->цель: у поворота последний
        становится крошечным и его перпендикуляр скачет каждый кадр —
        враг начинал кружиться. Направление сегмента постоянно.
        """
        seg_len = math.hypot(seg_x, seg_y)
        if seg_len < 1:
            return target_x, target_y
        nx, ny = -seg_y / seg_len, seg_x / seg_len
        shift = self.enemy.lane_offset * LANE_HALF_WIDTH
        return target_x + nx * shift, target_y + ny * shift

    def _segment_dir(self, path, index):
        """Вектор направления сегмента дороги, ведущего в waypoint index."""
        if index <= 0:
            # первый сегмент: от текущей позиции к точке
            return path[index][0] - self.enemy.x, path[index][1] - self.enemy.y
        px, py = path[index - 1]
        cx, cy = path[index]
        return cx - px, cy - py
    
    def update(self, dt: float):
        """Обновляет движение врага"""
        enemy = self.enemy
        
        enemy.combat.reset_attack_state()
        
        # Проверяем, может ли враг атаковать ворота или стены
        self._check_wall_attack()
        
        # Если враг летающий — игнорирует стены и ворота
        if enemy.is_flying:
            self._move_flying(dt)
            return
        
        # Если атакует стену — не двигается
        if enemy.combat.is_attacking_wall:
            if enemy.combat.target_wall and enemy.combat.target_wall.alive:
                enemy.combat.attack_wall(enemy.combat.target_wall, dt)
                return
            else:
                enemy.combat.is_attacking_wall = False
                enemy.combat.target_wall = None
                enemy.combat.is_looking_for_exit = False
                enemy.combat.is_at_gate = False
                enemy.combat.gate_attack_order = 0
        
        if enemy.combat.is_looking_for_exit:
            self._move_to_exit(dt)
            return
        
        # ✅ Используем путь из enemy (уже в экранных координатах)
        path = enemy.path
        if not path:
            return
        
        if enemy.current_target_index >= len(path):
            enemy.reached_end = True
            enemy.on_reach_end()
            return
        
        target_x, target_y = path[enemy.current_target_index]
        dx = target_x - enemy.x
        dy = target_y - enemy.y
        distance = math.hypot(dx, dy)
        
        if distance < 1:
            enemy.current_target_index += 1
            return
        
        enemy.dx = dx
        enemy.dy = dy
        
        if abs(dx) > abs(dy):
            enemy.direction = 'right' if dx > 0 else 'left'
        else:
            enemy.direction = 'down' if dy > 0 else 'up'
        
        # Смещаем цель вбок для «толпы». Перпендикуляр берём от направления
        # сегмента дороги (стабилен на поворотах), идём к смещённой точке и
        # по ней считаем достижение waypoint.
        seg_x, seg_y = self._segment_dir(path, enemy.current_target_index)
        aim_x, aim_y = self._offset_target(target_x, target_y, seg_x, seg_y)
        adx = aim_x - enemy.x
        ady = aim_y - enemy.y
        aim_dist = math.hypot(adx, ady)

        current_speed = enemy.speed * enemy.effects.slow_multiplier
        self.move_distance = current_speed * dt

        new_x = enemy.x
        new_y = enemy.y
        reached = False

        if self.move_distance >= aim_dist:
            new_x = aim_x
            new_y = aim_y
            reached = True
        elif aim_dist > 0:
            new_x += (adx / aim_dist) * self.move_distance
            new_y += (ady / aim_dist) * self.move_distance

        # Проверяем коллизию
        if not self._check_collision(new_x, new_y):
            enemy.x = new_x
            enemy.y = new_y
            if reached:
                enemy.current_target_index += 1
            self.stuck_timer = 0
        else:
            self.stuck_timer += dt
            if self.stuck_timer > self.stuck_threshold:
                self._try_attack_nearby_wall()
        
        enemy.rect.x = enemy.x - enemy.width // 2
        enemy.rect.y = enemy.y - enemy.height // 2
        
        if self.move_distance > 0:
            enemy.animation_frame += dt * 8
        enemy.image = enemy.visuals.get_current_frame()
    
    def _move_flying(self, dt: float):
        """Движение летающего врага (игнорирует стены и ворота)"""
        enemy = self.enemy
        
        path = enemy.path
        if not path:
            return
        
        if enemy.current_target_index >= len(path):
            enemy.reached_end = True
            enemy.on_reach_end()
            return
        
        target_x, target_y = path[enemy.current_target_index]
        dx = target_x - enemy.x
        dy = target_y - enemy.y
        distance = math.hypot(dx, dy)
        
        if distance < 1:
            enemy.current_target_index += 1
            return
        
        enemy.dx = dx
        enemy.dy = dy
        
        if abs(dx) > abs(dy):
            enemy.direction = 'right' if dx > 0 else 'left'
        else:
            enemy.direction = 'down' if dy > 0 else 'up'
        
        current_speed = enemy.speed * enemy.effects.slow_multiplier
        self.move_distance = current_speed * dt

        seg_x, seg_y = self._segment_dir(path, enemy.current_target_index)
        aim_x, aim_y = self._offset_target(target_x, target_y, seg_x, seg_y)
        adx = aim_x - enemy.x
        ady = aim_y - enemy.y
        aim_dist = math.hypot(adx, ady)

        if self.move_distance >= aim_dist:
            enemy.x = aim_x
            enemy.y = aim_y
            enemy.current_target_index += 1
        elif aim_dist > 0:
            enemy.x += (adx / aim_dist) * self.move_distance
            enemy.y += (ady / aim_dist) * self.move_distance
        
        enemy.rect.x = enemy.x - enemy.width // 2
        enemy.rect.y = enemy.y - enemy.height // 2
        
        if self.move_distance > 0:
            enemy.animation_frame += dt * 8
        enemy.image = enemy.visuals.get_current_frame()
    
    def _check_wall_attack(self):
        """Проверяет, может ли враг атаковать ворота или стены."""
        enemy = self.enemy
        if not enemy.state:
            return
        
        if enemy.is_flying:
            return
        
        for gate in enemy.state.gates:
            if not gate.alive:
                continue
            dist = ((enemy.x - gate.x) ** 2 + (enemy.y - gate.y) ** 2) ** 0.5
            if dist < 60:
                enemy.combat.attack_wall(gate, 0.016)
                return
        
        for wall in enemy.state.walls:
            if not wall.alive:
                continue
            dist = ((enemy.x - wall.x) ** 2 + (enemy.y - wall.y) ** 2) ** 0.5
            if dist < 50:
                enemy.combat.attack_wall(wall, 0.016)
                return
    
    def _move_to_exit(self, dt: float):
        """Движение к обходной цели (в обход ворот)"""
        enemy = self.enemy
        
        has_alive_gate = False
        for gate in enemy.state.gates:
            if gate.alive:
                has_alive_gate = True
                break
        
        if not has_alive_gate:
            enemy.combat.is_looking_for_exit = False
            enemy.combat.is_at_gate = False
            enemy.combat.gate_attack_order = 0
            return
        
        path = enemy.path
        if not path:
            return
        
        if enemy.current_target_index >= len(path):
            enemy.reached_end = True
            enemy.on_reach_end()
            return
        
        target_x, target_y = path[enemy.current_target_index]
        dx = target_x - enemy.x
        dy = target_y - enemy.y
        distance = math.hypot(dx, dy)
        
        if distance < 1:
            enemy.current_target_index += 1
            return
        
        enemy.dx = dx
        enemy.dy = dy
        
        if abs(dx) > abs(dy):
            enemy.direction = 'right' if dx > 0 else 'left'
        else:
            enemy.direction = 'down' if dy > 0 else 'up'
        
        current_speed = enemy.speed * enemy.effects.slow_multiplier
        self.move_distance = current_speed * dt
        
        new_x = enemy.x
        new_y = enemy.y
        
        if self.move_distance >= distance:
            new_x = target_x
            new_y = target_y
        else:
            new_x += (dx / distance) * self.move_distance
            new_y += (dy / distance) * self.move_distance
        
        if not self._check_wall_collision_only(new_x, new_y):
            enemy.x = new_x
            enemy.y = new_y
            if self.move_distance >= distance:
                enemy.current_target_index += 1
            self.stuck_timer = 0
        else:
            self._try_attack_nearby_wall()
        
        enemy.rect.x = enemy.x - enemy.width // 2
        enemy.rect.y = enemy.y - enemy.height // 2
        
        if self.move_distance > 0:
            enemy.animation_frame += dt * 8
        enemy.image = enemy.visuals.get_current_frame()
    
    def _try_attack_nearby_wall(self):
        """Пытается найти ближайшую стену для атаки."""
        enemy = self.enemy
        if not enemy.state:
            return
        
        nearest_wall = None
        nearest_dist = float('inf')
        for wall in enemy.state.walls:
            if not wall.alive:
                continue
            is_attacked = False
            for other_enemy in enemy.state.enemies:
                if other_enemy == enemy:
                    continue
                if other_enemy.combat.target_wall == wall and other_enemy.combat.is_attacking_wall:
                    is_attacked = True
                    break
            if is_attacked:
                continue
            dist = ((enemy.x - wall.x) ** 2 + (enemy.y - wall.y) ** 2) ** 0.5
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_wall = wall
        
        if nearest_wall:
            enemy.combat.attack_wall(nearest_wall, 0)
    
    def _check_collision(self, new_x: float, new_y: float) -> bool:
        """Проверяет коллизию с воротами и стенами."""
        enemy = self.enemy
        if not enemy.state:
            return False
        
        if enemy.is_flying:
            return False
        
        for gate in enemy.state.gates:
            if not gate.alive:
                continue
            if (new_x - enemy.width//2 < gate.x + gate.width//2 and
                new_x + enemy.width//2 > gate.x - gate.width//2 and
                new_y - enemy.height//2 < gate.y + gate.height//2 and
                new_y + enemy.height//2 > gate.y - gate.height//2):
                return True
        
        for wall in enemy.state.walls:
            if not wall.alive:
                continue
            if (new_x - enemy.width//2 < wall.x + wall.width//2 and
                new_x + enemy.width//2 > wall.x - wall.width//2 and
                new_y - enemy.height//2 < wall.y + wall.height//2 and
                new_y + enemy.height//2 > wall.y - wall.height//2):
                return True
        
        return False
    
    def _check_wall_collision_only(self, new_x: float, new_y: float) -> bool:
        """Проверяет коллизию только со стенами (для обхода ворот)."""
        enemy = self.enemy
        if not enemy.state:
            return False
        
        for wall in enemy.state.walls:
            if not wall.alive:
                continue
            if (new_x - enemy.width//2 < wall.x + wall.width//2 and
                new_x + enemy.width//2 > wall.x - wall.width//2 and
                new_y - enemy.height//2 < wall.y + wall.height//2 and
                new_y + enemy.height//2 > wall.y - wall.height//2):
                return True
        
        return False