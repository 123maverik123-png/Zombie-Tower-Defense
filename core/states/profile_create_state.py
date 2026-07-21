# core/states/profile_create_state.py
import pygame
import os
from core.state_manager import State
from core.audio import AudioManager
from services.profile_manager import ProfileManager
from core.font_loader import load_ui_font, load_title_font
from core.theme import (
    GOLD, GOLD_BRIGHT, GOLD_DIM, STONE_DARK, STONE_MID, STONE_LIGHT,
    PARCHMENT, PARCHMENT_DIM, TEAL_GLOW, DANGER, DANGER_BRIGHT, SUCCESS
)


def _draw_glow(screen, rect, color=TEAL_GLOW, pad=8, alpha=60, radius=10):
    glow = pygame.Surface((rect.width + pad * 2, rect.height + pad * 2), pygame.SRCALPHA)
    pygame.draw.rect(glow, (*color, alpha), glow.get_rect(), border_radius=radius)
    screen.blit(glow, (rect.x - pad, rect.y - pad))


class ProfileCreateState(State):
    def __init__(self, game, from_select=False):
        super().__init__(game)
        self.from_select = from_select
        self.profile_manager = ProfileManager()
        self.audio = AudioManager()

        self.font = load_ui_font(28)
        self.small_font = load_ui_font(20)
        self.title_font = load_title_font(40)

        self.name = ""
        self.mode = 'normal'
        self.error_message = ""
        self.error_timer = 0
        self.name_active = True
        self.click_cooldown = 0.0
        self.background = None
        self._load_background()

        self.dialog_rect = None
        self.name_input_rect = None
        self.mode_normal_btn = None
        self.mode_hardcore_btn = None
        self.create_btn = None
        self.cancel_btn = None

        self._update_ui()

    def _load_background(self):
        bg_path = "assets/images/menu_bg.jpg"
        if os.path.exists(bg_path):
            try:
                self.background = pygame.image.load(bg_path).convert()
            except Exception:
                self.background = None
        else:
            self.background = None

    def _update_ui(self):
        screen_w, screen_h = self.game.render_width, self.game.render_height
        self.dialog_rect = pygame.Rect(
            screen_w // 2 - 280,
            screen_h // 2 - 210,
            560,
            420
        )
        x = self.dialog_rect.x + 40
        y = self.dialog_rect.y + 80
        self.name_input_rect = pygame.Rect(x, y, 480, 42)
        self.mode_normal_btn = pygame.Rect(x, y + 140, 200, 48)
        self.mode_hardcore_btn = pygame.Rect(x + 280, y + 140, 200, 48)
        self.create_btn = pygame.Rect(x + 100, y + 260, 280, 52)
        self.cancel_btn = pygame.Rect(x + 160, y + 340, 160, 40)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._cancel()
                elif event.key == pygame.K_RETURN:
                    self._create_profile()
                elif self.name_active:
                    if event.key == pygame.K_BACKSPACE:
                        self.name = self.name[:-1]
                    elif event.key == pygame.K_TAB:
                        self.name_active = False
                    else:
                        if len(self.name) < 20 and event.unicode.isprintable():
                            self.name += event.unicode

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.click_cooldown <= 0:
                    if self.name_input_rect and self.name_input_rect.collidepoint(event.pos):
                        self.name_active = True
                    if self.mode_normal_btn and self.mode_normal_btn.collidepoint(event.pos):
                        self.mode = 'normal'
                        self.audio.play_sound("button_click", volume_override=0.3)
                    if self.mode_hardcore_btn and self.mode_hardcore_btn.collidepoint(event.pos):
                        self.mode = 'hardcore'
                        self.audio.play_sound("button_click", volume_override=0.3)
                    if self.create_btn and self.create_btn.collidepoint(event.pos):
                        self._create_profile()
                    if self.cancel_btn and self.cancel_btn.collidepoint(event.pos):
                        self._cancel()

    def _create_profile(self):
        if not self.name or len(self.name.strip()) < 2:
            self.error_message = "Name must be at least 2 characters!"
            self.error_timer = 120
            return

        name = self.name.strip()

        if self.profile_manager.profile_exists(name):
            self.error_message = f"Profile '{name}' already exists!"
            self.error_timer = 120
            return

        if self.profile_manager.get_profiles_count() >= ProfileManager.MAX_PROFILES:
            self.error_message = f"Max {ProfileManager.MAX_PROFILES} profiles allowed!"
            self.error_timer = 120
            return

        profile = self.profile_manager.create_profile(name, self.mode)
        if profile:
            self.audio.play_sound("button_click")
            if self.from_select:
                from .profile_select_state import ProfileSelectState
                self.game.state_manager.add_state('PROFILE_SELECT', ProfileSelectState(self.game))
                self.game.state_manager.change_state('PROFILE_SELECT')
            else:
                self.profile_manager.load_profile(name)
                from .menu.state import MenuState
                new_menu = MenuState(self.game, profile_manager=self.profile_manager, skip_check=False)
                self.game.state_manager.add_state('MENU', new_menu)
                self.game.state_manager.change_state('MENU')

    def _cancel(self):
        self.audio.play_sound("button_click")
        if self.from_select:
            self.game.state_manager.change_state('PROFILE_SELECT')
        else:
            if self.profile_manager.has_profile():
                self.game.state_manager.change_state('MENU')
            else:
                self.error_message = "You must create a profile to play!"
                self.error_timer = 120

    def update(self, dt):
        if self.click_cooldown > 0:
            self.click_cooldown -= dt
        if self.error_timer > 0:
            self.error_timer -= 1

    def draw(self, screen):
        screen_w, screen_h = self.game.render_width, self.game.render_height
        self._update_ui()

        screen.fill(STONE_DARK)
        if self.background:
            bg_scaled = pygame.transform.scale(self.background, (screen_w, screen_h))
            screen.blit(bg_scaled, (0, 0))
        else:
            for i in range(screen_h):
                t = i / screen_h
                r = int(15 + 30 * t)
                g = int(15 + 22 * t)
                b = int(30 + 55 * t)
                pygame.draw.line(screen, (r, g, b), (0, i), (screen_w, i))

        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        dialog_surf = pygame.Surface((self.dialog_rect.width, self.dialog_rect.height), pygame.SRCALPHA)
        dialog_surf.fill((20, 18, 16, 240))
        screen.blit(dialog_surf, (self.dialog_rect.x, self.dialog_rect.y))
        pygame.draw.rect(screen, GOLD, self.dialog_rect, 2, border_radius=10)

        x = self.dialog_rect.x + 40
        y = self.dialog_rect.y + 30

        title = self.title_font.render("CREATE PROFILE", True, GOLD)
        shadow = self.title_font.render("CREATE PROFILE", True, (0, 0, 0))
        tx = self.dialog_rect.x + (self.dialog_rect.width - title.get_width()) // 2
        screen.blit(shadow, (tx + 2, y + 2))
        screen.blit(title, (tx, y))

        y += 50

        label = self.font.render("Enter your name:", True, PARCHMENT)
        screen.blit(label, (x, y))
        y += 35

        input_rect = self.name_input_rect
        border_color = GOLD_BRIGHT if self.name_active else GOLD_DIM
        pygame.draw.rect(screen, STONE_DARK, input_rect, border_radius=5)
        pygame.draw.rect(screen, border_color, input_rect, 2, border_radius=5)

        display_name = self.name + ("|" if self.name_active else "")
        name_text = self.font.render(display_name, True, PARCHMENT)
        screen.blit(name_text, (input_rect.x + 12, input_rect.y + 8))

        y += 60

        mode_label = self.font.render("Select Mode:", True, PARCHMENT)
        screen.blit(mode_label, (x, y))
        y += 40

        normal_btn = self.mode_normal_btn
        normal_selected = self.mode == 'normal'
        color = SUCCESS if normal_selected else STONE_MID
        border = GOLD_BRIGHT if normal_selected else GOLD_DIM
        if normal_selected:
            _draw_glow(screen, normal_btn, TEAL_GLOW, pad=6, alpha=40)
        pygame.draw.rect(screen, color, normal_btn, border_radius=6)
        pygame.draw.rect(screen, border, normal_btn, 2, border_radius=6)
        text = self.font.render("NORMAL", True, PARCHMENT if normal_selected else PARCHMENT_DIM)
        screen.blit(text, (normal_btn.x + (normal_btn.width - text.get_width()) // 2,
                           normal_btn.y + 12))

        hardcore_btn = self.mode_hardcore_btn
        hardcore_selected = self.mode == 'hardcore'
        color = DANGER if hardcore_selected else STONE_MID
        border = DANGER_BRIGHT if hardcore_selected else GOLD_DIM
        if hardcore_selected:
            _draw_glow(screen, hardcore_btn, TEAL_GLOW, pad=6, alpha=40)
        pygame.draw.rect(screen, color, hardcore_btn, border_radius=6)
        pygame.draw.rect(screen, border, hardcore_btn, 2, border_radius=6)
        text = self.font.render("HARDCORE", True, PARCHMENT if hardcore_selected else PARCHMENT_DIM)
        screen.blit(text, (hardcore_btn.x + (hardcore_btn.width - text.get_width()) // 2,
                           hardcore_btn.y + 12))

        y += 70

        if self.mode == 'hardcore':
            desc = self.small_font.render("If you lose, ALL progress resets to Level 1!", True, GOLD_BRIGHT)
            screen.blit(desc, (self.dialog_rect.x + (self.dialog_rect.width - desc.get_width()) // 2, y))
            y += 35

        create_btn = self.create_btn
        can_create = len(self.name.strip()) >= 2
        color = SUCCESS if can_create else STONE_MID
        border = GOLD_BRIGHT if can_create else GOLD_DIM
        if can_create and create_btn.collidepoint(pygame.mouse.get_pos()):
            _draw_glow(screen, create_btn, TEAL_GLOW, pad=6, alpha=40)
        pygame.draw.rect(screen, color, create_btn, border_radius=6)
        pygame.draw.rect(screen, border, create_btn, 2, border_radius=6)
        text = self.font.render("CREATE PROFILE", True, PARCHMENT if can_create else PARCHMENT_DIM)
        screen.blit(text, (create_btn.x + (create_btn.width - text.get_width()) // 2,
                           create_btn.y + 14))

        y += 60

        cancel_btn = self.cancel_btn
        if cancel_btn.collidepoint(pygame.mouse.get_pos()):
            _draw_glow(screen, cancel_btn, TEAL_GLOW, pad=6, alpha=30)
        pygame.draw.rect(screen, STONE_MID, cancel_btn, border_radius=6)
        pygame.draw.rect(screen, GOLD_DIM, cancel_btn, 2, border_radius=6)
        text = self.small_font.render("CANCEL", True, PARCHMENT_DIM)
        screen.blit(text, (cancel_btn.x + (cancel_btn.width - text.get_width()) // 2,
                           cancel_btn.y + 10))

        if self.error_timer > 0:
            error_text = self.font.render(self.error_message, True, DANGER_BRIGHT)
            screen.blit(error_text, (self.dialog_rect.x + (self.dialog_rect.width - error_text.get_width()) // 2,
                                     self.dialog_rect.y + self.dialog_rect.height - 40))

    def on_resolution_changed(self, screen_w, screen_h):
        self._update_ui()