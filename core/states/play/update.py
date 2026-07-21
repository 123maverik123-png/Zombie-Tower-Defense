# core/states/play/update.py
import pygame
from entities.projectile import Projectile


class PlayUpdate:
    def __init__(self, state):
        self.state = state

    def update(self, dt):
        state = self.state
        dt *= state.game_speed

        if state.god_mode:
            self._update_god(dt)
            return

        if state.frozen:
            self._update_frozen(dt)
            return

        self._update_normal(dt)

    def _convert_mouse_pos(self, pos):
        """
        Конвертирует координаты мыши в систему render_surface.
        Используется для обновления mouse_pos.
        """
        state = self.state
        if hasattr(state, 'game') and hasattr(state.game, '_convert_mouse_pos'):
            converted = state.game._convert_mouse_pos(pos)
            if converted is not None:
                return converted
        return pos

    def _update_common(self, dt):
        state = self.state

        # ✅ ОБНОВЛЯЕМ С ЧАСТОТОЙ КАЖДЫЙ КАДР (это критично для игры)
        state.effects_logic.update(dt)
        state.decals_logic.update(dt)
        state.feedback_logic.update(dt)
        if hasattr(state, 'tutorial'):
            state.tutorial.update(dt)
        if hasattr(state, 'torch_layer'):
            state.torch_layer.update(dt)

        self._update_waves(dt)
        self._update_towers(dt)
        self._update_projectiles(dt)
        self._update_lightning_effects(dt)

        # Очистка мертвых врагов
        if hasattr(state, 'enemies_logic') and hasattr(state.enemies_logic, 'clear_dead_bodies'):
            state.enemies_logic.clear_dead_bodies()
        else:
            state.enemies = [e for e in state.enemies if e.alive]

        # Очистка разрушенных стен/ворот — иначе их клетки остаются "заняты"
        walls_before = len(state.walls)
        gates_before = len(state.gates)
        state.walls = [w for w in state.walls if w.alive]
        state.gates = [g for g in state.gates if g.alive]
        if (len(state.walls) != walls_before or len(state.gates) != gates_before):
            if hasattr(state, 'towers_logic'):
                state.towers_logic._reorient_walls()  # соседи пересчитывают форму

        # ✅ Конвертируем координаты мыши
        mouse_pos = pygame.mouse.get_pos()
        converted = self._convert_mouse_pos(mouse_pos)
        if converted is not None:
            state.mouse_pos = converted
        else:
            state.mouse_pos = mouse_pos
        
        # Проверяем состояние игры
        if hasattr(state, '_check_game_over'):
            state._check_game_over()
        if hasattr(state, '_check_victory'):
            state._check_victory()
        if hasattr(state, '_check_music'):
            state._check_music()

    def _update_god(self, dt):
        self._update_common(dt)

    def _update_frozen(self, dt):
        self._update_common(dt)

    def _update_normal(self, dt):
        state = self.state
        # ✅ Используем enemies_logic для обновления врагов
        if hasattr(state, 'enemies_logic') and hasattr(state.enemies_logic, 'update'):
            state.enemies_logic.update(dt)
        else:
            # Если enemies_logic нет, обновляем врагов вручную
            for enemy in state.enemies:
                enemy.update(dt)
        self._update_common(dt)

    # ===== ВОЛНЫ =====
    def _update_waves(self, dt):
        state = self.state

        if state.wave_manager.is_all_waves_complete():
            if hasattr(state, '_check_victory'):
                state._check_victory()
            return

        new_enemy = state.wave_manager.update(dt)
        if new_enemy:
            state.enemies.append(new_enemy)

        if state.wave_manager.is_wave_complete():
            next_index = state.wave_manager.current_wave_index + 1
            if next_index >= len(state.wave_data):
                state.wave_manager.all_waves_complete = True
                print(f"🏁 All waves complete! (total: {len(state.wave_data)})")
                if hasattr(state, '_check_victory'):
                    state._check_victory()
                return

            state.wave_manager.current_wave_index = next_index
            state.wave_manager.start_next_wave()
            state.audio.play_sound("wave_complete")

    # ===== ТАУЭРЫ =====
    def _update_towers(self, dt):
        state = self.state
        enemies = [e for e in state.enemies if e.alive]
        
        # ✅ ОБНОВЛЯЕМ БАШНИ С ОГРАНИЧЕНИЕМ
        for tower in state.towers:
            result = tower.update(dt, enemies)
            if result:
                if isinstance(result, bool) and result:
                    continue
                if isinstance(result, Projectile):
                    state.projectiles.append(result)

    # ===== СНАРЯДЫ =====
    def _update_projectiles(self, dt):
        state = self.state
        for proj in state.projectiles[:]:
            proj.update(dt)
            if not proj.alive:
                state.projectiles.remove(proj)

    # ===== МОЛНИИ =====
    def _update_lightning_effects(self, dt):
        state = self.state
        for effect in state.lightning_effects[:]:
            effect['timer'] -= dt
            if effect['timer'] <= 0:
                state.lightning_effects.remove(effect)