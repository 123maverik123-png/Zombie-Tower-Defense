# core/states/map_editor/actions.py
import json
import os


class MapEditorActions:
    def __init__(self, state):
        self.state = state

    def _get_tile_statistics(self):
        """Возвращает статистику использования тайлов"""
        state = self.state
        stats = {}
        for row in state.map_data:
            for cell in row:
                stats[cell] = stats.get(cell, 0) + 1
        return stats

    def save_map(self):
        state = self.state
        state.show_name_input = True
        state.input_name = state.map_name
        state.ui.show_message("Enter map name:")

    def save_with_name(self, name):
        state = self.state
        if not name or not name.strip():
            state.ui.show_message("❌ Name cannot be empty!")
            return

        name = name.strip()
        filename = f"data/maps/{name}.json"
        if os.path.exists(filename):
            state.ui.show_message(f"⚠️ Map '{name}' already exists! Press Y to overwrite, N to cancel")
            state.pending_overwrite = name
            return

        self.do_save(name)

    def do_save(self, name):
        state = self.state

        portals = []
        for y in range(state.map_height):
            for x in range(state.map_width):
                if state.map_data[y][x] == 'portal':
                    portals.append((x, y))

        castle = None
        for y in range(state.map_height):
            for x in range(state.map_width):
                if state.map_data[y][x] == 'castle':
                    castle = (x, y)
                    break
            if castle:
                break

        if not portals:
            state.ui.show_message("ERROR: Need at least one PORTAL!")
            return
        if not castle:
            state.ui.show_message("ERROR: Need a CASTLE!")
            return
        if len(state.waypoints) < 2:
            state.ui.show_message("ERROR: Need at least 2 waypoints (portal + castle)!")
            return

        data = {
            'name': name,
            'tile_size': state.tile_size,
            'map': state.map_data,
            'waypoints': state.waypoints,
            'width': state.map_width,
            'height': state.map_height,
            'version': '1.2'
        }

        os.makedirs('data/maps', exist_ok=True)
        filename = f"data/maps/{name}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        state.map_name = name
        state.show_name_input = False
        state.pending_overwrite = None
        state.ui.show_message(f"✅ Map saved: {name}")

    def load_map(self):
        state = self.state
        maps_dir = 'data/maps'
        if not os.path.exists(maps_dir):
            state.ui.show_message("No maps directory found!")
            return

        files = [f for f in os.listdir(maps_dir) if f.endswith('.json')]
        if not files:
            state.ui.show_message("No saved maps found!")
            return

        filename = f"{maps_dir}/{files[0]}"
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            state.map_data = data['map']
            state.map_width = len(state.map_data[0])
            state.map_height = len(state.map_data)
            state.map_name = data.get('name', 'custom_level')
            state.tile_size = data.get('tile_size', 65)
            state.waypoints = data.get('waypoints', [])

            if not state.waypoints:
                state._init_waypoints_from_portal()

            state.ui.show_message(f"✅ Map loaded: {files[0]}")
        except Exception as e:
            state.ui.show_message(f"❌ Error loading map: {e}")

    def new_map(self):
        state = self.state
        state.map_data = [['grass' for _ in range(state.map_width)] for _ in range(state.map_height)]
        state.map_name = f"level_{len(os.listdir('data/maps')) + 1 if os.path.exists('data/maps') else 1}"
        state.waypoints = []
        state.ui.show_message("New map created!")

    def delete_map(self):
        state = self.state
        filename = f"data/maps/{state.map_name}.json"
        if os.path.exists(filename):
            os.remove(filename)
            state.ui.show_message(f"🗑️ Map deleted: {state.map_name}")
            self.new_map()
        else:
            state.ui.show_message("Map file not found!")

    def change_map_size(self, dx, dy):
        state = self.state
        new_width = max(10, min(40, state.map_width + dx))
        new_height = max(8, min(30, state.map_height + dy))

        if new_width == state.map_width and new_height == state.map_height:
            return

        new_map = [['grass' for _ in range(new_width)] for _ in range(new_height)]
        for y in range(min(state.map_height, new_height)):
            for x in range(min(state.map_width, new_width)):
                new_map[y][x] = state.map_data[y][x]

        state.map_width = new_width
        state.map_height = new_height
        state.map_data = new_map
        state.ui.show_message(f"Map size: {state.map_width}x{state.map_height}")

    def waypoints_to_road(self):
        state = self.state
        if len(state.waypoints) < 2:
            state.ui.show_message("❌ Need at least 2 waypoints to create a road!")
            return

        for i, (wx, wy) in enumerate(state.waypoints):
            if i == 0:
                continue
            tile = state.map_data[wy][wx]
            if tile != 'grass' and tile != 'portal':
                state.ui.show_message(f"❌ Waypoint {i} at ({wx},{wy}) is blocked by {tile}!")
                return

        road_count = 0
        for i in range(len(state.waypoints) - 1):
            x1, y1 = state.waypoints[i]
            x2, y2 = state.waypoints[i + 1]

            if x1 == x2:
                step = 1 if y2 > y1 else -1
                for y in range(y1, y2 + step, step):
                    if (x1, y) not in state.waypoints or (x1, y) == state.waypoints[0]:
                        if state.map_data[y][x1] == 'grass':
                            state.map_data[y][x1] = 'road_v'
                            road_count += 1
            elif y1 == y2:
                step = 1 if x2 > x1 else -1
                for x in range(x1, x2 + step, step):
                    if (x, y1) not in state.waypoints or (x, y1) == state.waypoints[0]:
                        if state.map_data[y1][x] == 'grass':
                            state.map_data[y1][x] = 'road_h'
                            road_count += 1
            else:
                step_x = 1 if x2 > x1 else -1
                for x in range(x1, x2 + step_x, step_x):
                    if (x, y1) not in state.waypoints or (x, y1) == state.waypoints[0]:
                        if state.map_data[y1][x] == 'grass':
                            state.map_data[y1][x] = 'road_h'
                            road_count += 1
                step_y = 1 if y2 > y1 else -1
                for y in range(y1, y2 + step_y, step_y):
                    if (x2, y) not in state.waypoints or (x2, y) == state.waypoints[0]:
                        if state.map_data[y][x2] == 'grass':
                            state.map_data[y][x2] = 'road_v'
                            road_count += 1

        self._fix_road_turns()
        state.ui.show_message(f"✅ Created road from {len(state.waypoints)} waypoints! ({road_count} road tiles placed)")

    def _fix_road_turns(self):
        state = self.state
        path_set = set()
        for y in range(state.map_height):
            for x in range(state.map_width):
                if state.map_data[y][x].startswith('road_'):
                    path_set.add((x, y))

        for y in range(state.map_height):
            for x in range(state.map_width):
                if state.map_data[y][x] not in ['grass', 'portal', 'castle']:
                    up = (x, y-1) in path_set
                    down = (x, y+1) in path_set
                    left = (x-1, y) in path_set
                    right = (x+1, y) in path_set
                    neighbors = sum([up, down, left, right])

                    if neighbors == 2:
                        if up and down:
                            state.map_data[y][x] = 'road_v'
                        elif left and right:
                            state.map_data[y][x] = 'road_h'
                        elif up and right:
                            state.map_data[y][x] = 'road_tr'
                        elif up and left:
                            state.map_data[y][x] = 'road_tl'
                        elif down and right:
                            state.map_data[y][x] = 'road_br'
                        elif down and left:
                            state.map_data[y][x] = 'road_bl'
                    elif neighbors == 3 or neighbors == 4:
                        state.map_data[y][x] = 'road_cross'
                    elif neighbors == 1:
                        if up or down:
                            state.map_data[y][x] = 'road_v'
                        else:
                            state.map_data[y][x] = 'road_h'