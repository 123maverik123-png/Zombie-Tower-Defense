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
    
    def take_damage(self, amount: int, damage_type: str = 'physical') -> int:
        """Наносит урон с учётом уклонения"""
        enemy = self.enemy
        
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