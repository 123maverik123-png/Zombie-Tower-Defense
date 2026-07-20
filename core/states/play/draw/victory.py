# core/states/play/draw/victory.py
import pygame
from services.profile_manager import ProfileManager
from core.font_loader import load_ui_font, load_title_font
from core.theme import (
    GOLD, GOLD_BRIGHT, STONE_DARK, STONE_MID, STONE_LIGHT,
    PARCHMENT, PARCHMENT_DIM, TEAL_GLOW, SUCCESS
)


class VictoryDraw:
    """Экран победы в стиле главного меню (каменное фэнтези)"""

    def __init__(self, state):
        self.state = state
        self.title_font = load_title_font(64)
        self.font = load_ui_font(30)
        self.small_font = load_ui_font(22)
        self.btn_font = load_ui_font(32)

        self._mouse_was_pressed = True  # съедаем клик, которым добили волну
        self._victory_sound_played = False

    def draw(self, screen):
        """Рисует экран победы"""
        state = self.state
        w, h = state.game.render_width, state.game.render_height

        if not self._victory_sound_played:
            self._victory_sound_played = True
            if state.audio.settings.music_enabled:
                state.audio.play_music("victory_theme.wav")

        # Затемнение всего экрана
        dim = pygame.Surface((w, h), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 170))
        screen.blit(dim, (0, 0))

        # Панель по центру
        panel_w, panel_h = 520, 460
        panel_rect = pygame.Rect((w - panel_w) // 2, (h - panel_h) // 2 - 20, panel_w, panel_h)

        panel_surface = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surface.fill((10, 9, 8, 200))
        screen.blit(panel_surface, panel_rect.topleft)
        pygame.draw.rect(screen, GOLD, panel_rect, 2, border_radius=8)

        # Заголовок с тенью (шрифт ToxicRot, как в главном меню)
        title = self.title_font.render("VICTORY", True, GOLD)
        shadow = self.title_font.render("VICTORY", True, (0, 0, 0))
        tx = panel_rect.centerx - title.get_width() // 2
        ty = panel_rect.y + 28
        screen.blit(shadow, (tx + 3, ty + 3))
        screen.blit(title, (tx, ty))

        subtitle = self.small_font.render(
            f"— Level {state.level_number} defended —", True, PARCHMENT)
        screen.blit(subtitle, (panel_rect.centerx - subtitle.get_width() // 2,
                               ty + title.get_height() + 6))

        # Разделитель
        line_y = ty + title.get_height() + 40
        pygame.draw.line(screen, (90, 80, 60),
                         (panel_rect.x + 40, line_y), (panel_rect.right - 40, line_y))

        # Статистика: метка слева, значение справа
        stats = [
            ("Kills", f"{state.player.stats.get('total_kills', 0)}", PARCHMENT),
            ("Gold", f"{state.player.gold}", GOLD_BRIGHT),
            ("Lives left", f"{state.player.lives}", SUCCESS),
        ]
        sy = line_y + 24
        for label, value, color in stats:
            lbl = self.font.render(label, True, PARCHMENT_DIM)
            val = self.font.render(value, True, color)
            screen.blit(lbl, (panel_rect.x + 60, sy))
            screen.blit(val, (panel_rect.right - 60 - val.get_width(), sy))
            sy += 42

        # Кнопки
        btn_w, btn_h = 380, 62
        next_btn = pygame.Rect(panel_rect.centerx - btn_w // 2, sy + 18, btn_w, btn_h)
        menu_btn = pygame.Rect(panel_rect.centerx - btn_w // 2, sy + 18 + btn_h + 16, btn_w, btn_h)

        mx, my = self._get_mouse()
        is_last_level = state.level_number >= 50

        buttons = []
        if not is_last_level:
            buttons.append((next_btn, "NEXT LEVEL", self._go_to_next_level))
        buttons.append((menu_btn, "LEVEL SELECT", self._go_to_level_select))

        pressed = pygame.mouse.get_pressed()[0]
        clicked = pressed and not self._mouse_was_pressed
        self._mouse_was_pressed = pressed

        for rect, text, action in buttons:
            hovered = rect.collidepoint(mx, my)
            self._draw_button(screen, rect, text, hovered)
            if clicked and hovered:
                state.audio.play_sound("button_click")
                action()
                return

    def _get_mouse(self):
        mx, my = pygame.mouse.get_pos()
        converted = self.state.game._convert_mouse_pos((mx, my))
        if converted:
            return int(converted[0]), int(converted[1])
        return -1, -1

    def _draw_button(self, screen, rect, text, hovered):
        """Кнопка в стиле главного меню: тень, камень, золотая рамка, свечение"""
        # Тень
        shadow_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 120))
        screen.blit(shadow_surf, (rect.x + 4, rect.y + 5))

        # Свечение при наведении (под кнопкой)
        if hovered:
            glow = pygame.Surface((rect.width + 20, rect.height + 20), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*TEAL_GLOW, 70), glow.get_rect(), border_radius=12)
            screen.blit(glow, (rect.x - 10, rect.y - 10))

        # Фон
        base_color = STONE_LIGHT if hovered else STONE_MID
        btn_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        btn_surf.fill((*base_color, 240))
        screen.blit(btn_surf, rect.topleft)

        # Рамка
        border_color = GOLD_BRIGHT if hovered else GOLD
        pygame.draw.rect(screen, border_color, rect, 3, border_radius=8)

        # Текст
        title_color = GOLD_BRIGHT if hovered else PARCHMENT
        t = self.btn_font.render(text, True, title_color)
        screen.blit(t, (rect.centerx - t.get_width() // 2,
                        rect.centery - t.get_height() // 2))

    def _go_to_next_level(self):
        """Переход на следующий уровень"""
        state = self.state
        next_lvl = state.level_number + 1

        if next_lvl <= 50:
            pm = ProfileManager()
            profile = pm.get_current_profile()
            if profile:
                profile.current_level = next_lvl
                pm.save_profile(profile)

            if state.audio.settings.music_enabled:
                state.audio.play_music("game_theme.wav")

            from core.states.play.state import PlayState
            state.game.state_manager.add_state('PLAYING', PlayState(state.game, next_lvl))
            state.game.state_manager.change_state('PLAYING')

    def _go_to_level_select(self):
        """Переход в меню выбора уровней"""
        state = self.state
        if state.audio.settings.music_enabled:
            state.audio.play_music("menu_theme.wav")
        state.game.state_manager.change_state('LEVEL_SELECT')
