# core/states/map_editor/state.py
import pygame
from core.state_manager import State
from core.audio import AudioManager
from .ui import MapEditorUI
from .tools import MapEditorTools
from .actions import MapEditorActions
from .draw import MapEditorDraw


class MapEditorState(State):
    def __init__(self, game):
        super().__init__(game)
        self.audio = AudioManager()
        self.game = game

        # === ПАРАМЕТРЫ КАРТЫ ===
        self.map_width = 20
        self.map_height = 14
        self.tile_size = 65
        self.map_data = [['grass' for _ in range(self.map_width)] for _ in range(self.map_height)]

        # === ВСПОМОГАТЕЛЬНЫЕ ДАННЫЕ ===
        self.waypoints = []
        self.map_name = "custom_level"
        self.message = ""
        self.message_timer = 0
        self.show_name_input = False
        self.input_name = ""
        self.pending_overwrite = None
        self.selected_tile_index = 0
        self.selected_tile = 'grass'
        self.draw_mode = 'paint'
        self.show_path = True

        # === КАМЕРА ===
        self.camera_x = 0
        self.camera_y = 0
        self.scroll_speed = 20

        # === СОСТОЯНИЕ МЫШИ ===
        self.mouse_pos = (0, 0)
        self.is_dragging = False
        self.last_draw_pos = None

        # === ИНИЦИАЛИЗАЦИЯ ===
        self._init_waypoints_from_portal()

        # === ПОДСИСТЕМЫ ===
        self.ui = MapEditorUI(self)
        self.tools = MapEditorTools(self)
        self.actions = MapEditorActions(self)
        self.drawer = MapEditorDraw(self)

        # Загрузка тайлов
        self.tile_sprites = {}
        self.tools.load_tile_sprites()
        self.ui.create_tile_buttons()

        self.screen_width = self.game.render_width
        self.screen_height = self.game.render_height

    def _init_waypoints_from_portal(self):
        self.waypoints = []
        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.map_data[y][x] == 'portal':
                    self.waypoints.append((x, y))
        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.map_data[y][x] == 'castle':
                    if (x, y) not in self.waypoints:
                        self.waypoints.append((x, y))
                    break

    def _convert_mouse_pos(self, pos):
        """
        Конвертирует координаты мыши в систему render_surface.
        Используется для преобразования перед вызовом _screen_to_world.
        """
        if hasattr(self, 'game') and hasattr(self.game, '_convert_mouse_pos'):
            converted = self.game._convert_mouse_pos(pos)
            if converted is not None:
                return converted
        return pos

    def _screen_to_world(self, pos):
        """
        Конвертирует экранные координаты в координаты карты.
        Использует round() для правильного округления.
        """
        x, y = pos
        x -= self.ui.panel_width
        # ✅ Используем round для правильного округления при работе с float
        return int(round((x + self.camera_x) / self.tile_size)), int(round((y + self.camera_y) / self.tile_size))

    def _world_to_screen(self, world_x, world_y):
        """Конвертирует координаты карты в экранные"""
        return world_x * self.tile_size - self.camera_x + self.ui.panel_width, world_y * self.tile_size - self.camera_y

    def _place_tile(self, wx, wy):
        """Размещает тайл на карте"""
        if self.draw_mode == 'erase':
            if self.map_data[wy][wx] not in ('portal', 'castle'):
                self.map_data[wy][wx] = 'grass'
                if self.waypoints and self.waypoints[0] == (wx, wy):
                    self.waypoints = []
            return

        if self.draw_mode == 'waypoint':
            return

        current = self.map_data[wy][wx]

        if current in ('portal', 'castle') and self.selected_tile not in ('portal', 'castle'):
            self.ui.show_message("Cannot overwrite portal or castle!")
            return

        if self.selected_tile == 'castle':
            for y in range(self.map_height):
                for x in range(self.map_width):
                    if self.map_data[y][x] == 'castle' and (x != wx or y != wy):
                        self.ui.show_message("Castle already exists!")
                        return

        if self.selected_tile == 'portal':
            count = sum(1 for row in self.map_data for cell in row if cell == 'portal')
            if count >= 3 and self.map_data[wy][wx] != 'portal':
                self.ui.show_message("Maximum 3 portals allowed!")
                return

        self.map_data[wy][wx] = self.selected_tile

        if self.selected_tile == 'portal':
            if (wx, wy) not in self.waypoints:
                if not self.waypoints:
                    self.waypoints = [(wx, wy)]
                else:
                    self.waypoints.insert(0, (wx, wy))
                self.ui.show_message(f"Portal placed at ({wx}, {wy}) — waypoint added!")
        elif self.selected_tile == 'castle':
            if self.waypoints:
                if self.waypoints[-1] != (wx, wy):
                    self.waypoints.append((wx, wy))
            else:
                self.waypoints = [(wx, wy)]
            self.ui.show_message(f"Castle placed at ({wx}, {wy}) — end waypoint set!")
        else:
            self.ui.show_message(f"Placed {self.selected_tile} at ({wx}, {wy})")

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                self.tools.handle_key(event)
            if self.show_name_input or self.pending_overwrite:
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                self.tools.handle_mouse_down(event)
            if event.type == pygame.MOUSEMOTION:
                self.tools.handle_mouse_motion(event)
            if event.type == pygame.MOUSEBUTTONUP:
                self.tools.handle_mouse_up(event)

        if self.message_timer > 0:
            self.message_timer -= 1

    def update(self, dt):
        pass

    def draw(self, screen):
        self.drawer.draw(screen)

    def draw_scene(self, renderer):
        self.drawer.draw_scene(renderer)

    def on_resolution_changed(self, screen_w, screen_h):
        pass