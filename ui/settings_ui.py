# ui/settings_ui.py
import pygame
from core.settings import GameSettings
from core.audio import AudioManager
from core.font_loader import load_font, load_ui_font, load_title_font
from core.theme import (
    GOLD, GOLD_BRIGHT, GOLD_DIM, STONE_DARK, STONE_MID, STONE_LIGHT,
    PARCHMENT, PARCHMENT_DIM, TEAL_GLOW, DANGER, DANGER_BRIGHT, SUCCESS
)


def _draw_glow(screen, rect, color, pad=8, alpha=60, radius=10):
    glow = pygame.Surface((rect.width + pad * 2, rect.height + pad * 2), pygame.SRCALPHA)
    pygame.draw.rect(glow, (*color, alpha), glow.get_rect(), border_radius=radius)
    screen.blit(glow, (rect.x - pad, rect.y - pad))


class Slider:
    def __init__(self, x, y, width, height, min_val=0.0, max_val=1.0, initial=0.5, label=""):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial
        self.label = label
        self.dragging = False
        self.hovered = False
        self.font = load_ui_font(24)
        self.value_font = load_ui_font(22)
        self.knob_radius = 11
        self.knob_x = self._value_to_x(initial)

    def _value_to_x(self, value):
        t = (value - self.min_val) / (self.max_val - self.min_val)
        return self.rect.x + t * self.rect.width

    def _x_to_value(self, x):
        t = max(0, min(1, (x - self.rect.x) / self.rect.width))
        return self.min_val + t * (self.max_val - self.min_val)

    def handle_event(self, pos):
        if self.rect.collidepoint(pos) or self.dragging:
            self.dragging = True
            self.value = self._x_to_value(pos[0])
            self.knob_x = self._value_to_x(self.value)
            return True
        return False

    def handle_hover(self, pos):
        hit = self.rect.inflate(0, 16)
        self.hovered = hit.collidepoint(pos)

    def release(self):
        self.dragging = False

    def draw(self, screen):
        pygame.draw.rect(screen, STONE_DARK, self.rect, border_radius=4)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y,
                                 max(0, self.knob_x - self.rect.x), self.rect.height)
        pygame.draw.rect(screen, GOLD_DIM, fill_rect, border_radius=4)
        border_color = GOLD_BRIGHT if (self.hovered or self.dragging) else GOLD
        pygame.draw.rect(screen, border_color, self.rect, 2, border_radius=4)

        knob_center = (int(self.knob_x), int(self.rect.y + self.rect.height / 2))
        if self.dragging:
            _draw_glow(screen, pygame.Rect(knob_center[0] - 12, knob_center[1] - 12, 24, 24),
                       TEAL_GLOW, pad=6, alpha=90, radius=16)
        pygame.draw.circle(screen, GOLD_BRIGHT, knob_center, self.knob_radius)
        pygame.draw.circle(screen, STONE_DARK, knob_center, self.knob_radius, 2)

        label_text = self.font.render(self.label, True, PARCHMENT)
        value_text = self.value_font.render(f"{int(self.value * 100)}%", True, GOLD_BRIGHT)
        screen.blit(label_text, (self.rect.x, self.rect.y - 30))
        screen.blit(value_text, (self.rect.right - value_text.get_width(), self.rect.y - 29))


class ToggleButton:
    def __init__(self, x, y, label="", initial=True):
        self.x = x
        self.y = y
        self.width = 58
        self.height = 30
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.label = label
        self.is_on = initial
        self.font = load_ui_font(24)
        self.click_cooldown = 0.0
        self.hovered = False

    def handle_click(self, pos):
        if self.click_cooldown <= 0 and self.rect.collidepoint(pos):
            self.is_on = not self.is_on
            self.click_cooldown = 0.3
            return True
        return False

    def handle_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def update(self, dt):
        if self.click_cooldown > 0:
            self.click_cooldown -= dt

    def draw(self, screen):
        label_text = self.font.render(self.label, True, PARCHMENT)
        screen.blit(label_text, (self.x - label_text.get_width() - 16, self.y + 3))

        track_color = GOLD_DIM if self.is_on else STONE_MID
        pygame.draw.rect(screen, track_color, self.rect, border_radius=15)
        border_color = GOLD_BRIGHT if (self.is_on or self.hovered) else GOLD
        pygame.draw.rect(screen, border_color, self.rect, 2, border_radius=15)

        knob_x = self.rect.x + self.width - 25 if self.is_on else self.rect.x + 5
        knob_center = (int(knob_x + 10), int(self.rect.y + self.rect.height / 2))
        pygame.draw.circle(screen, GOLD_BRIGHT if self.is_on else PARCHMENT_DIM, knob_center, 10)
        pygame.draw.circle(screen, STONE_DARK, knob_center, 10, 2)


class DisplayModeSelector:
    def __init__(self, x, y, label="Display Mode", game=None):
        self.x = x
        self.y = y
        self.label = label
        self.game = game
        self.font = load_ui_font(24)
        self.small_font = load_ui_font(20)

        self.modes = ["window", "fullscreen", "borderless"]
        self.mode_labels = ["Window", "Fullscreen", "Borderless"]

        self.settings = GameSettings()
        self.audio = AudioManager()

        self.current_mode = self.settings.display_mode
        if self.current_mode not in self.modes:
            self.current_mode = "window"

        self.pending_mode = self.current_mode
        self.hover_index = -1

        self._create_buttons(x, y)

    def _create_buttons(self, x, y):
        btn_width = 140
        btn_height = 42
        spacing = 12
        total_width = btn_width * 3 + spacing * 2
        start_x = x + (400 - total_width) // 2

        self.buttons = []
        for i, mode in enumerate(self.modes):
            btn_rect = pygame.Rect(
                start_x + i * (btn_width + spacing),
                y + 36,
                btn_width,
                btn_height
            )
            self.buttons.append({'rect': btn_rect, 'mode': mode, 'label': self.mode_labels[i]})

    def handle_click(self, pos):
        for btn in self.buttons:
            if btn['rect'].collidepoint(pos):
                if btn['mode'] != self.pending_mode:
                    self.pending_mode = btn['mode']
                    self.audio.play_sound("button_click", volume_override=0.3)
                    return True
        return False

    def handle_hover(self, pos):
        self.hover_index = -1
        for i, btn in enumerate(self.buttons):
            if btn['rect'].collidepoint(pos):
                self.hover_index = i
                break

    def get_pending_mode(self):
        return self.pending_mode

    def draw(self, screen):
        self._create_buttons(self.x, self.y)

        label_text = self.font.render(f"{self.label}", True, PARCHMENT)
        screen.blit(label_text, (self.x, self.y + 6))

        for i, btn in enumerate(self.buttons):
            rect = btn['rect']
            is_selected = btn['mode'] == self.pending_mode
            is_hovered = i == self.hover_index

            if is_selected:
                _draw_glow(screen, rect, TEAL_GLOW, pad=6, alpha=55, radius=8)
                color = STONE_LIGHT
                border_color = GOLD_BRIGHT
            elif is_hovered:
                color = STONE_LIGHT
                border_color = GOLD
            else:
                color = STONE_MID
                border_color = GOLD_DIM

            pygame.draw.rect(screen, color, rect, border_radius=6)
            pygame.draw.rect(screen, border_color, rect, 2, border_radius=6)

            text_color = GOLD_BRIGHT if is_selected else PARCHMENT_DIM
            text = self.small_font.render(btn['label'], True, text_color)
            screen.blit(text, (rect.x + (rect.width - text.get_width()) // 2, rect.y + 12))

            if is_selected:
                check = self.small_font.render("✓", True, GOLD_BRIGHT)
                screen.blit(check, (rect.x + 6, rect.y + 4))


class ResolutionSelector:
    def __init__(self, x, y, label="Resolution", game=None):
        self.x = x
        self.y = y
        self.label = label
        self.game = game
        self.font = load_ui_font(24)
        self.small_font = load_ui_font(20)

        self.resolutions = ["1280x720", "1920x1080", "2560x1440"]
        self.current_index = 0
        self.pending_index = 0

        self.prev_btn = None
        self.next_btn = None
        self.value_rect = None
        self.prev_hovered = False
        self.next_hovered = False

        self.settings = GameSettings()
        self.audio = AudioManager()

        current_res = self.settings.resolution
        if current_res in self.resolutions:
            self.current_index = self.resolutions.index(current_res)
            self.pending_index = self.current_index

        self._create_buttons(x, y)

    def _create_buttons(self, x, y):
        self.prev_btn = pygame.Rect(x + 160, y, 40, 40)
        self.next_btn = pygame.Rect(x + 380, y, 40, 40)
        self.value_rect = pygame.Rect(x + 210, y, 160, 40)

    def handle_click(self, pos):
        if self.prev_btn and self.prev_btn.collidepoint(pos):
            self.pending_index = (self.pending_index - 1) % len(self.resolutions)
            self.audio.play_sound("button_click", volume_override=0.3)
            return True
        elif self.next_btn and self.next_btn.collidepoint(pos):
            self.pending_index = (self.pending_index + 1) % len(self.resolutions)
            self.audio.play_sound("button_click", volume_override=0.3)
            return True
        return False

    def handle_hover(self, pos):
        self.prev_hovered = bool(self.prev_btn and self.prev_btn.collidepoint(pos))
        self.next_hovered = bool(self.next_btn and self.next_btn.collidepoint(pos))

    def get_pending_resolution(self):
        return self.resolutions[self.pending_index]

    def draw(self, screen):
        self._create_buttons(self.x, self.y)

        label_text = self.font.render(f"{self.label}", True, PARCHMENT)
        screen.blit(label_text, (self.x, self.y + 8))

        for rect, hovered, arrow in [(self.prev_btn, self.prev_hovered, "<"),
                                      (self.next_btn, self.next_hovered, ">")]:
            pygame.draw.rect(screen, STONE_LIGHT if hovered else STONE_MID, rect, border_radius=5)
            pygame.draw.rect(screen, GOLD_BRIGHT if hovered else GOLD, rect, 2, border_radius=5)
            t = self.small_font.render(arrow, True, PARCHMENT)
            screen.blit(t, (rect.x + (rect.width - t.get_width()) // 2, rect.y + 8))

        pygame.draw.rect(screen, STONE_DARK, self.value_rect, border_radius=5)
        pygame.draw.rect(screen, GOLD, self.value_rect, 2, border_radius=5)
        res_text = self.small_font.render(self.resolutions[self.pending_index], True, GOLD_BRIGHT)
        screen.blit(res_text, (self.value_rect.x + (self.value_rect.width - res_text.get_width()) // 2,
                                self.value_rect.y + 9))


class SettingsUI:
    def __init__(self, game):
        self.game = game  # ✅ Сохраняем ссылку на game
        self.settings = GameSettings()
        self.audio = AudioManager()

        self.sliders = []
        self.toggles = []
        self.selectors = []

        self.dragging_slider = None
        self.apply_btn = None
        self.apply_hovered = False

        self.initialized = False

    def _init_elements(self, screen_w, screen_h):
        self.initialized = True

        center_x = screen_w // 2
        start_y = 130

        self.sliders = []
        self.toggles = []
        self.selectors = []

        slider_width = 440
        slider_x = center_x - slider_width // 2

        self.master_slider = Slider(slider_x, start_y, slider_width, 24, 0.0, 1.0,
                                     self.settings.master_volume, "Master Volume")
        self.music_slider = Slider(slider_x, start_y + 90, slider_width, 24, 0.0, 1.0,
                                    self.settings.music_volume, "Music Volume")
        self.sfx_slider = Slider(slider_x, start_y + 180, slider_width, 24, 0.0, 1.0,
                                  self.settings.sfx_volume, "SFX Volume")

        self.sliders.extend([self.master_slider, self.music_slider, self.sfx_slider])

        toggle_x = center_x - 60
        toggle_y = start_y + 270

        self.sound_toggle = ToggleButton(toggle_x, toggle_y, "Sound", self.settings.sound_enabled)
        self.music_toggle = ToggleButton(toggle_x + 260, toggle_y, "Music", self.settings.music_enabled)

        self.toggles.extend([self.sound_toggle, self.music_toggle])

        self.display_selector = DisplayModeSelector(center_x - 200, start_y + 340, "Display Mode", self.game)
        self.selectors.append(self.display_selector)

        self.resolution_selector = ResolutionSelector(center_x - 200, start_y + 430, "Resolution", self.game)
        self.selectors.append(self.resolution_selector)

        self.apply_btn = pygame.Rect(center_x - 110, start_y + 510, 220, 52)

    def _apply_settings(self):
        self.settings.set("master_volume", self.master_slider.value)
        self.settings.set("music_volume", self.music_slider.value)
        self.settings.set("sfx_volume", self.sfx_slider.value)
        self.settings.set("sound_enabled", self.sound_toggle.is_on)
        self.settings.set("music_enabled", self.music_toggle.is_on)

        self.audio.update_volumes()

        if not self.music_toggle.is_on:
            self.audio.stop_music()
        else:
            if not pygame.mixer.music.get_busy():
                self.audio.play_music("menu_theme.wav")

        new_res = self.resolution_selector.get_pending_resolution()
        new_mode = self.display_selector.get_pending_mode()

        self.settings.set("resolution", new_res)
        self.settings.set("display_mode", new_mode)

        pygame.event.post(pygame.event.Event(pygame.USEREVENT, code=1))

        print(f"✅ Applied: Resolution={new_res}, DisplayMode={new_mode}")

    def handle_click(self, pos):
        for slider in self.sliders:
            if slider.handle_event(pos):
                self.dragging_slider = slider
                return

        for toggle in self.toggles:
            if toggle.handle_click(pos):
                return

        for selector in self.selectors:
            if selector.handle_click(pos):
                return

        if self.apply_btn and self.apply_btn.collidepoint(pos):
            self._apply_settings()
            self.audio.play_sound("button_click")
            return True

        return False

    def handle_mouse_move(self, pos):
        if self.dragging_slider:
            self.dragging_slider.handle_event(pos)

        for slider in self.sliders:
            slider.handle_hover(pos)
        for toggle in self.toggles:
            toggle.handle_hover(pos)
        for selector in self.selectors:
            selector.handle_hover(pos)

        self.apply_hovered = bool(self.apply_btn and self.apply_btn.collidepoint(pos))

    def handle_mouse_release(self):
        if self.dragging_slider:
            self.dragging_slider.release()
            self.dragging_slider = None

    def draw(self, screen):
        screen_w, screen_h = self.game.render_width, self.game.render_height  # ✅ Теперь работает

        if not self.initialized:
            self._init_elements(screen_w, screen_h)

        if hasattr(self, '_last_screen_w') and (self._last_screen_w != screen_w or self._last_screen_h != screen_h):
            self._init_elements(screen_w, screen_h)

        self._last_screen_w = screen_w
        self._last_screen_h = screen_h

        panel_rect = pygame.Rect(
            screen_w // 2 - 380,
            50,
            760,
            min(screen_h - 100, 720)
        )
        panel_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel_surface.fill((10, 9, 8, 180))
        screen.blit(panel_surface, (panel_rect.x, panel_rect.y))
        pygame.draw.rect(screen, GOLD, panel_rect, 2, border_radius=8)

        title_font = load_title_font(46)
        title = title_font.render("SETTINGS", True, GOLD)
        title_shadow = title_font.render("SETTINGS", True, (0, 0, 0))
        tx = screen_w // 2 - title.get_width() // 2
        screen.blit(title_shadow, (tx + 2, 74))
        screen.blit(title, (tx, 72))

        for slider in self.sliders:
            slider.draw(screen)

        for toggle in self.toggles:
            toggle.draw(screen)

        for selector in self.selectors:
            selector.draw(screen)

        if self.apply_btn:
            shadow_rect = self.apply_btn.copy()
            shadow_rect.x += 3
            shadow_rect.y += 4
            shadow_surf = pygame.Surface((self.apply_btn.width, self.apply_btn.height), pygame.SRCALPHA)
            shadow_surf.fill((0, 0, 0, 100))
            screen.blit(shadow_surf, shadow_rect.topleft)

            base_color = STONE_LIGHT if self.apply_hovered else STONE_MID
            btn_surf = pygame.Surface((self.apply_btn.width, self.apply_btn.height), pygame.SRCALPHA)
            btn_surf.fill((*base_color, 235))
            screen.blit(btn_surf, self.apply_btn.topleft)

            if self.apply_hovered:
                _draw_glow(screen, self.apply_btn, TEAL_GLOW, pad=8, alpha=60, radius=10)

            border_color = GOLD_BRIGHT if self.apply_hovered else GOLD
            pygame.draw.rect(screen, border_color, self.apply_btn, 2, border_radius=6)

            btn_font = load_ui_font(28)
            text_color = GOLD_BRIGHT if self.apply_hovered else PARCHMENT
            btn_text = btn_font.render("APPLY", True, text_color)
            screen.blit(btn_text, (self.apply_btn.x + (self.apply_btn.width - btn_text.get_width()) // 2,
                                    self.apply_btn.y + (self.apply_btn.height - btn_text.get_height()) // 2))

    def update(self, dt):
        for toggle in self.toggles:
            toggle.update(dt)