# core/states/play/draw/preview.py
import pygame

from core.iso import world_to_screen


class PreviewDraw:
    """Отрисовка превью строительства (башни, ворота, стены)"""

    def __init__(self, state):
        self.state = state

    def draw(self, screen):
        """Рисует превью строительства"""
        state = self.state
        if not state.building_mode and not state.wall_placement_mode:
            return

        tile_size = state.tile_manager.tile_size
        mx, my = pygame.mouse.get_pos()

        converted = state.game._convert_mouse_pos((mx, my))
        if converted is None:
            return
        mx, my = converted

        wx, wy = state.tile_manager.get_grid_position(mx, my)

        if not (0 <= wx < state.tile_manager.map_width and 0 <= wy < state.tile_manager.map_height):
            return

        # Центр клетки на экране (та же изопроекция, что и в draw.py)
        ox, oy = state.tile_manager.get_offset()
        world_cx = (wx + 0.5) * tile_size
        world_cy = (wy + 0.5) * tile_size
        sx, sy = world_to_screen(world_cx, world_cy)
        cx = sx + ox
        cy = sy + oy

        if state.wall_placement_mode:
            self._draw_wall_preview(screen, state, wx, wy, cx, cy, tile_size)
        else:
            self._draw_tower_preview(screen, state, wx, wy, cx, cy, tile_size)

    def _cell_occupied(self, state, wx, wy):
        return state.towers_logic._is_position_occupied(wx, wy)

    def _draw_cell_highlight(self, screen, cx, cy, tile_size, can_build):
        """Зелёный/красный ромб на клетке под курсором (совпадает с формой изо-тайла)"""
        iso_w, iso_h = tile_size, tile_size * 0.5
        points = [
            (cx, cy - iso_h / 2),
            (cx + iso_w / 2, cy),
            (cx, cy + iso_h / 2),
            (cx - iso_w / 2, cy),
        ]

        color = (0, 255, 0, 80) if can_build else (255, 0, 0, 80)
        s = pygame.Surface((int(iso_w) + 2, int(iso_h) + 2), pygame.SRCALPHA)
        local_points = [(px - (cx - iso_w / 2), py - (cy - iso_h / 2)) for px, py in points]
        pygame.draw.polygon(s, color, local_points)
        screen.blit(s, (cx - iso_w / 2, cy - iso_h / 2))

        border_color = (0, 255, 0) if can_build else (255, 0, 0)
        pygame.draw.polygon(screen, border_color, points, 2)

    def _draw_tower_preview(self, screen, state, wx, wy, cx, cy, tile_size):
        tile = state.tile_manager.map_data[wy][wx]
        can_build = not tile.startswith('road_') and tile not in ('portal', 'castle')
        if can_build and self._cell_occupied(state, wx, wy):
            can_build = False

        self._draw_cell_highlight(screen, cx, cy, tile_size, can_build)

        # Квадратная зона поражения (сторона 2×range, выровнена по клеткам)
        config = state._get_tower_config(state.selected_tower)
        radius = config.get('range', 200)

        side = radius * 2
        range_surf = pygame.Surface((side, side), pygame.SRCALPHA)
        range_surf.fill((0, 255, 0, 30))
        screen.blit(range_surf, (cx - radius, cy - radius))
        pygame.draw.rect(screen, (0, 255, 0), (cx - radius, cy - radius, side, side), 1)

        name = state.selected_tower.upper()
        cost = config.get('cost', 100)
        info_text = f"{name} (${cost})"
        text = state.small_font.render(info_text, True, (255, 255, 255))
        screen.blit(text, (cx - text.get_width()//2, cy - tile_size // 2 - 30))

    def _draw_wall_preview(self, screen, state, wx, wy, cx, cy, tile_size):
        """Подсветка клетки + полупрозрачный спрайт выбранного укрепления."""
        tile = state.tile_manager.map_data[wy][wx]

        if state.selected_wall_type == 'gate':
            can_build = tile.startswith('road_')
            name, cost = 'GATE', 150
            orientation = state.towers_logic._gate_orientation(wx, wy)
            sprite_name = f"gate_{orientation}"
        else:
            can_build = tile == 'grass'
            # Показываем ту форму, что реально встанет по автоориентации,
            # учитывая гипотетическую стену в клетке под курсором.
            wall_cells, gate_cells = state.towers_logic._occupied_neighbor_cells()
            wall_cells = set(wall_cells)
            wall_cells.add((wx, wy))
            variant = state.towers_logic._wall_variant_at(wx, wy, wall_cells, gate_cells)
            name, cost = 'WALL', 80
            sprite_name = f"wall_{variant}"

        if can_build and self._cell_occupied(state, wx, wy):
            can_build = False

        self._draw_cell_highlight(screen, cx, cy, tile_size, can_build)

        # Полупрозрачный спрайт выбранного укрепления в клетке
        self._blit_ghost(screen, sprite_name, cx, cy, tile_size)

        text = state.small_font.render(f"{name} (${cost})", True, (255, 255, 255))
        screen.blit(text, (cx - text.get_width()//2, cy - tile_size // 2 - 30))

    _ghost_cache = {}

    def _blit_ghost(self, screen, sprite_name, cx, cy, tile_size):
        """Рисует полупрозрачный спрайт укрепления по центру клетки."""
        img = self._ghost_cache.get((sprite_name, tile_size))
        if img is None:
            try:
                from services.resource_loader import ResourceLoader
                base = ResourceLoader().load_image(f"fortify/{sprite_name}.png")
                img = pygame.transform.scale(base, (tile_size, tile_size)).convert_alpha()
                img.set_alpha(150)
                self._ghost_cache[(sprite_name, tile_size)] = img
            except Exception:
                return
        gx = cx - img.get_width() // 2
        gy = cy - img.get_height() // 2
        screen.blit(img, (gx, gy))
