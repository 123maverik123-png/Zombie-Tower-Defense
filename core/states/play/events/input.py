# core/states/play/events/input.py
import pygame
from core.event_bus import EventBus


class InputEvents:
    """Обработка пользовательского ввода (мышь, клавиатура)"""
    
    def __init__(self, state):
        self.state = state
    
    def handle(self, events):
        state = self.state
        
        for event in events:
            # === КОНСОЛЬ ===
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and not state.console.active:
                    state.console.toggle()
                    return
                if state.console.active:
                    if state.console.handle_event(event):
                        return
            
            if state.console.active:
                continue
            
            # === КЛАВИАТУРА ===
            if event.type == pygame.KEYDOWN:
                self._handle_key(event.key)
            
            # === МЫШЬ ===
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_down(event)

            elif event.type == pygame.MOUSEWHEEL:
                self._handle_mouse_wheel(event)

            elif event.type == pygame.MOUSEMOTION:
                self._handle_mouse_motion(event)
            
            # === КАМЕРА ===
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
                self._start_camera_drag(event)
            
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 2:
                self._stop_camera_drag()
            
            elif event.type == pygame.MOUSEMOTION and hasattr(state, 'camera_dragging') and state.camera_dragging:
                self._handle_camera_drag(event)
    
    def _handle_key(self, key):
        state = self.state
        
        if key == pygame.K_ESCAPE:
            state.game.state_manager.change_state('PAUSED')
        
        elif key == pygame.K_1:
            self._select_tower_by_index(0)
        elif key == pygame.K_2:
            self._select_tower_by_index(1)
        elif key == pygame.K_3:
            self._select_tower_by_index(2)
        elif key == pygame.K_4:
            self._select_tower_by_index(3)
        elif key == pygame.K_5:
            self._select_tower_by_index(4)
        elif key == pygame.K_6:
            self._select_tower_by_index(5)
        elif key == pygame.K_7:
            self._select_tower_by_index(6)
        elif key == pygame.K_8:
            self._select_tower_by_index(7)
        elif key == pygame.K_9:
            self._select_tower_by_index(8)
        
        elif key == pygame.K_g:
            self._toggle_wall_mode()

        elif key == pygame.K_r:
            self._cycle_wall_variant()

    def _cycle_wall_variant(self):
        """Переключает форму стены по кругу (только для типа 'wall')."""
        state = self.state
        if not state.wall_placement_mode or state.selected_wall_type != 'wall':
            return
        from entities.wall import WALL_VARIANTS
        cur = getattr(state, 'selected_wall_variant', 'h')
        idx = (WALL_VARIANTS.index(cur) + 1) % len(WALL_VARIANTS) if cur in WALL_VARIANTS else 0
        state.selected_wall_variant = WALL_VARIANTS[idx]
        state.audio.play_sound("button_click", volume_override=0.3)

    def _handle_mouse_wheel(self, event):
        """Колесо в режиме строительства: крутит форму стены / ориентацию ворот."""
        state = self.state
        if not state.wall_placement_mode:
            return
        step = 1 if event.y > 0 else -1
        if state.selected_wall_type == 'wall':
            from entities.wall import WALL_VARIANTS
            cur = getattr(state, 'selected_wall_variant', 'h')
            idx = WALL_VARIANTS.index(cur) if cur in WALL_VARIANTS else 0
            state.selected_wall_variant = WALL_VARIANTS[(idx + step) % len(WALL_VARIANTS)]
        else:  # gate — ручной оверрайд авто-ориентации
            cur = getattr(state, 'gate_orientation_override', None)
            # None(авто) -> h -> v -> None по кругу
            cycle = [None, 'h', 'v']
            idx = cycle.index(cur) if cur in cycle else 0
            state.gate_orientation_override = cycle[(idx + step) % len(cycle)]
        state.audio.play_sound("button_click", volume_override=0.3)
    
    def _select_tower_by_index(self, index):
        state = self.state
        if index < len(state.ui_logic.tower_buttons):
            btn = state.ui_logic.tower_buttons[index]
            if btn.get('is_unlocked', True):
                state.ui_logic.handle_tower_panel_click(btn['rect'].center)
            else:
                state.feedback_logic.show_error(0, 0, f"Unlocked at level {btn.get('unlock_level', 1)}!")
    
    def _toggle_wall_mode(self):
        state = self.state
        
        if state.level_number < 5:
            state.feedback_logic.show_error(0, 0, "Walls unlocked at level 5!")
            return
        
        if state.wall_placement_mode:
            state.wall_placement_mode = False
            state.building_mode = False
            state.audio.play_sound("button_click")
            print("🏗️ Wall placement mode: OFF")
        else:
            state.wall_placement_mode = True
            state.selected_wall_type = 'gate'
            state.building_mode = False
            state.audio.play_sound("button_click")
            print("🏗️ Wall placement mode: ON (Gate)")
            print("   Press G again to switch between Gate and Wall")
            print("   Click on road for Gate, on grass for Wall")
    
    def _handle_mouse_down(self, event):
        state = self.state
        pos = event.pos
        
        if event.button == 1:
            self._handle_left_click(pos)
        elif event.button == 3:
            if state.wall_placement_mode:
                state.wall_placement_mode = False
                state.audio.play_sound("button_click")
                print("🏗️ Wall placement mode: OFF")
                return
            
            state.building_mode = not state.building_mode
            if state.building_mode:
                state.audio.play_sound("button_click")
            else:
                state.tower_ui.hide()
    
    def _handle_left_click(self, pos):
        state = self.state
        
        # 1. Проверяем клик по UI башни
        if state.tower_ui.active:
            action = state.tower_ui.handle_click(pos)
            if action == 'upgrade':
                if state.tower_ui.tower:
                    state.towers_logic.upgrade_tower(state.tower_ui.tower)
                return
            elif action == 'sell':
                if state.tower_ui.tower:
                    state.towers_logic.sell_tower(state.tower_ui.tower)
                return
            elif action is None:
                state.tower_ui.hide()
        
        # 2. Проверяем клик по панели башен
        tower_clicked = state.ui_logic.handle_tower_panel_click(pos)
        if tower_clicked:
            return
        
        # 3. Проверяем клик по башне на карте
        offset_x, offset_y = state.tile_manager.get_offset()
        # Примечание: pos уже в координатах render_surface
        for tower in state.towers:
            tower_rect = pygame.Rect(
                tower.x + offset_x - tower.width // 2,
                tower.y + offset_y - tower.height // 2,
                tower.width,
                tower.height
            )
            if tower_rect.collidepoint(pos):
                state.tower_ui.show(tower, (tower.x, tower.y))
                return

        # 3b. Клик по стене/воротам — то же меню улучшения/продажи.
        # Не в режиме строительства, чтобы не мешать постройке.
        if not state.wall_placement_mode:
            for fort in list(state.gates) + list(state.walls):
                ds = getattr(fort, 'draw_size', max(fort.width, fort.height))
                fort_rect = pygame.Rect(
                    fort.x + offset_x - ds // 2,
                    fort.y + offset_y - ds // 2,
                    ds, ds
                )
                if fort_rect.collidepoint(pos):
                    state.tower_ui.show(fort, (fort.x, fort.y))
                    return
        
        # 4. Если кликнули по пустому месту — скрываем UI
        state.tower_ui.hide()
        
        # 5. ✅ Обрабатываем клик по карте (встроенная логика)
        if state.wall_placement_mode:
            state.towers_logic.build_wall(pos)
            return
        
        if state.building_mode:
            state.towers_logic.build(pos)
        else:
            # Просто клик по карте (выбор башни уже обработан выше)
            pass
    
    def _handle_mouse_motion(self, event):
        state = self.state
        if state.tower_ui.active:
            state.tower_ui.handle_hover(event.pos)
    
    def _start_camera_drag(self, event):
        state = self.state
        state.camera_dragging = True
        state.camera_drag_start = event.pos
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZEALL)
    
    def _stop_camera_drag(self):
        state = self.state
        state.camera_dragging = False
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
    
    def _handle_camera_drag(self, event):
        state = self.state
        dx = event.pos[0] - state.camera_drag_start[0]
        dy = event.pos[1] - state.camera_drag_start[1]
        state.tile_manager.camera_x -= dx
        state.tile_manager.camera_y -= dy
        state.camera_drag_start = event.pos