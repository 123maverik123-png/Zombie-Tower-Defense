# core/states/play/events/bus.py
import random
import math
from core.event_bus import EventBus
from entities.decals import Decal
from entities.hit_effect import HitEffect

class BusEvents:
    """Обработчики событий EventBus"""
    
    def __init__(self, state):
        self.state = state
        self._water_sound_ticks = 0  # троттлинг звука водяной струи
    
    def setup(self):
        EventBus.subscribe('enemy_killed', self._on_enemy_killed)
        EventBus.subscribe('enemy_reached_end', self._on_enemy_reached_end)
        EventBus.subscribe('wave_complete', self._on_wave_complete)
        EventBus.subscribe('tower_shot', self._on_tower_shot)
        EventBus.subscribe('aoe_damage_request', self._on_aoe_damage)
        EventBus.subscribe('acid_splash_request', self._on_acid_splash)
        EventBus.subscribe('acid_pool_request', self._on_acid_pool)
        EventBus.subscribe('enemy_dodged', self._on_enemy_dodged)
        EventBus.subscribe('tower_upgraded', self._on_tower_upgraded)
        EventBus.subscribe('lightning_effect', self._on_lightning_effect)
        EventBus.subscribe('chain_lightning_effect', self._on_chain_lightning_effect)
    
    def _on_enemy_killed(self, data):
        state = self.state
        enemy = data['enemy']
        
        for tower in state.towers:
            if tower.id == 'flamethrower' and tower.flame_target == enemy:
                tower.add_falling_flame(enemy.x, enemy.y)
                break
        
        state.player.add_gold(data['gold'])
        state.player.add_experience(data['exp'])
        state.player.stats['total_kills'] += 1
        state.total_kills += 1
        state.audio.play_sound("death")
        state.wave_manager.on_enemy_killed()
        # ✅ ЗАКОММЕНТИРОВАНА ДЕКАЛЬ СМЕРТИ
        # state.decals_logic.add_death_decal(enemy)
    
    def _on_enemy_reached_end(self, data):
        state = self.state
        enemy = data.get('enemy')
        damage = data.get('damage', 1)
        
        state.player.lives -= damage
        
        if enemy and enemy in state.enemies:
            state.enemies.remove(enemy)
        
        # ✅ ЗАКОММЕНТИРОВАНА ДЕКАЛЬ ПОПАДАНИЯ
        # if enemy:
        #     state.decals_logic.add_hit_decal(enemy, 'blood_small', 0.5)
        
        if state.player.lives <= 0:
            state.player.lives = 0
            state.game_over = True
            state.audio.play_sound("game_over")
            state.game.state_manager.change_state('GAME_OVER')
    
    def _on_wave_complete(self, data):
        state = self.state
        state.player.stats['waves_survived'] += 1
        state.wave_delay = 3.0

        # Бонус за завершение волны — финансирует апгрейды между волнами
        wave_number = data.get('wave_number', 1)
        bonus = 10 + 2 * wave_number
        state.player.add_gold(bonus)

        state.audio.play_sound("wave_complete")
    
    def _on_tower_shot(self, data):
        state = self.state
        
        tower_id = data.get('tower_id', '')
        target = data.get('target')
        projectile = data.get('projectile')
        tower_x = data.get('tower_x', 0)
        tower_y = data.get('tower_y', 0)
        
        if tower_x and tower_y and target:
            state.decals_logic.add_muzzle_flash(tower_x, tower_y, target, tower_id)
            state.effects_logic.add_muzzle_effect(tower_x, tower_y, tower_id)
        
        # ✅ ЗАКОММЕНТИРОВАНЫ ВСЕ ДЕКАЛИ ПОПАДАНИЯ ОТ ВЫСТРЕЛОВ
        # if target:
        #     decal_type = 'blood_small'
        #     scale = 0.3
        #     
        #     if tower_id == 'water':
        #         decal_type = 'water_splash'
        #         scale = 0.4
        #     elif tower_id == 'freeze':
        #         decal_type = 'ice_crystal'
        #         scale = 0.4
        #     elif tower_id == 'acid':
        #         decal_type = 'acid'
        #         scale = 0.5
        #     elif tower_id == 'rocket':
        #         decal_type = 'crack'
        #         scale = 0.8
        #     elif tower_id == 'sniper':
        #         decal_type = 'blood_small'
        #         scale = 0.25
        #     elif tower_id == 'turret':
        #         decal_type = 'blood_small'
        #         scale = 0.35
        #     elif tower_id == 'flamethrower':
        #         decal_type = 'fire'
        #         scale = 0.5
        #     elif tower_id == 'electric':
        #         decal_type = 'spark'
        #         scale = 0.3
        #     
        #     decal = Decal(target.x, target.y, decal_type, scale=scale)
        #     state.decals.append(decal)
        #     state.effects_logic.add_hit_effect(target, tower_id)
        
        # Звуки
        if tower_id == 'flamethrower':
            pass
        elif tower_id == 'sniper':
            state.audio.play_sound("shoot", volume_override=0.3)
        elif tower_id == 'turret':
            state.audio.play_sound("shoot", volume_override=0.15)
        elif tower_id == 'electric':
            state.audio.play_sound("shoot", volume_override=0.3)
        elif tower_id == 'water':
            # Струя бьёт ~10 раз/сек — звук проигрываем не чаще ~2.5 раз/сек
            import pygame
            now = pygame.time.get_ticks()
            if now - self._water_sound_ticks >= 400:
                self._water_sound_ticks = now
                state.audio.play_sound("water_shoot", volume_override=0.25)
        elif tower_id == 'freeze':
            state.audio.play_sound("freeze_shoot", volume_override=0.25)
            if target:
                state.audio.play_sound("freeze_hit", volume_override=0.2)
        elif tower_id == 'acid':
            state.audio.play_sound("acid_shoot", volume_override=0.25)
            if target:
                state.audio.play_sound("acid_hit", volume_override=0.2)
        elif tower_id == 'rocket':
            state.audio.play_sound("rocket_shoot", volume_override=0.35)
            if target:
                state.audio.play_sound("rocket_hit", volume_override=0.35)
        elif tower_id == 'pvo':
            state.audio.play_sound("pvo_shoot", volume_override=0.2)
        
        if projectile:
            state.projectiles.append(projectile)
    
    def _on_enemy_dodged(self, data):
        state = self.state
        enemy = data.get('enemy')
        state.effects_logic.add_dodge_effect(enemy)
    
    def _on_tower_upgraded(self, data):
        state = self.state
        state.audio.play_sound("tower_build")
        state.feedback_logic.show_success(data['tower'].x, data['tower'].y)
        state.effects_logic.add_hit_effect(data['tower'], 'sniper')
        # ✅ ЗАКОММЕНТИРОВАНА ДЕКАЛЬ
        # state.decals_logic.add_hit_decal(data['tower'], 'spark', 0.6)
    
    def _on_aoe_damage(self, data):
        state = self.state
        center_x, center_y = data['center']
        radius = data['radius']
        damage = data['damage']
        damage_type = data.get('damage_type', 'physical')

        for enemy in state.enemies:
            if not enemy.alive:
                continue
            dist = math.hypot(enemy.x - center_x, enemy.y - center_y)
            if dist <= radius:
                enemy.take_damage(damage, damage_type)
                state.effects_logic.add_hit_effect(enemy, 'rocket')

        state.effects_logic.add_explosion_effect(center_x, center_y)
        state.audio.play_sound("rocket_hit", volume_override=0.4)

    def _on_acid_splash(self, data):
        """AoE кислотного снаряда: урон + эффект кислоты вокруг точки попадания."""
        state = self.state
        center_x, center_y = data['center']
        radius = data['radius']
        damage = data['damage']
        acid_damage = data['acid_damage']
        acid_interval = data['acid_interval']
        acid_duration = data['acid_duration']
        exclude = data.get('exclude')

        for enemy in state.enemies:
            if not enemy.alive or enemy is exclude:
                continue
            dist = math.hypot(enemy.x - center_x, enemy.y - center_y)
            if dist <= radius:
                enemy.take_damage(damage, 'acid')
                if hasattr(enemy, 'apply_acid_effect'):
                    enemy.apply_acid_effect(acid_damage, acid_interval, acid_duration)

    def _on_acid_pool(self, data):
        """Создаёт лужу кислоты на месте попадания снаряда."""
        from entities.acid_pool import AcidPool
        state = self.state
        x, y = data['pos']
        pool = AcidPool(x, y, data['ground_damage'],
                        data['interval'], data['duration'])
        state.acid_pools.append(pool)

    def _on_lightning_effect(self, data):
        state = self.state
        from_pos = data['from']
        to_pos = data['to']
        
        state.lightning_effects.append({
            'from': from_pos,
            'to': to_pos,
            'timer': 0.25,
            'damage': data.get('damage', 0)
        })
        
        # ✅ ЗАКОММЕНТИРОВАНЫ ИСКРЫ
        # from_x, from_y = from_pos
        # to_x, to_y = to_pos
        # 
        # for i in range(3):
        #     t = random.uniform(0.2, 0.8)
        #     x = from_x + (to_x - from_x) * t + random.uniform(-20, 20)
        #     y = from_y + (to_y - from_y) * t + random.uniform(-20, 20)
        #     decal = Decal(x, y, 'spark', scale=0.5)
        #     state.decals.append(decal)
        
        # ✅ ИСПРАВЛЕНО: создаём эффект только если есть координаты
        # Получаем координаты из to_pos
        if to_pos:
            to_x, to_y = to_pos
            effect = HitEffect(to_x, to_y, 'electric')
            state.hit_effects.append(effect)
    
    def _on_chain_lightning_effect(self, data):
        state = self.state
        from_enemy = data['from']
        to_enemy = data['to']
        
        state.lightning_effects.append({
            'from': (from_enemy.x, from_enemy.y),
            'to': (to_enemy.x, to_enemy.y),
            'timer': 0.2,
            'damage': data.get('damage', 0),
            'is_chain': True
        })
        
        # ✅ ЗАКОММЕНТИРОВАНЫ ИСКРЫ
        # x = (from_enemy.x + to_enemy.x) // 2 + random.uniform(-15, 15)
        # y = (from_enemy.y + to_enemy.y) // 2 + random.uniform(-15, 15)
        # decal = Decal(x, y, 'spark', scale=0.4)
        # state.decals.append(decal)
        
        effect = HitEffect(to_enemy.x, to_enemy.y, 'electric')
        state.hit_effects.append(effect)