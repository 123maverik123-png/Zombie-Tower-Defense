# core/states/map_editor/draw.py
import pygame


class MapEditorDraw:
    def __init__(self, state):
        self.state = state

    def draw_scene(self, renderer):
        """GPU-сцена редактора: фон и тайлы карты"""
        state = self.state
        batch = renderer.batch
        offset_x = state.ui.panel_width

        # Фон
        batch.draw_rect(0, 0, state.game.render_width, state.game.render_height,
                        (30, 30, 50, 255))

        for y in range(state.map_height):
            for x in range(state.map_width):
                tile_name = state.map_data[y][x]
                px = x * state.tile_size - state.camera_x + offset_x
                py = y * state.tile_size - state.camera_y

                if tile_name in state.tile_sprites:
                    atlas_name = f"edtile_{tile_name}"
                    if not renderer.has_texture(atlas_name):
                        renderer.load_texture(atlas_name, state.tile_sprites[tile_name])
                    region = renderer.get_region(atlas_name)
                    batch.draw(region, px, py, state.tile_size, state.tile_size,
                               centered=False)
                else:
                    color_map = {
                        'grass': (34, 139, 34),
                        'castle': (139, 69, 19),
                        'portal': (128, 0, 128),
                        'road_h': (160, 160, 160),
                        'road_v': (160, 160, 160),
                        'road_cross': (150, 150, 150),
                        'road_bl': (155, 155, 155),
                        'road_br': (155, 155, 155),
                        'road_tl': (155, 155, 155),
                        'road_tr': (155, 155, 155)
                    }
                    color = color_map.get(tile_name, (255, 0, 255))
                    batch.draw_rect(px, py, state.tile_size, state.tile_size,
                                    (*color, 255))

    def draw(self, screen):
        state = self.state

        self._draw_panel(screen)
        self._draw_fallback_tile_labels(screen)
        self._draw_waypoints(screen)
        self._draw_highlight(screen)
        self._draw_message(screen)
        self._draw_name_input(screen)
        self._draw_bottom_panel(screen)
        self._draw_statistics(screen)

    def _draw_fallback_tile_labels(self, screen):
        """Буквы P/C на клетках портала/замка без спрайтов (текст — на оверлее)"""
        state = self.state
        offset_x = state.ui.panel_width
        small_font = pygame.font.Font(None, 12)

        for y in range(state.map_height):
            for x in range(state.map_width):
                tile_name = state.map_data[y][x]
                if tile_name in state.tile_sprites:
                    continue
                if tile_name not in ('portal', 'castle'):
                    continue
                rect = pygame.Rect(
                    x * state.tile_size - state.camera_x + offset_x,
                    y * state.tile_size - state.camera_y,
                    state.tile_size, state.tile_size
                )
                label = "P" if tile_name == 'portal' else "C"
                text = small_font.render(label, True, (255, 255, 255))
                screen.blit(text, (rect.x + rect.width//2 - 4, rect.y + rect.height//2 - 6))

    def _draw_panel(self, screen):
        state = self.state
        panel_rect = pygame.Rect(0, 0, state.ui.panel_width, state.game.render_height)
        pygame.draw.rect(screen, (40, 40, 60), panel_rect)
        pygame.draw.rect(screen, (80, 80, 100), panel_rect, 2)

        font = state.ui.font
        small_font = state.ui.small_font

        title = font.render("MAP EDITOR", True, (255, 200, 50))
        screen.blit(title, (10, 10))
        title2 = small_font.render("1-9,0: tiles", True, (200, 200, 200))
        screen.blit(title2, (10, 32))
        title3 = small_font.render("W: waypoints | E: erase | H: path", True, (200, 200, 200))
        screen.blit(title3, (10, 50))

        # Тайлы
        for btn, tile_name, idx in state.ui.tile_buttons:
            color = (60, 60, 80)
            if idx == state.selected_tile_index and state.draw_mode != 'waypoint':
                color = (100, 150, 255)
            pygame.draw.rect(screen, color, btn)
            pygame.draw.rect(screen, (200, 200, 200), btn, 2)

            if tile_name in state.tile_sprites:
                sprite = state.tile_sprites[tile_name]
                scaled = pygame.transform.scale(sprite, (56, 56))
                screen.blit(scaled, (btn.x + 2, btn.y + 2))
            else:
                text = small_font.render(tile_name.replace('_', ' '), True, (255, 255, 255))
                screen.blit(text, (btn.x + 5, btn.y + 20))

            num_font = pygame.font.Font(None, 14)
            num_text = num_font.render(str(idx + 1), True, (255, 255, 255))
            screen.blit(num_text, (btn.x + 2, btn.y + 2))

        # Кнопки размера
        for btn in [state.ui.size_x_minus, state.ui.size_x_plus,
                     state.ui.size_y_minus, state.ui.size_y_plus]:
            pygame.draw.rect(screen, (60, 60, 100), btn)
            pygame.draw.rect(screen, (150, 150, 200), btn, 2)

        font18 = pygame.font.Font(None, 18)
        screen.blit(font18.render("-", True, (255, 255, 255)), (22, state.ui.size_x_minus.y + 6))
        screen.blit(font18.render("+", True, (255, 255, 255)), (100, state.ui.size_x_plus.y + 6))
        screen.blit(font18.render("-", True, (255, 255, 255)), (152, state.ui.size_y_minus.y + 6))
        screen.blit(font18.render("+", True, (255, 255, 255)), (230, state.ui.size_y_plus.y + 6))

        size_text = small_font.render(f"{state.map_width}x{state.map_height}", True, (255, 255, 255))
        screen.blit(size_text, (50, state.ui.size_x_minus.y + 4))

        # Кнопки действий
        for btn, label, color in [
            (state.ui.save_btn, "SAVE (S)", (0, 150, 0)),
            (state.ui.load_btn, "LOAD (L)", (50, 100, 200)),
            (state.ui.new_btn, "NEW (N)", (200, 150, 50)),
            (state.ui.delete_btn, "DELETE (Del)", (200, 50, 50))
        ]:
            pygame.draw.rect(screen, color, btn)
            pygame.draw.rect(screen, (255, 255, 255), btn, 2)
            text = small_font.render(label, True, (255, 255, 255))
            screen.blit(text, (btn.x + 10, btn.y + 6))

        # Кнопки WAYPOINTS
        wp_color = (100, 200, 100) if state.draw_mode == 'waypoint' else (60, 100, 60)
        pygame.draw.rect(screen, wp_color, state.ui.add_wp_btn)
        pygame.draw.rect(screen, (255, 255, 255), state.ui.add_wp_btn, 2)
        text = small_font.render("ADD WP (W)", True, (255, 255, 255))
        screen.blit(text, (state.ui.add_wp_btn.x + 5, state.ui.add_wp_btn.y + 6))

        pygame.draw.rect(screen, (100, 60, 60), state.ui.clear_wp_btn)
        pygame.draw.rect(screen, (255, 255, 255), state.ui.clear_wp_btn, 2)
        text = small_font.render("CLEAR (C)", True, (255, 255, 255))
        screen.blit(text, (state.ui.clear_wp_btn.x + 10, state.ui.clear_wp_btn.y + 6))

        pygame.draw.rect(screen, (200, 150, 50), state.ui.wp_to_road_btn)
        pygame.draw.rect(screen, (255, 255, 255), state.ui.wp_to_road_btn, 2)
        text = small_font.render("WP → ROAD (R)", True, (255, 255, 255))
        screen.blit(text, (state.ui.wp_to_road_btn.x + 15, state.ui.wp_to_road_btn.y + 6))

    def _draw_waypoints(self, screen):
        state = self.state
        offset_x = state.ui.panel_width

        if state.waypoints and state.show_path:
            for i in range(len(state.waypoints) - 1):
                x1, y1 = state.waypoints[i]
                x2, y2 = state.waypoints[i + 1]
                px1 = x1 * state.tile_size - state.camera_x + offset_x + state.tile_size // 2
                py1 = y1 * state.tile_size - state.camera_y + state.tile_size // 2
                px2 = x2 * state.tile_size - state.camera_x + offset_x + state.tile_size // 2
                py2 = y2 * state.tile_size - state.camera_y + state.tile_size // 2
                pygame.draw.line(screen, (255, 255, 0, 180), (px1, py1), (px2, py2), 4)

            for idx, (x, y) in enumerate(state.waypoints):
                px = x * state.tile_size - state.camera_x + offset_x + state.tile_size // 2
                py = y * state.tile_size - state.camera_y + state.tile_size // 2

                if idx == 0:
                    color = (0, 255, 0)
                    radius = 10
                elif idx == len(state.waypoints) - 1:
                    color = (255, 0, 0)
                    radius = 10
                else:
                    color = (255, 255, 0)
                    radius = 8

                pygame.draw.circle(screen, color, (int(px), int(py)), radius)
                pygame.draw.circle(screen, (255, 255, 255), (int(px), int(py)), radius, 2)

                num_font = pygame.font.Font(None, 16)
                num_text = num_font.render(str(idx), True, (255, 255, 255))
                screen.blit(num_text, (int(px) + 12, int(py) - 8))

    def _draw_highlight(self, screen):
        state = self.state
        offset_x = state.ui.panel_width
        mx, my = state.mouse_pos

        if mx > state.ui.panel_width:
            wx, wy = state._screen_to_world((mx, my))
            if 0 <= wx < state.map_width and 0 <= wy < state.map_height:
                rect = pygame.Rect(
                    wx * state.tile_size - state.camera_x + offset_x,
                    wy * state.tile_size - state.camera_y,
                    state.tile_size, state.tile_size
                )
                if state.draw_mode == 'waypoint':
                    if (wx, wy) not in state.waypoints:
                        pygame.draw.rect(screen, (0, 255, 0, 80), rect, 3)
                    else:
                        pygame.draw.rect(screen, (255, 200, 0, 80), rect, 3)
                else:
                    pygame.draw.rect(screen, (255, 255, 0, 80), rect, 3)

    def _draw_message(self, screen):
        state = self.state
        if state.message_timer > 0:
            font = pygame.font.Font(None, 28)
            text = font.render(state.message, True, (255, 255, 100))
            text_rect = text.get_rect(center=(state.game.render_width // 2, state.game.render_height - 100))
            bg_rect = text_rect.inflate(20, 10)
            pygame.draw.rect(screen, (0, 0, 0, 200), bg_rect)
            pygame.draw.rect(screen, (150, 150, 200), bg_rect, 2)
            screen.blit(text, text_rect)

    def _draw_name_input(self, screen):
        state = self.state
        if not state.show_name_input:
            return

        dialog_rect = pygame.Rect(state.game.render_width//2 - 200, state.game.render_height//2 - 60, 400, 120)
        pygame.draw.rect(screen, (40, 40, 60), dialog_rect)
        pygame.draw.rect(screen, (150, 150, 200), dialog_rect, 3)

        font = pygame.font.Font(None, 28)
        label = font.render("Enter map name:", True, (255, 255, 255))
        screen.blit(label, (dialog_rect.x + 20, dialog_rect.y + 15))

        input_rect = pygame.Rect(dialog_rect.x + 20, dialog_rect.y + 50, 360, 35)
        pygame.draw.rect(screen, (60, 60, 80), input_rect)
        pygame.draw.rect(screen, (200, 200, 200), input_rect, 2)

        name_text = font.render(state.input_name + "|", True, (255, 255, 255))
        screen.blit(name_text, (input_rect.x + 10, input_rect.y + 5))

        hint = state.ui.small_font.render("Enter: save | ESC: cancel", True, (200, 200, 200))
        screen.blit(hint, (dialog_rect.x + 20, dialog_rect.y + 95))

    def _draw_bottom_panel(self, screen):
        state = self.state
        bottom_y = state.game.render_height - 30
        bg_rect = pygame.Rect(0, bottom_y, state.game.render_width, 30)
        pygame.draw.rect(screen, (0, 0, 0, 220), bg_rect)
        pygame.draw.rect(screen, (80, 80, 100), bg_rect, 2)

        hints = [
            f"Tile: {state.selected_tile}",
            f"Mode: {state.draw_mode.upper()}",
            f"WP: {len(state.waypoints)}",
            f"Size: {state.map_width}x{state.map_height}",
            "LMB: Place/WP",
            "RMB: Erase/Delete WP",
            "W: WP mode | R: WP→Road",
            "Backspace: Delete last WP"
        ]

        x_offset = 10
        small_font = state.ui.small_font
        for hint in hints:
            text = small_font.render(hint, True, (200, 200, 200))
            screen.blit(text, (x_offset, bottom_y + 7))
            x_offset += text.get_width() + 15

    def _draw_statistics(self, screen):
        state = self.state
        # ✅ Используем метод из actions
        stats = state.actions._get_tile_statistics()
        stats_text = " | ".join([f"{k}:{v}" for k, v in sorted(stats.items()) if v > 0])
        if stats_text:
            stat_surface = state.ui.small_font.render(stats_text[:60], True, (150, 200, 150))
            screen.blit(stat_surface, (state.ui.panel_width + 10, state.game.render_height - 60))