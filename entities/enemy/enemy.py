# entities/enemy/enemy.py
import pygame
import math
import random
from typing import List, Tuple, Optional, Dict
from entities.base import Entity
from core.event_bus import EventBus
from .states import EnemyStates
from .movement import EnemyMovement
from .effects import EnemyEffects
from .combat import EnemyCombat
from .visuals import EnemyVisuals


class Enemy(Entity):
    """Враг с анимациями по 4 направлениям — координаты (x, y) = центр, МИРОВЫЕ (без смещения камеры)"""

    def __init__(self, config: dict, path_points: List[Tuple[float, float]],
                 animations: Dict[str, List[pygame.Surface]], state=None):

        # ✅ Путь и стартовая позиция - в МИРОВЫХ координатах,
        # как у башен/снарядов/стен. Смещение камеры добавляется
        # только в момент отрисовки (EnemyVisuals.draw получает offset_x/offset_y).
        start_x = path_points[0][0] if path_points else 0
        start_y = path_points[0][1] if path_points else 0

        super().__init__(
            entity_id=config.get('id', 'zombie_normal'),
            x=start_x,
            y=start_y,
            config=config
        )

        # Ссылка на PlayState для коллизий
        self.state = state

        # Флаг летающего врага
        self.is_flying = config.get('is_flying', False)
        self.ignore_walls = config.get('ignore_walls', False)

        # Рандомный разброс скорости ±7%
        base_speed = config.get('speed', 90.0)
        speed_variation = random.uniform(0.93, 1.07)
        self.speed = base_speed * speed_variation

        # ✅ Путь в МИРОВЫХ координатах
        self.path = path_points
        self.current_target_index = 1
        self.reached_end = False

        # Боковое смещение от центра дороги [-1..1] — чтобы враги шли
        # толпой, а не по одной линии. Умножается на LANE_WIDTH в movement.
        self.lane_offset = random.uniform(-1.0, 1.0)

        # Награда
        self.reward_gold = config.get('reward_gold', 5)
        self.reward_exp = config.get('reward_exp', 3)
        self.damage_to_base = config.get('base_damage', 1)

        # Босс
        self.is_boss = config.get('is_boss', False)

        # Размеры
        if animations and animations.get('down'):
            first_frame = animations['down'][0]
            base_width = first_frame.get_width()
            base_height = first_frame.get_height()

            if self.is_flying:
                # Летучая мышь крупная, парит над полем
                self.width = int(base_width * 1.05)
                self.height = int(base_height * 1.05)
            else:
                self.width = base_width
                self.height = base_height
        else:
            self.width = config.get('width', 54)
            self.height = config.get('height', 54)

        self.rect = pygame.Rect(
            self.x - self.width // 2,
            self.y - self.height // 2,
            self.width,
            self.height
        )

        # Инициализация модулей
        self.states = EnemyStates(self)
        self.movement = EnemyMovement(self)
        self.effects = EnemyEffects(self)
        self.combat = EnemyCombat(self)
        self.visuals = EnemyVisuals(self)

        # Анимации
        self.animations = animations
        self.animation_frame = 0
        self.animation_speed = config.get('animation_speed', 0.15)
        self.direction = 'down'
        self.dx = 0
        self.dy = 0
        self.image = self.visuals.get_current_frame()

        # Раны на теле — декали попаданий, живут на враге и исчезают с ним.
        # Каждая: {'decal': Decal, 'fx': доля ширины, 'fy': доля высоты}
        self.wounds = []

    def take_damage(self, amount: int, damage_type: str = 'physical') -> int:
        return self.combat.take_damage(amount, damage_type)

    def update(self, dt: float):
        self._update_wounds(dt)
        if not self.states.update(dt):
            return

        self.effects.update(dt)
        self.movement.update(dt)

        if self.movement.move_distance > 0:
            self.animation_frame += dt * 8
        self.image = self.visuals.get_current_frame()

    def add_wound(self, decal_type='blood_small', scale=0.3):
        """Добавляет рану на тело — декаль в случайной точке от ног до головы.

        Рана живёт на враге (двигается с ним) и исчезает вместе с ним.
        Точка фиксируется как доля размера спрайта, чтобы держаться на теле.
        """
        import random
        from entities.decals import Decal
        # Точка на теле спрайта: 0 = центр по X; fy 0..1 = голова..ноги
        fx = random.uniform(-0.28, 0.28)
        fy = random.uniform(0.0, 1.0)
        decal = Decal(self.x, self.y, decal_type, scale=scale)
        # Рана не исчезает по своему таймеру — живёт пока жив враг
        decal.lifetime = float('inf')
        decal.max_lifetime = float('inf')
        decal.fade = False
        self.wounds.append({'decal': decal, 'fx': fx, 'fy': fy})

    def _update_wounds(self, dt: float):
        """Позиционирует раны на теле по текущим координатам врага.

        Спрайт рисуется от (y - h/1.2) вверх, тело занимает по вертикали
        примерно [y - 0.83h .. y + 0.17h] в ЭКРАННЫХ пикселях (после изопроекции).
        Раскидываем раны от головы к ногам через screen-space подъём z, а не
        сдвиг мировых координат — иначе изопроекция шерит смещение по диагонали.
        """
        if not self.wounds:
            return
        head_z = self.height * 0.78
        feet_z = -self.height * 0.05
        if self.is_flying:
            # Летающий спрайт парит выше — раны смещаем вместе с ним
            lift = self.height * 0.55 + self.visuals.float_offset
            head_z += lift
            feet_z += lift
        for w in self.wounds:
            w['decal'].x = self.x + w['fx'] * self.width
            w['decal'].y = self.y
            w['decal'].z = head_z + (feet_z - head_z) * w['fy']
            w['decal'].update(dt)

    def on_reach_end(self):
        self.combat.on_reach_end()

    def on_death(self):
        self.combat.on_death()

    def apply_fire_effect(self, duration: float = 3.0, dot_damage: int = 4, dot_interval: float = 0.5):
        self.effects.apply_fire_effect(duration, dot_damage, dot_interval)

    def apply_water_effect(self, duration: float = 10.0):
        self.effects.apply_water_effect(duration)

    def apply_freeze_effect(self, duration: float = 3.0):
        self.effects.apply_freeze_effect(duration)

    def apply_acid_effect(self, damage: int, interval: float, duration: float):
        self.effects.apply_acid_effect(damage, interval, duration)

    def apply_acid_ground_effect(self, damage: int, interval: float, duration: float):
        self.effects.apply_acid_ground_effect(damage, interval, duration)

    def apply_electric_effect(self, duration: float = 1.0):
        self.effects.apply_electric_effect(duration)

    def apply_slow(self, multiplier: float, duration: float):
        self.effects.apply_slow(multiplier, duration)