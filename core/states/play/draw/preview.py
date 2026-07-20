# core/states/play/draw/preview.py
import pygame


class PreviewDraw:
    """Отрисовка превью строительства (башни, ворота, стены)"""

    def __init__(self, state):
        self.state = state

    def draw(self, screen):
        """Рисует превью строительства"""
        state = self.state
        if not state.building_mode and not state.wall_placement_mode:
            return

        ox, oy = state.tile_manager.get_offset()
        tile_size = state.tile_manager.tile_size
        mx, my = pygame.mouse.get_pos()

        converted = state.game._convert_mouse_pos((mx, my))
        if converted is None:
            return
        mx, my = converted

        wx = int((mx - ox) // tile_size)
        wy = int((my - oy) // tile_size)

        if not (0 <= wx < state.tile_manager.map_width and 0 <= wy < state.tile_manager.map_height):
            return

        cell_x = wx * tile_size + ox
        cell_y = wy * tile_size + oy

        if state.wall_placement_mode:
            self._draw_wall_preview(screen, state, wx, wy, cell_x, cell_y, tile_size)
        else:
            self._draw_tower_preview(screen, state, wx, wy, cell_x, cell_y, tile_size)

    def _cell_occupied(self, state, wx, wy):
        return state.towers_logic._is_position_occupied(wx, wy)

    def _draw_cell_highlight(self, screen, cell_x, cell_y, tile_size, can_build):
        """Зелёный/красный квадрат на клетке под курсором"""
        color = (0, 255, 0, 80) if can_build else (255, 0, 0, 80)
        s = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        s.fill(color)
        screen.blit(s, (cell_x, cell_y))

        border_color = (0, 255, 0) if can_build else (255, 0, 0)
        pygame.draw.rect(screen, border_color, (cell_x, cell_y, tile_size, tile_size), 2)

    def _draw_tower_preview(self, screen, state, wx, wy, cell_x, cell_y, tile_size):
        tile = state.tile_manager.map_data[wy][wx]
        can_build = not tile.startswith('road_') and tile not in ('portal', 'castle')
        if can_build and self._cell_occupied(state, wx, wy):
            can_build = False

        self._draw_cell_highlight(screen, cell_x, cell_y, tile_size, can_build)

        # Квадратная зона поражения (сторона 2×range, выровнена по клеткам)
        config = state._get_tower_config(state.selected_tower)
        radius = config.get('range', 200)
        cx = cell_x + tile_size // 2
        cy = cell_y + tile_size // 2

        side = radius * 2
        range_surf = pygame.Surface((side, side), pygame.SRCALPHA)
        range_surf.fill((0, 255, 0, 30))
        screen.blit(range_surf, (cx - radius, cy - radius))
        pygame.draw.rect(screen, (0, 255, 0), (cx - radius, cy - radius, side, side), 1)

        name = state.selected_tower.upper()
        cost = config.get('cost', 100)
        info_text = f"{name} (${cost})"
        text = state.small_font.render(info_text, True, (255, 255, 255))
        screen.blit(text, (cx - text.get_width()//2, cell_y - 30))

    def _draw_wall_preview(self, screen, state, wx, wy, cell_x, cell_y, tile_size):
        """Подсветка клетки для ворот/стены — без зоны поражения"""
        tile = state.tile_manager.map_data[wy][wx]

        if state.selected_wall_type == 'gate':
            can_build = tile.startswith('road_')
            name, cost = 'GATE', 150
        else:
            can_build = tile == 'grass'
            name, cost = 'WALL', 80

        if can_build and self._cell_occupied(state, wx, wy):
            can_build = False

        self._draw_cell_highlight(screen, cell_x, cell_y, tile_size, can_build)

        cx = cell_x + tile_size // 2
        text = state.small_font.render(f"{name} (${cost})", True, (255, 255, 255))
        screen.blit(text, (cx - text.get_width()//2, cell_y - 30))
