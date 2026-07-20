# ui/settings/draw.py
import pygame
from core.theme import GOLD, GOLD_BRIGHT, GOLD_DIM, STONE_DARK, STONE_MID, STONE_LIGHT, PARCHMENT, TEAL_GLOW


def draw_glow(screen, rect, color, pad=8, alpha=60, radius=10):
    """Рисует свечение вокруг прямоугольника"""
    glow = pygame.Surface((rect.width + pad * 2, rect.height + pad * 2), pygame.SRCALPHA)
    pygame.draw.rect(glow, (*color, alpha), glow.get_rect(), border_radius=radius)
    screen.blit(glow, (rect.x - pad, rect.y - pad))


def draw_button(screen, rect, text, hovered=False, color=STONE_MID, border_color=GOLD, font=None):
    """Рисует кнопку с тенью и свечением"""
    if font is None:
        from core.font_loader import load_ui_font
        font = load_ui_font(28)
    
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
        draw_glow(screen, rect, TEAL_GLOW, pad=8, alpha=55, radius=10)

    border = GOLD_BRIGHT if hovered else border_color
    pygame.draw.rect(screen, border, rect, 2, border_radius=6)

    text_color = GOLD_BRIGHT if hovered else PARCHMENT
    text_surf = font.render(text, True, text_color)
    screen.blit(text_surf, (rect.x + (rect.width - text_surf.get_width()) // 2,
                            rect.y + (rect.height - text_surf.get_height()) // 2))