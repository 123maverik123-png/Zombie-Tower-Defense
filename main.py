# main.py
import pygame
import sys
import os

# Консоль Windows по умолчанию cp1251 — эмодзи в print() роняли игру
# при запуске из терминала. Перекодируем вывод в UTF-8 с заменой.
for _stream in (sys.stdout, sys.stderr):
    if _stream is not None and hasattr(_stream, 'reconfigure'):
        try:
            _stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
from core.state_manager import StateManager
from core.settings import GameSettings
from core.opengl import Renderer
from core.states import MenuState, PlayState, PauseState, GameOverState, SettingsState, LevelSelectState
from core.states.map_editor_state import MapEditorState
from core.states.profile_select_state import ProfileSelectState
from core.states.profile_create_state import ProfileCreateState


class Game:
    def __init__(self):
        pygame.init()

        self.settings = GameSettings()
        self.screen_w, self.screen_h = self.settings.get_resolution_tuple()
        self.display_mode = self.settings.display_mode

        self.render_width = self.screen_w
        self.render_height = self.screen_h

        self.renderer = None
        self._applying_resolution = False

        self._init_renderer()

        self.clock = pygame.time.Clock()
        self.running = True
        self.dt = 0

        # Создаём папки
        os.makedirs("saves", exist_ok=True)
        os.makedirs("saves/profiles", exist_ok=True)
        os.makedirs("data/configs", exist_ok=True)
        os.makedirs("assets/sounds", exist_ok=True)
        os.makedirs("assets/images", exist_ok=True)
        os.makedirs("assets/images/tiles", exist_ok=True)
        os.makedirs("assets/images/towers", exist_ok=True)
        os.makedirs("assets/images/projectiles", exist_ok=True)
        os.makedirs("assets/images/ui", exist_ok=True)
        os.makedirs("assets/sprites", exist_ok=True)
        os.makedirs("assets/fonts", exist_ok=True)

        # Создаём состояния
        self.state_manager = StateManager()
        self.state_manager.add_state('PROFILE_CREATE', ProfileCreateState(self))
        self.state_manager.add_state('PROFILE_SELECT', ProfileSelectState(self))
        self.state_manager.add_state('MENU', MenuState(self))
        self.state_manager.add_state('PAUSED', PauseState(self))
        self.state_manager.add_state('GAME_OVER', GameOverState(self))
        self.state_manager.add_state('SETTINGS', SettingsState(self))
        self.state_manager.add_state('LEVEL_SELECT', LevelSelectState(self))
        self.state_manager.add_state('MAP_EDITOR', MapEditorState(self))
        self.state_manager.change_state('MENU')

    def _init_renderer(self):
        self._create_window()
        if self.renderer:
            self.renderer.destroy()
        try:
            self.renderer = Renderer(self.screen_w, self.screen_h)
        except RuntimeError as e:
            print(f"❌ {e}")
            pygame.quit()
            sys.exit(1)

    def _create_window(self):
        """Создаёт окно с OpenGL контекстом"""
        display_mode = self.settings.display_mode
        print(f"🖥️ Creating OpenGL window: {self.screen_w}x{self.screen_h}, mode={display_mode}")

        if display_mode == "window":
            os.environ['SDL_VIDEO_WINDOW_POS'] = 'center'
        else:
            os.environ['SDL_VIDEO_WINDOW_POS'] = '0,0'

        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 1)

        flags = pygame.OPENGL | pygame.DOUBLEBUF

        if display_mode == "fullscreen":
            flags |= pygame.FULLSCREEN
        elif display_mode == "borderless":
            flags |= pygame.NOFRAME

        try:
            self.screen = pygame.display.set_mode((self.screen_w, self.screen_h), flags)
        except Exception as e:
            print(f"❌ Failed to set OpenGL mode: {e}")
            self.screen = pygame.display.set_mode((self.screen_w, self.screen_h), pygame.OPENGL | pygame.DOUBLEBUF)
            self.settings.set("display_mode", "window")

        pygame.display.set_caption("Zombie Tower Defense")
        print(f"📺 OpenGL window created: {self.screen_w}x{self.screen_h}")

    def _get_scale_and_offset(self):
        scale_x = self.screen_w / self.render_width
        scale_y = self.screen_h / self.render_height
        scale = min(scale_x, scale_y, 1.5)

        scaled_w = int(self.render_width * scale)
        scaled_h = int(self.render_height * scale)

        offset_x = (self.screen_w - scaled_w) // 2
        offset_y = (self.screen_h - scaled_h) // 2

        return scale, offset_x, offset_y, scaled_w, scaled_h

    def apply_display_mode(self):
        """Применяет изменения разрешения и режима отображения"""
        if self._applying_resolution:
            return
        self._applying_resolution = True

        try:
            print(f"🔄 Applying display mode: {self.settings.resolution} @ {self.settings.display_mode}")

            self.screen_w, self.screen_h = self.settings.get_resolution_tuple()
            self.render_width = self.screen_w
            self.render_height = self.screen_h

            # Пересоздаём окно и рендерер (контекст привязан к окну)
            if self.renderer:
                self.renderer.destroy()
                self.renderer = None

            self._init_renderer()

            # Обновляем все состояния
            for name in ['MENU', 'LEVEL_SELECT', 'SETTINGS', 'GAME_OVER', 'PAUSED', 'PROFILE_SELECT', 'PROFILE_CREATE', 'PLAYING']:
                if name in self.state_manager._states:
                    state = self.state_manager._states[name]
                    if hasattr(state, 'on_resolution_changed'):
                        state.on_resolution_changed(self.screen_w, self.screen_h)

            menu_state = self.state_manager._states.get('MENU')
            if menu_state and hasattr(menu_state, '_update_buttons'):
                menu_state._update_buttons(self.screen_w, self.screen_h)

            print(f"✅ Resolution applied: {self.screen_w}x{self.screen_h}")

        finally:
            self._applying_resolution = False

    def _convert_mouse_pos(self, pos):
        scale, offset_x, offset_y, scaled_w, scaled_h = self._get_scale_and_offset()

        if pos[0] < offset_x or pos[0] > offset_x + scaled_w or pos[1] < offset_y or pos[1] > offset_y + scaled_h:
            return None

        render_x = (pos[0] - offset_x) / scale
        render_y = (pos[1] - offset_y) / scale

        return (render_x, render_y)

    def run(self):
        frame_count = 0
        fps_timer = 0.0
        current_fps = 0
        fps_font = pygame.font.Font(None, 24)

        while self.running:
            fps_limit = self.settings.get("fps_limit", 60) or 60
            self.dt = self.clock.tick(fps_limit) / 1000.0

            frame_count += 1
            fps_timer += self.dt
            if fps_timer >= 1.0:
                current_fps = frame_count
                frame_count = 0
                fps_timer = 0.0

            events = pygame.event.get()
            converted_events = []

            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                    self.quit()
                    return

                if event.type == pygame.USEREVENT and getattr(event, 'code', None) == 1:
                    print("🔄 Processing resolution change event...")
                    self.apply_display_mode()
                    continue

                if event.type == pygame.MOUSEMOTION:
                    converted = self._convert_mouse_pos(event.pos)
                    if converted is not None:
                        new_event = pygame.event.Event(event.type, {
                            'pos': converted,
                            'rel': event.rel,
                            'buttons': event.buttons,
                            'window': event.window if hasattr(event, 'window') else None
                        })
                        converted_events.append(new_event)
                    else:
                        converted_events.append(event)
                elif event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEBUTTONUP:
                    converted = self._convert_mouse_pos(event.pos)
                    if converted is not None:
                        new_event = pygame.event.Event(event.type, {
                            'pos': converted,
                            'button': event.button,
                            'window': event.window if hasattr(event, 'window') else None
                        })
                        converted_events.append(new_event)
                    else:
                        converted_events.append(event)
                else:
                    converted_events.append(event)

            state = self.state_manager.get_current_state()
            if state:
                state.handle_events(converted_events)
                state.update(self.dt)

                # 1. Очистка экрана и UI-поверхности
                ui_surface = self.renderer.begin_frame()

                # 2. GPU-сцена (состояния со сценой реализуют draw_scene)
                if hasattr(state, 'draw_scene'):
                    state.draw_scene(self.renderer)

                # 3. Pygame-UI поверх
                state.draw(ui_surface)

                if self.settings.show_fps:
                    fps_text = fps_font.render(f"FPS: {current_fps}", True, (0, 255, 0))
                    ui_surface.blit(fps_text, (self.render_width - 120, 10))

                # 4. Батч сцены + оверлей на экран
                self.renderer.end_frame()
                pygame.display.flip()

    def quit(self):
        if self.renderer:
            try:
                self.renderer.destroy()
            except Exception:
                pass
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
