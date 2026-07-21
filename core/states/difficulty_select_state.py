# core/states/difficulty_select_state.py
"""Окно выбора сложности перед первым запуском игры на профиле.

Показывается из меню, когда у профиля ещё не выбрана сложность
(profile.difficulty is None). После выбора MEDIUM/HARD и нажатия START
сложность привязывается к профилю навсегда и игра запускается.
"""
import pygame
import os
from core.state_manager import State
from core.audio import AudioManager
from services.profile_manager import ProfileManager
from core.level_loader import build_level
from core.event_bus import EventBus
from core.font_loader import load_ui_font, load_title_font
from core.theme import (
    GOLD, GOLD_BRIGHT, GOLD_DIM, STONE_DARK, STONE_MID,
    PARCHMENT, PARCHMENT_DIM, TEAL_GLOW, DANGER, DANGER_BRIGHT, SUCCESS
)


def _draw_glow(screen, rect, color=TEAL_GLOW, pad=8, alpha=60, radius=10):
    glow = pygame.Surface((rect.width + pad * 2, rect.height + pad * 2), pygame.SRCALPHA)
    pygame.draw.rect(glow, (*color, alpha), glow.get_rect(), border_radius=radius)
    screen.blit(glow, (rect.x - pad, rect.y - pad))


class DifficultySelectState(State):
    def __init__(self, game):
        super().__init__(game)
        self.profile_manager = ProfileManager()
        self.audio = AudioManager()

        self.font = load_ui_font(28)
        self.small_font = load_ui_font(20)
        self.title_font = load_title_font(40)

        self.difficulty = 'medium'  # выбор по умолчанию
        self.click_cooldown = 0.15
        self.background = None
        self._load_background()

        self.dialog_rect = None
        self.medium_btn = None
        self.hard_btn = None
        self.start_btn = None
        self._update_ui()

    def _load_background(self):
        bg_path = "assets/images/menu_bg.jpg"
        if os.path.exists(bg_path):
            try:
                self.background = pygame.image.load(bg_path).convert()
            except Exception:
                self.background = None

    def _update_ui(self):
        sw, sh = self.game.render_width, self.game.render_height
        self.dialog_rect = pygame.Rect(sw // 2 - 280, sh // 2 - 200, 560, 400)
        x = self.dialog_rect.x + 40
        y = self.dialog_rect.y + 110
        self.medium_btn = pygame.Rect(x, y, 220, 60)
        self.hard_btn = pygame.Rect(x + 260, y, 220, 60)
        self.start_btn = pygame.Rect(self.dialog_rect.x + 140, y + 190, 280, 56)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._back_to_menu()
                elif event.key == pygame.K_RETURN:
                    self._start_game()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.click_cooldown > 0:
                    continue
                if self.medium_btn.collidepoint(event.pos):
                    self.difficulty = 'medium'
                    self.audio.play_sound("button_click", volume_override=0.3)
                elif self.hard_btn.collidepoint(event.pos):
                    self.difficulty = 'hard'
                    self.audio.play_sound("button_click", volume_override=0.3)
                elif self.start_btn.collidepoint(event.pos):
                    self._start_game()

    def _start_game(self):
        profile = self.profile_manager.get_current_profile()
        if not profile:
            self._back_to_menu()
            return

        # Привязываем сложность к профилю навсегда
        profile.difficulty = self.difficulty
        self.profile_manager.save_profile(profile)
        self.audio.play_sound("button_click")

        # Запуск боя через интро-сцену (сглаживает резкий переход;
        # при первом заходе покажет сюжетное интро, дальше — карточку уровня).
        from .intro_state import launch_game_with_intro
        launch_game_with_intro(self.game, profile, self.audio)

    def _back_to_menu(self):
        self.audio.play_sound("button_click")
        self.game.state_manager.change_state('MENU')

    def update(self, dt):
        if self.click_cooldown > 0:
            self.click_cooldown -= dt

    def _draw_mode_btn(self, screen, rect, label, selected, accent, accent_bright, sub):
        color = accent if selected else STONE_MID
        border = accent_bright if selected else GOLD_DIM
        if selected:
            _draw_glow(screen, rect, TEAL_GLOW, pad=6, alpha=45)
        pygame.draw.rect(screen, color, rect, border_radius=8)
        pygame.draw.rect(screen, border, rect, 3 if selected else 2, border_radius=8)
        text = self.font.render(label, True, PARCHMENT if selected else PARCHMENT_DIM)
        screen.blit(text, (rect.x + (rect.width - text.get_width()) // 2, rect.y + 8))
        stext = self.small_font.render(sub, True, PARCHMENT if selected else PARCHMENT_DIM)
        screen.blit(stext, (rect.x + (rect.width - stext.get_width()) // 2, rect.y + 36))

    def draw(self, screen):
        sw, sh = self.game.render_width, self.game.render_height
        self._update_ui()

        screen.fill(STONE_DARK)
        if self.background:
            screen.blit(pygame.transform.scale(self.background, (sw, sh)), (0, 0))
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        dialog_surf = pygame.Surface((self.dialog_rect.width, self.dialog_rect.height), pygame.SRCALPHA)
        dialog_surf.fill((20, 18, 16, 240))
        screen.blit(dialog_surf, (self.dialog_rect.x, self.dialog_rect.y))
        pygame.draw.rect(screen, GOLD, self.dialog_rect, 2, border_radius=10)

        # Заголовок
        y = self.dialog_rect.y + 30
        title = self.title_font.render("SELECT DIFFICULTY", True, GOLD)
        shadow = self.title_font.render("SELECT DIFFICULTY", True, (0, 0, 0))
        tx = self.dialog_rect.x + (self.dialog_rect.width - title.get_width()) // 2
        screen.blit(shadow, (tx + 2, y + 2))
        screen.blit(title, (tx, y))

        hint = self.small_font.render("Choose once — it stays for this profile", True, PARCHMENT_DIM)
        screen.blit(hint, (self.dialog_rect.x + (self.dialog_rect.width - hint.get_width()) // 2, y + 50))

        # Кнопки сложности
        self._draw_mode_btn(screen, self.medium_btn, "MEDIUM", self.difficulty == 'medium',
                            SUCCESS, GOLD_BRIGHT, "Balanced")
        self._draw_mode_btn(screen, self.hard_btn, "HARD", self.difficulty == 'hard',
                            DANGER, DANGER_BRIGHT, "Tougher, faster foes")

        # Описание выбранного
        desc_y = self.medium_btn.bottom + 24
        if self.difficulty == 'hard':
            desc = self.small_font.render("Enemies: +28% HP, +12% gold. For veterans.", True, DANGER_BRIGHT)
        else:
            desc = self.small_font.render("Standard balance. Recommended for first playthrough.", True, GOLD_BRIGHT)
        screen.blit(desc, (self.dialog_rect.x + (self.dialog_rect.width - desc.get_width()) // 2, desc_y))

        # Кнопка START
        start_btn = self.start_btn
        if start_btn.collidepoint(pygame.mouse.get_pos()):
            _draw_glow(screen, start_btn, TEAL_GLOW, pad=6, alpha=45)
        pygame.draw.rect(screen, SUCCESS, start_btn, border_radius=8)
        pygame.draw.rect(screen, GOLD_BRIGHT, start_btn, 2, border_radius=8)
        text = self.font.render("START", True, PARCHMENT)
        screen.blit(text, (start_btn.x + (start_btn.width - text.get_width()) // 2, start_btn.y + 14))

    def on_resolution_changed(self, screen_w, screen_h):
        self._update_ui()
