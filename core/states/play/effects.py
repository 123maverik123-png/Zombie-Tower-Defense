# core/states/play/effects.py
from entities.hit_effect import HitEffect

class PlayEffects:
    def __init__(self, state):
        self.state = state
    
    def add_hit_effect(self, target, tower_id='turret'):
        state = self.state
        if not target or not target.alive:
            return
        
        effect_type = {
            'sniper': 'sniper',
            'turret': 'turret',
            'flamethrower': 'flamethrower',
            'electric': 'electric'
        }.get(tower_id, 'turret')
        
        effect = HitEffect(target.x, target.y, effect_type)
        state.hit_effects.append(effect)
    
    def add_muzzle_effect(self, x, y, tower_id):
        state = self.state
        effect_type = {
            'sniper': 'sniper',
            'turret': 'turret',
            'electric': 'electric'
        }.get(tower_id)
        
        if effect_type:
            effect = HitEffect(x, y, effect_type)
            state.hit_effects.append(effect)
    
    def add_explosion_effect(self, x, y):
        state = self.state
        effect = HitEffect(x, y, 'explosive')
        state.hit_effects.append(effect)
    
    def add_dodge_effect(self, enemy):
        state = self.state
        if enemy:
            effect = HitEffect(enemy.x, enemy.y, 'acid')
            state.hit_effects.append(effect)
    
    def update(self, dt):
        state = self.state
        for effect in state.hit_effects[:]:
            effect.update(dt)
            if not effect.alive:
                state.hit_effects.remove(effect)