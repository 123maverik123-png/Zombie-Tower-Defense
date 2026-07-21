# entities/enemy/effects.py
import random
import math

class EnemyEffects:
    """Управление эффектами врага"""
    
    def __init__(self, enemy):
        self.enemy = enemy
        
        # Замедление
        self.slow_multiplier = 1.0
        self.slow_timer = 0.0
        self.slow_resistance = enemy.config.get('slow_resistance', 0.0)
        
        # Огонь
        self.fire_effect_timer = 0.0
        self.fire_effect_active = False
        self.fire_damage_timer = 0.0
        self.fire_dot_damage = 4
        self.fire_dot_interval = 0.5
        
        # Вода
        self.water_effect_timer = 0.0
        self.water_effect_active = False
        
        # Заморозка
        self.freeze_effect_timer = 0.0
        self.freeze_effect_active = False
        
        # Электричество
        self.electric_effect_timer = 0.0
        self.electric_effect_active = False
        self.electric_sparks = []
        
        # Кислота
        self.acid_effect_active = False
        self.acid_damage = 0
        self.acid_interval = 0.5
        self.acid_timer = 0.0
        self.acid_duration = 0.0
    
    def update(self, dt: float):
        enemy = self.enemy
        
        self._update_electric(dt)
        self._update_fire(dt)
        self._update_water(dt)
        self._update_freeze(dt)
        self._update_acid(dt)
        
        if self.slow_timer > 0:
            self.slow_timer -= dt
            if self.slow_timer <= 0:
                self.slow_multiplier = 1.0
    
    def _update_electric(self, dt: float):
        if self.electric_effect_active:
            self.electric_effect_timer -= dt
            if self.electric_effect_timer <= 0:
                self.electric_effect_active = False
                self.electric_sparks = []
            else:
                for spark in self.electric_sparks[:]:
                    spark['x'] += spark['dx'] * dt
                    spark['y'] += spark['dy'] * dt
                    spark['life'] -= dt
                    if spark['life'] <= 0:
                        self.electric_sparks.remove(spark)
                if random.random() < 0.3:
                    self.electric_sparks.append({
                        'x': random.uniform(-self.enemy.width//2, self.enemy.width//2),
                        'y': random.uniform(-self.enemy.height//2, self.enemy.height//2),
                        'dx': random.uniform(-30, 30),
                        'dy': random.uniform(-30, 30),
                        'life': random.uniform(0.2, 0.5)
                    })
    
    def _update_fire(self, dt: float):
        if self.fire_effect_active:
            self.fire_effect_timer -= dt
            self.fire_damage_timer += dt

            if self.fire_damage_timer >= self.fire_dot_interval:
                self.fire_damage_timer = 0
                self.enemy.health -= self.fire_dot_damage
                if self.enemy.health <= 0:
                    self.enemy.health = 0
                    self.enemy.alive = False
                    self.enemy.on_death()

            if self.fire_effect_timer <= 0:
                self.fire_effect_active = False
                self.fire_damage_timer = 0
    
    def _update_water(self, dt: float):
        if self.water_effect_active:
            self.water_effect_timer -= dt
            if self.water_effect_timer <= 0:
                self.water_effect_active = False
    
    def _update_freeze(self, dt: float):
        if self.freeze_effect_active:
            self.freeze_effect_timer -= dt
            if self.freeze_effect_timer <= 0:
                self.freeze_effect_active = False
    
    def _update_acid(self, dt: float):
        if self.acid_effect_active:
            self.acid_timer += dt
            self.acid_duration -= dt
            if self.acid_timer >= self.acid_interval:
                self.acid_timer = 0
                enemy = self.enemy
                enemy.health -= self.acid_damage
                if enemy.health <= 0:
                    enemy.health = 0
                    enemy.alive = False
                    enemy.on_death()
            if self.acid_duration <= 0:
                self.acid_effect_active = False
    
    def apply_slow(self, multiplier: float, duration: float):
        if self.enemy.is_flying:
            return
        effective_multiplier = 1.0 - (1.0 - multiplier) * (1.0 - self.slow_resistance)
        self.slow_multiplier = min(self.slow_multiplier, effective_multiplier)
        self.slow_timer = max(self.slow_timer, duration)
    
    def apply_electric_effect(self, duration: float = 1.0):
        if self.enemy.is_flying:
            return
        
        self.electric_effect_active = True
        self.electric_effect_timer = duration
        self.electric_sparks = []
        for _ in range(8):
            self.electric_sparks.append({
                'x': random.uniform(-self.enemy.width//2, self.enemy.width//2),
                'y': random.uniform(-self.enemy.height//2, self.enemy.height//2),
                'dx': random.uniform(-30, 30),
                'dy': random.uniform(-30, 30),
                'life': random.uniform(0.2, 0.5)
            })
    
    def apply_fire_effect(self, duration: float = 3.0, dot_damage: int = 4, dot_interval: float = 0.5):
        if self.enemy.is_flying:
            return
        if self.water_effect_active:
            return
        self.fire_effect_active = True
        self.fire_effect_timer = duration
        self.fire_damage_timer = 0.0
        self.fire_dot_damage = dot_damage
        self.fire_dot_interval = dot_interval
    
    def apply_water_effect(self, duration: float = 10.0):
        if self.enemy.is_flying:
            return
        if self.fire_effect_active:
            self.fire_effect_active = False
            self.fire_effect_timer = 0
            self.fire_damage_timer = 0
        self.water_effect_active = True
        self.water_effect_timer = duration
    
    def apply_freeze_effect(self, duration: float = 3.0):
        if self.enemy.is_flying:
            return
        self.freeze_effect_active = True
        self.freeze_effect_timer = duration

    def apply_acid_effect(self, damage: int, interval: float, duration: float):
        if self.enemy.is_flying:
            return
        self.acid_effect_active = True
        self.acid_damage = damage
        self.acid_interval = interval
        self.acid_timer = 0.0
        self.acid_duration = duration