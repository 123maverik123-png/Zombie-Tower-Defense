# core/states/map_editor/tools.py
import pygame
from services.resource_loader import ResourceLoader


class MapEditorTools:
    def __init__(self, state):
        self.state = state
        self.available_tiles = [
            'grass', 'road_h', 'road_v', 'road_cross',
            'road_bl', 'road_br', 'road_tl', 'road_tr',
            'portal', 'castle'
        ]

    def load_tile_sprites(self):
        state = self.state
        loader = ResourceLoader()
        tile_files = {
            'grass': 'tile_grass.png',
            'castle': 'tile_castle.png',
            'portal': 'tile_portal.png',
            'road_cross': 'tile_road_cross.png',
            'road_h': 'tile_road_straight_h.png',
            'road_v': 'tile_road_straight_v.png',
            'road_bl': 'tile_road_turn_bottom_left.png',
            'road_br': 'tile_road_turn_bottom_right.png',
            'road_tl': 'tile_road_turn_top_left.png',
            'road_tr': 'tile_road_turn_top_right.png'
        }
        for name, filename in tile_files.items():
            try:
                img = loader.load_image(f"tiles/{filename}")
                if img:
                    state.tile_sprites[name] = img
                else:
                    self._create_fallback_tile(name)
            except:
                self._create_fallback_tile(name)

    def _create_fallback_tile(self, name):
        import pygame
        colors = {
            'grass': (34, 139, 34),
            'castle': (139, 69, 19),
            'portal': (128, 0, 128),
            'road_cross': (150, 150, 150),
            'road_h': (160, 160, 160),
            'road_v': (160, 160, 160),
            'road_bl': (155, 155, 155),
            'road_br': (155, 155, 155),
            'road_tl': (155, 155, 155),
            'road_tr': (155, 155, 155)
        }
        surf = pygame.Surface((64, 64), pygame.SRCALPHA)
        color = colors.get(name, (100, 100, 100))
        surf.fill(color)
        pygame.draw.rect(surf, (200, 200, 200), (0, 0, 63, 63), 2)
        self.state.tile_sprites[name] = surf  # Используем self.state вместо переменной state

    def handle_key(self, event):
        state = self.state
        key = event.key

        if key == pygame.K_ESCAPE:
            if state.show_name_input:
                state.show_name_input = False
                state.pending_overwrite = None
                return
            state.game.state_manager.change_state('MENU')
        elif key == pygame.K_s:
            state.actions.save_map()
        elif key == pygame.K_l:
            state.actions.load_map()
        elif key == pygame.K_n:
            state.actions.new_map()
        elif key == pygame.K_DELETE:
            state.actions.delete_map()
        elif key == pygame.K_e:
            state.draw_mode = 'erase' if state.draw_mode == 'paint' else 'paint'
            state.ui.show_message(f"Mode: {state.draw_mode}")
        elif key == pygame.K_w:
            state.draw_mode = 'waypoint' if state.draw_mode != 'waypoint' else 'paint'
            state.ui.show_message(f"Mode: {state.draw_mode}")
        elif key == pygame.K_h:
            state.show_path = not state.show_path
            state.ui.show_message(f"Path: {'ON' if state.show_path else 'OFF'}")
        elif key == pygame.K_r:
            state.actions.waypoints_to_road()
        elif key == pygame.K_BACKSPACE:
            self.delete_last_waypoint()
        elif key == pygame.K_c:
            self.clear_waypoints()
        elif key == pygame.K_y and state.pending_overwrite:
            state.actions.do_save(state.pending_overwrite)
            state.pending_overwrite = None
        elif key == pygame.K_n and state.pending_overwrite:
            state.pending_overwrite = None
            state.ui.show_message("Overwrite cancelled")
        elif key == pygame.K_RETURN and state.show_name_input:
            state.actions.save_with_name(state.input_name)
        elif key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
                      pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_0]:
            idx = key - pygame.K_1
            if idx >= len(self.available_tiles):
                idx = 9
            self.select_tile(idx)
        elif key == pygame.K_LEFT:
            state.camera_x = max(0, state.camera_x - state.scroll_speed)
        elif key == pygame.K_RIGHT:
            state.camera_x += state.scroll_speed
        elif key == pygame.K_UP:
            state.camera_y = max(0, state.camera_y - state.scroll_speed)
        elif key == pygame.K_DOWN:
            state.camera_y += state.scroll_speed
        elif key == pygame.K_BACKSPACE and state.show_name_input:
            state.input_name = state.input_name[:-1]
        else:
            if state.show_name_input and event.unicode and event.unicode.isprintable():
                state.input_name += event.unicode

    def _get_converted_mouse_pos(self, pos):
        """Получает конвертированные координаты мыши через game._convert_mouse_pos"""
        state = self.state
        if hasattr(state, 'game') and hasattr(state.game, '_convert_mouse_pos'):
            converted = state.game._convert_mouse_pos(pos)
            if converted is not None:
                return converted
        # Fallback: используем координаты как есть (если нет конвертации)
        return pos

    def handle_mouse_down(self, event):
        state = self.state
        # Конвертируем координаты мыши
        mx, my = self._get_converted_mouse_pos(event.pos)

        if event.button == 1:
            # Проверяем клик по UI
            if state.ui.handle_click(mx, my):
                return

            # Рисуем на карте
            if mx > state.ui.panel_width:
                wx, wy = state._screen_to_world((mx, my))
                if 0 <= wx < state.map_width and 0 <= wy < state.map_height:
                    if state.draw_mode == 'waypoint':
                        self.add_waypoint(wx, wy)
                    else:
                        state._place_tile(wx, wy)
                        state.is_dragging = True
                        state.last_draw_pos = (wx, wy)

        elif event.button == 3:
            if mx > state.ui.panel_width:
                wx, wy = state._screen_to_world((mx, my))
                if 0 <= wx < state.map_width and 0 <= wy < state.map_height:
                    if (wx, wy) in state.waypoints and (wx, wy) != state.waypoints[0]:
                        state.waypoints.remove((wx, wy))
                        state.ui.show_message(f"Removed waypoint at ({wx}, {wy})")
                        return
                    if state.map_data[wy][wx] not in ('portal', 'castle'):
                        state.map_data[wy][wx] = 'grass'
                        state.ui.show_message(f"Erased at ({wx}, {wy})")

        elif event.button == 4:
            state.tile_size = min(128, state.tile_size + 5)
        elif event.button == 5:
            state.tile_size = max(30, state.tile_size - 5)

    def handle_mouse_motion(self, event):
        state = self.state
        # Конвертируем координаты мыши
        mx, my = self._get_converted_mouse_pos(event.pos)
        state.mouse_pos = (mx, my)
        
        if state.is_dragging and state.draw_mode != 'waypoint':
            if mx > state.ui.panel_width:
                wx, wy = state._screen_to_world((mx, my))
                if 0 <= wx < state.map_width and 0 <= wy < state.map_height:
                    if (wx, wy) != state.last_draw_pos:
                        state._place_tile(wx, wy)
                        state.last_draw_pos = (wx, wy)

    def handle_mouse_up(self, event):
        state = self.state
        if event.button == 1:
            state.is_dragging = False
            state.last_draw_pos = None

    def select_tile(self, idx):
        state = self.state
        if 0 <= idx < len(self.available_tiles):
            state.selected_tile_index = idx
            state.selected_tile = self.available_tiles[idx]
            state.draw_mode = 'paint'
            state.ui.show_message(f"Selected: {state.selected_tile}")

    def add_waypoint(self, wx, wy):
        state = self.state
        tile = state.map_data[wy][wx]
        if tile != 'grass':
            state.ui.show_message(f"Cannot place waypoint on {tile}!")
            return
        if (wx, wy) in state.waypoints:
            state.ui.show_message("Waypoint already exists!")
            return
        state.waypoints.append((wx, wy))
        state.ui.show_message(f"Waypoint {len(state.waypoints)-1} placed at ({wx}, {wy})")

    def delete_last_waypoint(self):
        state = self.state
        if len(state.waypoints) <= 1:
            state.ui.show_message("Cannot delete start waypoint!")
            return
        removed = state.waypoints.pop()
        state.ui.show_message(f"Removed waypoint at {removed}")

    def clear_waypoints(self):
        state = self.state
        if not state.waypoints:
            state.ui.show_message("No waypoints to clear!")
            return
        start = state.waypoints[0]
        state.waypoints = [start]
        state.ui.show_message(f"Cleared all waypoints except start at {start}")