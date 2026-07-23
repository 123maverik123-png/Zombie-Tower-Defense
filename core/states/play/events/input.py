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
                # Открыть/закрыть консоль по ` (backquote) — не печатается внутрь
                if event.key == pygame.K_BACKQUOTE:
                    state.console.toggle()
                    return
                if state.console.active:
                    if state.console.handle_event(event):
                        return
            
            if state.console.active:
                continue

            # === РЕДАКТОР БАЛАНСА (dev) ===
            if getattr(state, 'balance_editor', None) and state.balance_editor.active:
                state.balance_editor.handle_event(event)
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

    def _handle_mouse_wheel(self, event):
        """Колесо мыши больше не меняет форму стены — она авто по соседям."""
        return
    
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
            elif action == 'repair':
                if state.tower_ui.tower:
                    state.towers_logic.repair_fort(state.tower_ui.tower)
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
        from core.iso import world_to_screen
        for tower in state.towers:
            sx, sy = world_to_screen(tower.x, tower.y)
            tower_rect = pygame.Rect(
                sx + offset_x - tower.width // 2,
                sy + offset_y - tower.height // 2,
                tower.width,
                tower.height
            )
            if tower_rect.collidepoint(pos):
                state.tower_ui.show(tower, (tower.x, tower.y))
                return

        if not state.wall_placement_mode:
            for fort in list(state.gates) + list(state.walls):
                if not fort.alive:
                    continue
                ds = getattr(fort, 'draw_size', max(fort.width, fort.height))
                fsx, fsy = world_to_screen(fort.x, fort.y)
                fort_rect = pygame.Rect(
                    fsx + offset_x - ds // 2,
                    fsy + offset_y - ds // 2,
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