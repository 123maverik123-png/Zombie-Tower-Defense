# core/states/map_editor/ui.py
import pygame


class MapEditorUI:
    def __init__(self, state):
        self.state = state
        self.panel_width = 220
        self.tile_buttons = []
        self.font = pygame.font.Font(None, 20)
        self.small_font = pygame.font.Font(None, 15)
        self.bold_font = pygame.font.Font(None, 24)

        # Кнопки
        self.save_btn = None
        self.load_btn = None
        self.new_btn = None
        self.delete_btn = None
        self.add_wp_btn = None
        self.clear_wp_btn = None
        self.wp_to_road_btn = None
        self.size_x_minus = None
        self.size_x_plus = None
        self.size_y_minus = None
        self.size_y_plus = None

        self._create_buttons()

    def _create_buttons(self):
        state = self.state
        screen_h = state.game.render_height

        self.save_btn = pygame.Rect(10, screen_h - 250, 200, 32)
        self.load_btn = pygame.Rect(10, screen_h - 215, 200, 32)
        self.new_btn = pygame.Rect(10, screen_h - 180, 200, 32)
        self.delete_btn = pygame.Rect(10, screen_h - 145, 200, 32)

        self.add_wp_btn = pygame.Rect(10, screen_h - 105, 95, 28)
        self.clear_wp_btn = pygame.Rect(115, screen_h - 105, 95, 28)
        self.wp_to_road_btn = pygame.Rect(10, screen_h - 70, 200, 28)

        self.size_x_minus = pygame.Rect(10, screen_h - 300, 30, 28)
        self.size_x_plus = pygame.Rect(90, screen_h - 300, 30, 28)
        self.size_y_minus = pygame.Rect(140, screen_h - 300, 30, 28)
        self.size_y_plus = pygame.Rect(220, screen_h - 300, 30, 28)

    def create_tile_buttons(self):
        self.tile_buttons = []
        y = 60
        for i, tile_name in enumerate(self.state.tools.available_tiles):
            btn = pygame.Rect(10, y, 60, 60)
            self.tile_buttons.append((btn, tile_name, i))
            y += 66

    def handle_click(self, mx, my):
        state = self.state

        # Проверяем кнопки тайлов
        for btn, tile_name, idx in self.tile_buttons:
            if btn.collidepoint(mx, my):
                state.tools.select_tile(idx)
                return True

        # Проверяем кнопки действий
        if self.save_btn.collidepoint(mx, my):
            state.actions.save_map()
            return True
        if self.load_btn.collidepoint(mx, my):
            state.actions.load_map()
            return True
        if self.new_btn.collidepoint(mx, my):
            state.actions.new_map()
            return True
        if self.delete_btn.collidepoint(mx, my):
            state.actions.delete_map()
            return True

        if self.add_wp_btn.collidepoint(mx, my):
            state.draw_mode = 'waypoint'
            state.ui.show_message("Waypoint mode: click on map to add waypoints")
            return True
        if self.clear_wp_btn.collidepoint(mx, my):
            state.tools.clear_waypoints()
            return True
        if self.wp_to_road_btn.collidepoint(mx, my):
            state.actions.waypoints_to_road()
            return True

        if self.size_x_minus.collidepoint(mx, my):
            state.actions.change_map_size(-1, 0)
            return True
        if self.size_x_plus.collidepoint(mx, my):
            state.actions.change_map_size(1, 0)
            return True
        if self.size_y_minus.collidepoint(mx, my):
            state.actions.change_map_size(0, -1)
            return True
        if self.size_y_plus.collidepoint(mx, my):
            state.actions.change_map_size(0, 1)
            return True

        return False

    def show_message(self, msg):
        state = self.state
        state.message = msg
        state.message_timer = 120