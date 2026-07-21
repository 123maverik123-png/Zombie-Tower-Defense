# core/states/profile_select_state.py
import pygame
import os 
from core.state_manager import State
from core.audio import AudioManager
from services.profile_manager import ProfileManager
from core.font_loader import load_ui_font, load_title_font
from core.theme import (
    GOLD, GOLD_BRIGHT, GOLD_DIM, STONE_DARK, STONE_MID, STONE_LIGHT,
    PARCHMENT, PARCHMENT_DIM, TEAL_GLOW, DANGER, DANGER_BRIGHT
)


def _draw_glow(screen, rect, color=TEAL_GLOW, pad=8, alpha=60, radius=10):
    glow = pygame.Surface((rect.width + pad * 2, rect.height + pad * 2), pygame.SRCALPHA)
    pygame.draw.rect(glow, (*color, alpha), glow.get_rect(), border_radius=radius)
    screen.blit(glow, (rect.x - pad, rect.y - pad))


def _draw_button(screen, rect, text, hovered=False, icon=None, color=STONE_MID, border_color=GOLD):
    shadow_rect = rect.copy()
    shadow_rect.x += 3
    shadow_rect.y += 4
    shadow_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    shadow_surf.fill((0, 0, 0, 100))
    screen.blit(shadow_surf, shadow_rect.topleft)

    base_color = STONE_LIGHT if hovered else color
    btn_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    btn_surf.fill((*base_color, 235))
    screen.blit(btn_surf, rect.topleft)

    if hovered:
        _draw_glow(screen, rect, TEAL_GLOW, pad=8, alpha=55)

    border = GOLD_BRIGHT if hovered else border_color
    pygame.draw.rect(screen, border, rect, 2, border_radius=6)

    text_color = GOLD_BRIGHT if hovered else PARCHMENT
    font = load_ui_font(26)
    text_surf = font.render(text, True, text_color)
    screen.blit(text_surf, (rect.x + (rect.width - text_surf.get_width()) // 2,
                            rect.y + (rect.height - text_surf.get_height()) // 2))


class ProfileSelectState(State):
    def __init__(self, game):
        super().__init__(game)
        self.profile_manager = ProfileManager()
        self.audio = AudioManager()
        self.font = load_ui_font(32)
        self.small_font = load_ui_font(22)
        self.title_font = load_title_font(48)

        self.click_cooldown = 0.0
        self.selected_index = 0
        self.hovered_index = -1
        self._load_profiles()

        self.new_profile_btn = None
        self.back_btn = None
        self.delete_btns = []
        self.background = None
        self._load_background()

        self._update_buttons()

    def _load_background(self):
        bg_path = "assets/images/menu_bg.jpg"
        if os.path.exists(bg_path):
            try:
                self.background = pygame.image.load(bg_path).convert()
            except Exception:
                self.background = None
        else:
            self.background = None

    def _load_profiles(self):
        self.profiles = self.profile_manager.get_all_profiles()
        self.profiles.sort(key=lambda p: p.last_played, reverse=True)

    def _update_buttons(self):
        screen_w, screen_h = self.game.render_width, self.game.render_height
        btn_w = 220
        btn_h = 50
        center_x = screen_w // 2 - btn_w // 2

        self.new_profile_btn = pygame.Rect(center_x, screen_h - 130, btn_w, btn_h)
        self.back_btn = pygame.Rect(center_x, screen_h - 70, btn_w, btn_h)

    def _get_delete_btn(self, index: int) -> pygame.Rect:
        rect = self._get_profile_rect(index)
        return pygame.Rect(rect.right + 12, rect.y + 14, 32, 32)

    def _get_profile_rect(self, index: int) -> pygame.Rect:
        screen_w, screen_h = self.game.render_width, self.game.render_height
        item_height = 60
        spacing = 8
        total_height = len(self.profiles) * (item_height + spacing) - spacing
        start_y = (screen_h - total_height) // 2 - 40

        width = min(460, screen_w - 180)
        x = screen_w // 2 - width // 2
        y = start_y + index * (item_height + spacing)

        return pygame.Rect(x, y, width, item_height)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._go_back()
                elif event.key == pygame.K_UP:
                    self.selected_index = max(0, self.selected_index - 1)
                elif event.key == pygame.K_DOWN:
                    self.selected_index = min(len(self.profiles) - 1, self.selected_index + 1)
                elif event.key == pygame.K_RETURN:
                    self._select_profile()
                elif event.key == pygame.K_DELETE:
                    self._delete_selected()

            if event.type == pygame.MOUSEMOTION:
                self._handle_hover(event.pos)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.click_cooldown <= 0:
                    if self.new_profile_btn and self.new_profile_btn.collidepoint(event.pos):
                        self._create_new_profile()
                        return
                    if self.back_btn and self.back_btn.collidepoint(event.pos):
                        self._go_back()
                        return
                    self._handle_click(event.pos)

    def _handle_hover(self, pos):
        self.hovered_index = -1
        for i in range(len(self.profiles)):
            if self._get_profile_rect(i).collidepoint(pos):
                self.hovered_index = i
                break

    def _handle_click(self, pos):
        for i in range(len(self.profiles)):
            rect = self._get_profile_rect(i)
            if rect.collidepoint(pos):
                self.selected_index = i
                self._select_profile()
                return
            del_btn = self._get_delete_btn(i)
            if del_btn.collidepoint(pos):
                self.selected_index = i
                self._delete_selected()
                return

    def _select_profile(self):
        if 0 <= self.selected_index < len(self.profiles):
            profile = self.profiles[self.selected_index]
            self.profile_manager.load_profile(profile.name)
            self.audio.play_sound("button_click")

            from .menu.state import MenuState
            new_menu = MenuState(self.game, profile_manager=self.profile_manager, skip_check=True)
            self.game.state_manager.add_state('MENU', new_menu)
            self.game.state_manager.change_state('MENU')

    def _delete_selected(self):
        if 0 <= self.selected_index < len(self.profiles):
            profile = self.profiles[self.selected_index]
            self.profile_manager.delete_profile(profile.name)
            self.audio.play_sound("button_click")
            self._load_profiles()
            self.selected_index = min(self.selected_index, len(self.profiles) - 1)
            if self.selected_index < 0:
                self.selected_index = 0

    def _create_new_profile(self):
        self.audio.play_sound("button_click")
        from .profile_create_state import ProfileCreateState
        self.game.state_manager.add_state('PROFILE_CREATE', ProfileCreateState(self.game, from_select=True))
        self.game.state_manager.change_state('PROFILE_CREATE')

    def _go_back(self):
        self.audio.play_sound("button_click")
        self.game.state_manager.change_state('MENU')

    def update(self, dt):
        if self.click_cooldown > 0:
            self.click_cooldown -= dt

    def draw(self, screen):
        screen_w, screen_h = self.game.render_width, self.game.render_height
        self._update_buttons()

        screen.fill(STONE_DARK)
        if self.background:
            bg_scaled = pygame.transform.scale(self.background, (screen_w, screen_h))
            screen.blit(bg_scaled, (0, 0))
        else:
            self._draw_fallback_background(screen, screen_w, screen_h)

        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        screen.blit(overlay, (0, 0))

        title = self.title_font.render("SELECT PROFILE", True, GOLD)
        shadow = self.title_font.render("SELECT PROFILE", True, (0, 0, 0))
        tx = screen_w // 2 - title.get_width() // 2
        screen.blit(shadow, (tx + 3, 63))
        screen.blit(title, (tx, 60))

        sub_text = self.small_font.render(f"Profiles: {len(self.profiles)} / {ProfileManager.MAX_PROFILES}", True, PARCHMENT_DIM)
        screen.blit(sub_text, (screen_w // 2 - sub_text.get_width() // 2, 110))

        for i, profile in enumerate(self.profiles):
            rect = self._get_profile_rect(i)
            is_selected = i == self.selected_index
            is_hovered = i == self.hovered_index

            if is_selected:
                _draw_glow(screen, rect, TEAL_GLOW, pad=6, alpha=40)

            color = STONE_LIGHT if (is_selected or is_hovered) else STONE_MID
            bg_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            bg_surf.fill((*color, 220))
            screen.blit(bg_surf, (rect.x, rect.y))

            border = GOLD_BRIGHT if is_selected else (GOLD if is_hovered else GOLD_DIM)
            pygame.draw.rect(screen, border, rect, 2, border_radius=8)

            mode_icon = "N" if profile.mode == 'normal' else "H"
            mode_text = "Normal" if profile.mode == 'normal' else "Hardcore"
            text = f"[{mode_icon}] {profile.name}  {mode_text}  Level {profile.unlocked_level}/50"

            text_surf = self.font.render(text, True, PARCHMENT)
            screen.blit(text_surf, (rect.x + 20, rect.y + 15))

            del_btn = self._get_delete_btn(i)
            del_color = DANGER_BRIGHT if is_hovered else DANGER
            pygame.draw.rect(screen, del_color, del_btn, border_radius=5)
            pygame.draw.rect(screen, GOLD, del_btn, 2, border_radius=5)
            del_text = self.small_font.render("✕", True, PARCHMENT)
            screen.blit(del_text, (del_btn.x + 10, del_btn.y + 7))

        _draw_button(screen, self.new_profile_btn, "+ NEW PROFILE",
                     self.new_profile_btn and self.new_profile_btn.collidepoint(pygame.mouse.get_pos()))
        _draw_button(screen, self.back_btn, "← BACK TO MENU",
                     self.back_btn and self.back_btn.collidepoint(pygame.mouse.get_pos()))

        hint = self.small_font.render("ESC: Back to Menu  |  DEL: Delete Profile", True, PARCHMENT_DIM)
        screen.blit(hint, (screen_w // 2 - hint.get_width() // 2, screen_h - 30))

    def _draw_fallback_background(self, screen, screen_w, screen_h):
        for i in range(screen_h):
            t = i / screen_h
            r = int(15 + 30 * t)
            g = int(15 + 22 * t)
            b = int(30 + 55 * t)
            pygame.draw.line(screen, (r, g, b), (0, i), (screen_w, i))

    def on_resolution_changed(self, screen_w, screen_h):
        pass