# core/states/play/decals.py
import math
from entities.decals import Decal
from entities.hit_effect import HitEffect

class PlayDecals:
    def __init__(self, state):
        self.state = state
        self.muzzle_flashes = []
    
    def add_muzzle_flash(self, tower_x, tower_y, target, tower_id):
        """Добавляет дульную вспышку (маленькая, у края башни)"""
        state = self.state
        if not target:
            return
        
        # Вычисляем направление на цель
        dx = target.x - tower_x
        dy = target.y - tower_y
        distance = math.hypot(dx, dy)
        if distance == 0:
            return
        
        dx /= distance
        dy /= distance
        
        # Смещаем вспышку к краю башни (в сторону цели)
        offset = 32
        flash_x = tower_x + dx * offset
        flash_y = tower_y + dy * offset
        
        # Создаём маленькую вспышку
        if tower_id == 'sniper':
            effect = HitEffect(flash_x, flash_y, 'sniper')
            self.muzzle_flashes.append(effect)
            # ✅ ЗАКОММЕНТИРОВАН ДЫМ
            # decal = Decal(flash_x, flash_y, 'smoke_light', scale=0.2)
            # state.decals.append(decal)
        
        elif tower_id == 'turret':
            effect = HitEffect(flash_x, flash_y, 'turret')
            self.muzzle_flashes.append(effect)
            # ✅ ЗАКОММЕНТИРОВАН ДЫМ
            # decal = Decal(flash_x, flash_y, 'smoke_light', scale=0.15)
            # state.decals.append(decal)
        
        elif tower_id == 'flamethrower':
            effect = HitEffect(flash_x, flash_y, 'flamethrower')
            self.muzzle_flashes.append(effect)
            # ✅ ЗАКОММЕНТИРОВАНО ПЛАМЯ
            # decal = Decal(flash_x, flash_y, 'fire', scale=0.3)
            # state.decals.append(decal)
        
        elif tower_id == 'electric':
            effect = HitEffect(flash_x, flash_y, 'electric')
            self.muzzle_flashes.append(effect)
            # ✅ ЗАКОММЕНТИРОВАНА ИСКРА
            # decal = Decal(flash_x, flash_y, 'spark', scale=0.2)
            # state.decals.append(decal)
    
    def add_hit_decal(self, target, decal_type='blood_small', scale=0.3):
        """Устар.: раны теперь живут на враге (Enemy.add_wound)."""
        if target and hasattr(target, 'add_wound'):
            target.add_wound(decal_type, scale)

    def add_hit_decal_at(self, x, y, decal_type='blood_small', scale=0.3):
        """Добавляет декаль попадания в точке на земле (для снарядов/луж)."""
        decal = Decal(x, y, decal_type, scale=scale)
        self.state.decals.append(decal)
    
    def add_death_decal(self, enemy):
        """Добавляет декаль смерти"""
        # ✅ ЗАКОММЕНТИРОВАНЫ ВСЕ ДЕКАЛИ СМЕРТИ
        # state = self.state
        # if enemy:
        #     decal_type = 'blood_large' if enemy.is_boss else 'blood'
        #     decal = Decal(enemy.x, enemy.y, decal_type, scale=0.7)
        #     state.decals.append(decal)
        pass
    
    def add_explosion_decal(self, x, y):
        """Добавляет декаль взрыва"""
        # ✅ ЗАКОММЕНТИРОВАНЫ ВСЕ ДЕКАЛИ ВЗРЫВА
        # state = self.state
        # decal = Decal(x, y, 'crack', scale=1.2)
        # state.decals.append(decal)
        # decal_smoke = Decal(x, y, 'smoke', scale=1.0)
        # state.decals.append(decal_smoke)
        pass
    
    def update(self, dt):
        """Обновляет все декали"""
        state = self.state
        
        # Обновляем обычные декали
        for decal in state.decals[:]:
            decal.update(dt)
            if not decal.alive:
                state.decals.remove(decal)
        
        # Обновляем дульные вспышки
        for flash in self.muzzle_flashes[:]:
            flash.update(dt)
            if not flash.alive:
                self.muzzle_flashes.remove(flash)
    
    def draw_muzzle_flashes(self, screen, offset_x=0, offset_y=0):
        """Рисует дульные вспышки поверх башен"""
        for flash in self.muzzle_flashes:
            flash.draw(screen, offset_x, offset_y)