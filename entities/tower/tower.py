# entities/tower/tower.py
import pygame
import math
import random
from typing import Optional, List
from entities.base import Entity
from .targeting import TowerTargeting
from .shooting import TowerShooting
from .upgrades import TowerUpgrades
from .visuals import TowerVisuals


class Tower(Entity):
    """Башня — координаты (x, y) = центр"""
    
    def __init__(self, x: float, y: float, config: dict):
        super().__init__(
            entity_id=config.get('id', 'sniper'),
            x=x,
            y=y,
            config=config
        )
        
        self.range = config.get('range', 250)
        self.damage = config.get('damage', 50)
        self.fire_rate = config.get('fire_rate', 1.5)
        self.fire_timer = 0.0
        self.attack_cooldown = self.fire_rate
        self.fire_timer = random.uniform(0, self.fire_rate)
        
        self.damage_type = config.get('damage_type', 'physical')
        self.projectile_speed = config.get('projectile_speed', 500)
        self.aoe_radius = config.get('aoe_radius', 0)
        self.slow_duration = config.get('slow_duration', 0)
        self.slow_multiplier = config.get('slow_multiplier', 0.5)
        
        self.effect_duration = config.get('effect_duration', 10.0)
        self.acid_damage = config.get('acid_damage', 0)
        self.acid_interval = config.get('acid_interval', 0.5)
        self.acid_duration = config.get('acid_duration', 0)
        self.bonus_multiplier = config.get('bonus_multiplier', 1.0)

        # Параметры поджога (огнемёт)
        self.fire_dot_damage = config.get('fire_dot_damage', 4)
        self.fire_dot_interval = config.get('fire_dot_interval', 0.5)
        self.fire_dot_duration = config.get('fire_dot_duration', 3.0)
        
        self.target: Optional[Entity] = None
        self.target_type = config.get('target_type', 'ground')
        
        self.width = config.get('width', 64)
        self.height = config.get('height', 64)
        self.rect = pygame.Rect(x - self.width//2, y - self.height//2, self.width, self.height)
        
        self.chain_count = config.get('chain_count', 0)
        self.burning_grounds = []
        
        # Огнемёт — управление струёй и звуком
        self._flame_sound_playing = False
        self.flame_target = None
        self.flame_falling = []
        self.flame_level = 1
        
        # Для глобального звука огнемёта
        self._was_flame_target = False
        
        # Таймеры для управления звуком
        self._flame_sound_timer = 0.0
        self._flame_sound_cooldown = 0.0
        self._flame_has_target = False
        self._sound_reset_timer = 0.0
        self._flame_update_counter = 0
        
        self.targeting = TowerTargeting(self)
        self.shooting = TowerShooting(self)
        self.upgrades = TowerUpgrades(self)

        # Поворотная голова (пулемёт/огнемёт): угол в градусах, 0 = вправо
        self.aim_angle = 0.0
        self._aim_target_angle = 0.0
        self.visuals = TowerVisuals(self)
        
        self.image = None
        self.visuals.load_image()
    
    def upgrade(self) -> bool:
        result = self.upgrades.upgrade()
        if result:
            self.flame_level = self.upgrades.level
        return result
    
    def get_center(self) -> tuple:
        return (self.x, self.y)
    
    def update(self, dt: float, enemies: List[Entity]):
        if not self.alive:
            return None
        
        self.shooting.update_burning_grounds(dt, enemies)
        
        # Фильтруем только живых врагов
        alive_enemies = [e for e in enemies if e.alive]
        
        # Выбор цели
        if self.target_type == 'flying':
            self.target = self.targeting.find_target(alive_enemies, 'flying')
        elif self.target_type == 'all':
            self.target = self.targeting.find_target(alive_enemies, 'all')
        else:
            self.target = self.targeting.find_target(alive_enemies, 'ground')
        
        # Проверяем цель
        has_target = False
        if self.target and self.target.alive:
            from .targeting import in_square_range
            if in_square_range(self, self.target):
                has_target = True

        # Плавный доворот головы к цели (пулемёт/огнемёт)
        if has_target:
            self._aim_target_angle = math.degrees(
                math.atan2(self.target.y - self.y, self.target.x - self.x))
        diff = (self._aim_target_angle - self.aim_angle + 180) % 360 - 180
        turn_speed = 360 * dt  # градусов в секунду
        if abs(diff) <= turn_speed:
            self.aim_angle = self._aim_target_angle
        else:
            self.aim_angle += turn_speed if diff > 0 else -turn_speed
        self.aim_angle %= 360
        
        # Огнемёт — глобальный звук
        if self.id == 'flamethrower':
            self._update_flame_sound_global(has_target)
        
        # Если цели нет — выходим
        if not has_target:
            self.fire_timer = self.attack_cooldown
            self.flame_target = None
            return None
        
        # Сохраняем цель для струи
        if self.id == 'flamethrower':
            self.flame_target = self.target
        
        # Стреляем
        self.fire_timer += dt
        if self.fire_timer >= self.attack_cooldown:
            self.fire_timer = 0
            return self.shooting.shoot(enemies)
        
        return None
    
    def _update_flame_sound_global(self, has_target: bool):
        """Управляет глобальным звуком огнемёта через AudioManager."""
        from core.audio import AudioManager
        audio = AudioManager()
        
        if has_target and not self._was_flame_target:
            audio.flame_start()
            self._was_flame_target = True
        elif not has_target and self._was_flame_target:
            audio.flame_stop()
            self._was_flame_target = False
    
    def on_death(self):
        """При удалении башни — освобождаем звук"""
        if self.id == 'flamethrower':
            from core.audio import AudioManager
            audio = AudioManager()
            if self._was_flame_target:
                audio.flame_stop()
                self._was_flame_target = False
        self.alive = False
    
    def reset_flame_sound_state(self):
        """Сброс состояния звука (для паузы)"""
        if self.id == 'flamethrower':
            self._was_flame_target = False
    
    def add_falling_flame(self, x: float, y: float):
        """Добавляет падающее пламя при смерти врага"""
        # ✅ ЗАКОММЕНТИРОВАНО ПАДАЮЩЕЕ ПЛАМЯ
        # base_duration = 1.0
        # duration = base_duration + (self.flame_level - 1) * 0.3
        # duration = min(duration, 3.0)
        # 
        # self.flame_falling.append({
        #     'x': x,
        #     'y': y,
        #     'timer': duration,
        #     'max_timer': duration,
        #     'speed': random.uniform(30, 60),
        #     'particles': self._generate_falling_particles(x, y)
        # })
        pass
    
    def _generate_falling_particles(self, x: float, y: float) -> List[dict]:
        """Генерирует частицы для падающего пламени"""
        # ✅ ЗАКОММЕНТИРОВАНО
        return []
    
    def get_stats(self) -> dict:
        return self.upgrades.get_stats()

    def draw_batch(self, renderer, offset_x: int = 0, offset_y: int = 0):
        self.visuals.draw_batch(renderer, offset_x, offset_y)