# core/states/menu/draw.py
import pygame
from core.font_loader import load_ui_font, load_title_font
from core.theme import GOLD, GOLD_BRIGHT, GOLD_DIM, STONE_DARK, STONE_MID, STONE_LIGHT, PARCHMENT, TEAL_GLOW
from .utils import draw_fallback_background


class MenuDraw:
    """Отрисовка главного меню"""
    
    def __init__(self, state):
        self.state = state
        self.font = load_ui_font(24)
        self.small_font = load_ui_font(20)
    
    def draw(self, screen):
        state = self.state
        screen_w, screen_h = state.game.render_width, state.game.render_height

        self._draw_background(screen, screen_w, screen_h)
        self._draw_left_panel(screen, screen_w, screen_h)
        self._draw_title(screen, screen_w, screen_h)
        self._draw_profile_info(screen, screen_w, screen_h)
        self._draw_buttons(screen)
        self._draw_version(screen, screen_w, screen_h)

    def _draw_background(self, screen, screen_w, screen_h):
        state = self.state
        screen.fill(STONE_DARK)
        
        if state.background:
            bg_scaled = pygame.transform.scale(state.background, (screen_w, screen_h))
            screen.blit(bg_scaled, (0, 0))
        else:
            draw_fallback_background(screen, screen_w, screen_h)

        # Затемнение слева для читаемости
        vignette = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        grad_w = int(screen_w * 0.45)
        for i in range(grad_w):
            alpha = int(220 * (1 - i / grad_w))
            pygame.draw.line(vignette, (0, 0, 0, alpha), (i, 0), (i, screen_h))
        screen.blit(vignette, (0, 0))

        # Теневой градиент сверху
        top_shade = pygame.Surface((screen_w, 160), pygame.SRCALPHA)
        for i in range(160):
            alpha = int(160 * (1 - i / 160))
            pygame.draw.line(top_shade, (0, 0, 0, alpha), (0, i), (screen_w, i))
        screen.blit(top_shade, (0, 0))

    def _draw_left_panel(self, screen, screen_w, screen_h):
        state = self.state
        panel_rect = state.panel_rect
        
        panel_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel_surface.fill((10, 9, 8, 160))
        screen.blit(panel_surface, (panel_rect.x, panel_rect.y))
        pygame.draw.rect(screen, GOLD, panel_rect, 2, border_radius=8)

    def _draw_title(self, screen, screen_w, screen_h):
        state = self.state
        panel_rect = state.panel_rect
        
        title_font = load_title_font(72)
        subtitle_font = load_ui_font(28)
        
        title = title_font.render("ZOMBIE TD", True, GOLD)
        shadow = title_font.render("ZOMBIE TD", True, (0, 0, 0))
        
        tx = panel_rect.x + 30
        ty = panel_rect.y - 100
        
        screen.blit(shadow, (tx + 3, ty + 3))
        screen.blit(title, (tx, ty))

        subtitle = subtitle_font.render("— Defend the Realm —", True, PARCHMENT)
        screen.blit(subtitle, (tx + 6, ty + title.get_height() + 8))

    def _draw_profile_info(self, screen, screen_w, screen_h):
        state = self.state
        profile = state.profile_manager.get_current_profile()
        
        x = state.panel_rect.x + 30
        y = state.panel_rect.y + 20

        if profile:
            mode_icon = "N" if profile.mode == 'normal' else "H"
            mode_text = "Normal" if profile.mode == 'normal' else "Hardcore"

            welcome = self.font.render(f"[{mode_icon}] {profile.name}", True, PARCHMENT)
            screen.blit(welcome, (x, y))

            mode_info = self.small_font.render(
                f"{mode_text} Mode  •  Level {profile.unlocked_level}/50", True, (170, 160, 140)
            )
            screen.blit(mode_info, (x, y + 34))
        else:
            no_profile = self.font.render("⚠️ No profile loaded", True, (220, 160, 90))
            screen.blit(no_profile, (x, y))

    def _draw_buttons(self, screen):
        state = self.state
        for btn in state.buttons.values():
            self._draw_button(screen, btn)

    def _draw_button(self, screen, btn):
        rect = btn.rect

        # Тень
        shadow_rect = rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 5
        shadow_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 120))
        screen.blit(shadow_surf, shadow_rect.topleft)

        # Фон кнопки
        base_color = STONE_LIGHT if btn.hovered else STONE_MID
        btn_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        btn_surf.fill((*base_color, 240))
        screen.blit(btn_surf, rect.topleft)

        # Рамка
        border_color = GOLD_BRIGHT if btn.hovered else GOLD
        pygame.draw.rect(screen, border_color, rect, 3, border_radius=8)

        # Свечение при наведении
        if btn.hovered:
            glow = pygame.Surface((rect.width + 20, rect.height + 20), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*TEAL_GLOW, 70), glow.get_rect(), border_radius=12)
            screen.blit(glow, (rect.x - 10, rect.y - 10))
            pygame.draw.rect(screen, border_color, rect, 3, border_radius=8)

        # Иконка
        icon_size = 56
        icon_x = rect.x + 20
        icon_y = rect.y + (rect.height - icon_size) // 2
        if btn.icon:
            icon_scaled = pygame.transform.smoothscale(btn.icon, (icon_size, icon_size))
            screen.blit(icon_scaled, (icon_x, icon_y))
        else:
            pygame.draw.rect(screen, GOLD, (icon_x, icon_y, icon_size, icon_size), 2, border_radius=6)

        # Текст
        btn_title_font = load_ui_font(34)
        btn_sub_font = load_ui_font(20)
        
        text_x = icon_x + icon_size + 20
        title_color = GOLD_BRIGHT if btn.hovered else PARCHMENT
        title_surf = btn_title_font.render(btn.title, True, title_color)
        screen.blit(title_surf, (text_x, rect.y + 18))

        if btn.subtitle:
            sub_surf = btn_sub_font.render(btn.subtitle, True, (160, 150, 130))
            screen.blit(sub_surf, (text_x, rect.y + 18 + title_surf.get_height() + 6))

    def _draw_version(self, screen, screen_w, screen_h):
        version = pygame.font.Font(None, 20).render("v1.5.2", True, (140, 130, 110))
        screen.blit(version, (screen_w - 90, screen_h - 30))