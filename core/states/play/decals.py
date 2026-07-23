# core/states/play/decals.py
from entities.decals import Decal

class PlayDecals:
    def __init__(self, state):
        self.state = state

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