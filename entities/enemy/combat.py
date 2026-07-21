# entities/enemy/combat.py
import random
from core.event_bus import EventBus

class EnemyCombat:
    """Управление атакой и уроном врага"""
    
    def __init__(self, enemy):
        self.enemy = enemy
        
        # Атака стен
        self.attack_cooldown = 0.0
        self.attack_rate = 0.5
        self.damage_to_wall = 50
        self.target_wall = None
        self.is_attacking_wall = False
        self.attack_range = 45
        self.has_attacked_this_frame = False
        
        # Состояние у ворот
        self.is_at_gate = False
        self.gate_attack_order = 0  # порядковый номер у ворот
        self.is_looking_for_exit = False  # ищет выход
        self.wall_side = None  # 'left' или 'right'
        self.assigned_wall = None  # стена, назначенная под атаку (идёт к ней)

    # ===== Координация штурма ворот и стен =====

    def count_attackers(self, target) -> int:
        """Сколько живых зомби атакуют цель ИЛИ назначены/идут к ней."""
        enemy = self.enemy
        if not enemy.state or target is None:
            return 0
        n = 0
        for other in enemy.state.enemies:
            if not other.alive:
                continue
            oc = other.combat
            if oc.target_wall is target and oc.is_attacking_wall:
                n += 1
            elif oc.assigned_wall is target:
                n += 1
        return n

    def _gate_wall_chain(self, gate):
        """Стены, примыкающие к воротам, двумя ветками вдоль линии обороны.

        Ворота 'h' (перекрывают вертикальный проход) → стены тянутся влево и
        вправо; 'v' → вверх и вниз. Идём по grid, пока есть смежная стена.
        Возвращает (branch_a, branch_b) — списки стен по возрастанию расстояния
        от ворот (первая — вплотную к воротам).
        """
        enemy = self.enemy
        if not enemy.state or not hasattr(gate, 'wx'):
            return [], []
        by_cell = {}
        for w in enemy.state.walls:
            if w.alive and hasattr(w, 'wx'):
                by_cell[(w.wx, w.wy)] = w

        orient = getattr(gate, 'orientation', 'h')
        if orient == 'h':
            dirs = ((-1, 0), (1, 0))   # влево, вправо
        else:
            dirs = ((0, -1), (0, 1))   # вверх, вниз

        branches = []
        for dx, dy in dirs:
            chain = []
            cx, cy = gate.wx + dx, gate.wy + dy
            while (cx, cy) in by_cell:
                chain.append(by_cell[(cx, cy)])
                cx += dx
                cy += dy
            branches.append(chain)
        return branches[0], branches[1]

    def choose_wall_target(self, gate):
        """Выбирает стену для атаки, когда ворота перегружены (>3 штурмующих).

        Возвращает:
          - Wall  — идти атаковать эту стену;
          - None  — штурмовать сами ворота (ещё есть места);
          - 'reroute' — все стены заняты, искать обход.
        """
        if self.count_attackers(gate) <= 3:
            return None

        branch_a, branch_b = self._gate_wall_chain(gate)
        if not branch_a and not branch_b:
            return 'reroute'

        # Случайная сторона (запоминаем за зомби), при пустой — другая
        if self.wall_side not in ('a', 'b'):
            self.wall_side = random.choice(['a', 'b'])
        order = ([branch_a, branch_b] if self.wall_side == 'a'
                 else [branch_b, branch_a])

        enemy = self.enemy
        for branch in order:
            free = [w for w in branch if self.count_attackers(w) == 0]
            if free:
                # Дальняя от зомби = ближе к порталу (конец линии обороны)
                free.sort(key=lambda w: (enemy.x - w.x) ** 2 + (enemy.y - w.y) ** 2)
                return free[-1]
        return 'reroute'

    
    def take_damage(self, amount: int, damage_type: str = 'physical') -> int:
        """Наносит урон с учётом уклонения"""
        enemy = self.enemy

        # Летающие враги неуязвимы ко всему, кроме урона ПВО
        if enemy.is_flying and damage_type != 'pvo':
            EventBus.emit('enemy_immune', {'enemy': enemy})
            return 0

        dodge_chance = enemy.config.get('dodge_chance', 0.0)
        if dodge_chance > 0 and random.random() < dodge_chance:
            EventBus.emit('enemy_dodged', {'enemy': enemy})
            return 0
        
        actual_damage = enemy._calculate_damage(amount, damage_type)
        enemy.health -= actual_damage
        
        if enemy.health <= 0:
            enemy.health = 0
            enemy.alive = False
            self.on_death()
        
        return actual_damage
    
    def can_attack_wall(self, wall) -> bool:
        """Проверяет, может ли враг атаковать стену (достаточно близко)"""
        enemy = self.enemy
        if not wall or not wall.alive:
            return False
        dist = ((enemy.x - wall.x) ** 2 + (enemy.y - wall.y) ** 2) ** 0.5
        return dist < self.attack_range + wall.width // 2
    
    def attack_wall(self, wall, dt: float) -> bool:
        """Атакует стену."""
        if not wall or not wall.alive:
            self.is_attacking_wall = False
            self.target_wall = None
            return False
        
        if not self.can_attack_wall(wall):
            self.is_attacking_wall = False
            self.target_wall = None
            return False
        
        self.is_attacking_wall = True
        self.target_wall = wall
        self.attack_cooldown -= dt
        if self.attack_cooldown <= 0:
            self.attack_cooldown = self.attack_rate
            wall.take_damage(self.damage_to_wall)
            self.has_attacked_this_frame = True
            return True
        return False
    
    def find_nearest_wall(self, gate) -> object:
        """Находит ближайшую стену к воротам (случайно левую или правую)"""
        enemy = self.enemy
        if not enemy.state:
            return None
        
        # Определяем сторону случайно
        if self.wall_side is None:
            self.wall_side = random.choice(['left', 'right'])
        
        # Ищем стену с нужной стороны
        walls = []
        for wall in enemy.state.walls:
            if not wall.alive:
                continue
            # Проверяем сторону относительно ворот
            if self.wall_side == 'left' and wall.x < gate.x:
                walls.append(wall)
            elif self.wall_side == 'right' and wall.x > gate.x:
                walls.append(wall)
        
        if walls:
            # Сортируем по расстоянию до ворот
            walls.sort(key=lambda w: abs(w.x - gate.x) + abs(w.y - gate.y))
            return walls[0]
        return None
    
    def reset_attack_state(self):
        """Сбрасывает состояние атаки для следующего кадра."""
        self.has_attacked_this_frame = False
    
    def on_reach_end(self):
        """Когда враг дошёл до конца пути"""
        enemy = self.enemy
        enemy.alive = False
        enemy.reached_end = True
        
        EventBus.emit('enemy_reached_end', {
            'enemy': enemy,
            'damage': enemy.damage_to_base
        })
        
        EventBus.emit('enemy_killed', {
            'enemy': enemy,
            'gold': 0,
            'exp': 0
        })
        
        enemy.states.start_dying()
    
    def on_death(self):
        """Когда враг убит башней"""
        enemy = self.enemy
        #print(f"💀 Enemy died! Sending enemy_killed event...")
        EventBus.emit('enemy_killed', {
            'enemy': enemy,
            'gold': enemy.reward_gold,
            'exp': enemy.reward_exp
        })
        
        enemy.states.start_dying()