# core/states/menu/utils.py
import pygame
import os


def load_background():
    """Загружает фоновое изображение"""
    bg_path = "assets/images/menu_bg.jpg"
    if os.path.exists(bg_path):
        try:
            return pygame.image.load(bg_path).convert()
        except Exception:
            return None
    return None


def load_icons():
    """Загружает иконки для кнопок меню"""
    icon_files = {
        'play': 'icon_play.png',
        'levels': 'icon_levels.png',
        'settings': 'icon_settings.png',
        'switch': 'icon_switch.png',
        'editor': 'icon_editor.png',
        'exit': 'icon_exit.png',
    }
    icons = {}
    for key, fname in icon_files.items():
        path = f"assets/images/icons/{fname}"
        if os.path.exists(path):
            try:
                icons[key] = pygame.image.load(path).convert_alpha()
            except Exception:
                icons[key] = None
        else:
            icons[key] = None
    return icons


def draw_fallback_background(screen, screen_w, screen_h):
    """Рисует фоновую заглушку"""
    import random
    random.seed(42)
    
    for i in range(screen_h):
        t = i / screen_h
        r = int(15 + 30 * t)
        g = int(15 + 22 * t)
        b = int(30 + 55 * t)
        pygame.draw.line(screen, (r, g, b), (0, i), (screen_w, i))
    
    for _ in range(80):
        x = random.randint(0, screen_w)
        y = random.randint(0, screen_h)
        size = random.randint(1, 3)
        pygame.draw.circle(screen, (255, 255, 255), (x, y), size)