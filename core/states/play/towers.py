# core/states/play/towers.py
import json
import math
from entities.tower import Tower
from entities.wall import Wall
from entities.gate import Gate
from entities.decals import Decal
from core.event_bus import EventBus


class PlayTowers:
    def __init__(self, state):
        self.state = state

    def _gate_orientation(self, wx, wy):
        """Ориентация ворот по дороге: 'h' — створки горизонтальны (перекрывают
        вертикальный проход), 'v' — вертикальны (перекрывают горизонтальный).

        road_v (дорога идёт вертикально) → ворота 'h' поперёк; road_h → 'v'.
        Для поворотов смотрим, с какой стороны есть дорожные соседи.
        """
        tm = self.state.tile_manager
        tile = tm.map_data[wy][wx]
        if tile == 'road_v':
            return 'h'
        if tile == 'road_h':
            return 'v'

        # Поворот/перекрёсток: по направлению соседних дорожных клеток
        def is_road(x, y):
            if 0 <= x < tm.map_width and 0 <= y < tm.map_height:
                return tm.map_data[y][x].startswith('road_')
            return False

        vert = is_road(wx, wy - 1) + is_road(wx, wy + 1)
        horiz = is_road(wx - 1, wy) + is_road(wx + 1, wy)
        # Больше вертикальных соседей → проход вертикальный → ворота 'h'
        return 'h' if vert >= horiz else 'v'
    
    def _find_portal(self):
        state = self.state
        for y in range(state.tile_manager.map_height):
            for x in range(state.tile_manager.map_width):
                if state.tile_manager.map_data[y][x] == 'portal':
                    return (x, y)
        return None
    
    def _get_occupied_cells(self):
        state = self.state
        tile_size = state.tile_manager.tile_size
        occupied = set()
        
        for tower in state.towers:
            wx = tower.x // tile_size
            wy = tower.y // tile_size
            occupied.add((int(wx), int(wy)))
        
        for wall in state.walls:
            wx = wall.x // tile_size
            wy = wall.y // tile_size
            occupied.add((int(wx), int(wy)))
        
        for gate in state.gates:
            wx = gate.x // tile_size
            wy = gate.y // tile_size
            occupied.add((int(wx), int(wy)))
        
        return occupied
    
    def _is_position_occupied(self, wx, wy):
        occupied = self._get_occupied_cells()
        return (int(wx), int(wy)) in occupied
    
    def build(self, pos):
        state = self.state
        x, y = pos
        
        # ✅ Получаем координаты и преобразуем в int
        wx_float, wy_float = state.tile_manager.get_grid_position(x, y)
        wx = int(wx_float)
        wy = int(wy_float)
        
        if wx < 0 or wx >= state.tile_manager.map_width or wy < 0 or wy >= state.tile_manager.map_height:
            return False
        
        tile = state.tile_manager.map_data[wy][wx]
        if tile.startswith('road_') or tile in ('portal', 'castle'):
            state.feedback_logic.show_error(x, y, "Cannot build on road!")
            return False
        
        if self._is_position_occupied(wx, wy):
            state.feedback_logic.show_error(x, y, "Space occupied!")
            return False
        
        config = state._get_tower_config(state.selected_tower)
        if not config:
            return False
        
        cost = config.get('cost', 100)
        if not state.player.spend_gold(cost):
            state.feedback_logic.show_error(x, y, f"Not enough gold! Need {cost}")
            return False
        
        tile_size = state.tile_manager.tile_size
        tower_x = wx * tile_size + tile_size // 2
        tower_y = wy * tile_size + tile_size // 2
        
        tower = Tower(tower_x, tower_y, config)
        state.towers.append(tower)
        
        state.audio.play_sound("tower_build")
        EventBus.emit('tower_built', {'tower': tower})
        
        decal = Decal(tower_x, tower_y, 'smoke_light', scale=0.8)
        state.decals.append(decal)
        
        state.feedback_logic.show_success(tower_x, tower_y)
        return True
    
    def build_wall(self, pos):
        state = self.state
        x, y = pos
        
        # ✅ Получаем координаты и преобразуем в int
        wx_float, wy_float = state.tile_manager.get_grid_position(x, y)
        wx = int(wx_float)
        wy = int(wy_float)

        if wx < 0 or wx >= state.tile_manager.map_width or wy < 0 or wy >= state.tile_manager.map_height:
            state.feedback_logic.show_error(x, y, "Out of map!")
            return False

        tile = state.tile_manager.map_data[wy][wx]
        
        if state.level_number < 5:
            state.feedback_logic.show_error(x, y, "Walls unlocked at level 5!")
            return False

        if state.selected_wall_type == 'gate':
            if not tile.startswith('road_'):
                state.feedback_logic.show_error(x, y, "Gate must be placed on road!")
                return False
            
            portal_pos = self._find_portal()
            if portal_pos:
                dx = abs(wx - portal_pos[0])
                dy = abs(wy - portal_pos[1])
                if dx + dy < 10:
                    state.feedback_logic.show_error(x, y, "Gate too close to portal! Need 10 tiles away")
                    return False
            
            if self._is_position_occupied(wx, wy):
                state.feedback_logic.show_error(x, y, "Space occupied by tower, wall or gate!")
                return False
            
            cost = 150
            if not state.player.spend_gold(cost):
                state.feedback_logic.show_error(x, y, f"Not enough gold! Need {cost}")
                return False
            
            tile_size = state.tile_manager.tile_size
            gate_x = wx * tile_size + tile_size // 2
            gate_y = wy * tile_size + tile_size // 2
            
            gate = Gate(gate_x, gate_y, 500, self._gate_orientation(wx, wy))
            state.gates.append(gate)
            
            state.audio.play_sound("tower_build")
            state.feedback_logic.show_success(gate_x, gate_y)
            return True
        
        elif state.selected_wall_type == 'wall':
            if tile != 'grass':
                state.feedback_logic.show_error(x, y, "Wall can only be placed on grass!")
                return False
            
            if self._is_position_occupied(wx, wy):
                state.feedback_logic.show_error(x, y, "Space occupied by tower, wall or gate!")
                return False
            
            cost = 80
            if not state.player.spend_gold(cost):
                state.feedback_logic.show_error(x, y, f"Not enough gold! Need {cost}")
                return False
            
            tile_size = state.tile_manager.tile_size
            wall_x = wx * tile_size + tile_size // 2
            wall_y = wy * tile_size + tile_size // 2
            
            wall = Wall(wall_x, wall_y, 200, getattr(state, 'selected_wall_variant', 'h'))
            state.walls.append(wall)
            
            state.audio.play_sound("tower_build")
            state.feedback_logic.show_success(wall_x, wall_y)
            return True
        
        return False
    
    def upgrade_tower(self, tower):
        state = self.state
        
        if tower.upgrades.level < tower.upgrades.max_level:
            cost = tower.upgrades.upgrade_cost
            if state.player.spend_gold(cost):
                tower.upgrade()
                state.tower_ui.hide()
                state.audio.play_sound("tower_build")
                state.feedback_logic.show_success(tower.x, tower.y)
                return True
            else:
                state.feedback_logic.show_error(tower.x, tower.y, f"Need {cost} gold for upgrade!")
                return False
        else:
            state.feedback_logic.show_error(tower.x, tower.y, "MAX LEVEL!")
            return False
    
    def sell_tower(self, tower):
        state = self.state
        
        total_cost = tower.upgrades.cost
        for level in range(2, tower.upgrades.level + 1):
            total_cost += int(tower.upgrades.cost * (1.5 ** (level - 2)))
        
        sell_price = int(total_cost * 0.5)
        state.player.gold += sell_price
        
        if tower in state.towers:
            state.towers.remove(tower)
        
        state.tower_ui.hide()
        state.audio.play_sound("button_click")
        state.feedback_logic.show_success(tower.x, tower.y)
        print(f"💰 Tower sold for ${sell_price}!")
        return True