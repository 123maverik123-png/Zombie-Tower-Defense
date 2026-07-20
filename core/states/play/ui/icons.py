# core/states/play/ui/icons.py
import pygame
import os
from core.theme import GOLD, GOLD_BRIGHT, GOLD_DIM, STONE_DARK, TEAL_GLOW, DANGER_BRIGHT, PARCHMENT_DIM


class IconsManager:
    """Управление иконками для HUD"""
    
    def __init__(self, state):
        self.state = state
        self.icons = {}
        self._load_icons()
    
    def _get_scale(self):
        screen_w = self.state.game.render_width
        screen_h = self.state.game.render_height
        scale_x = screen_w / 1920
        scale_y = screen_h / 1080
        scale = min(scale_x, scale_y)
        scale = min(scale, 1.5)
        scale = max(scale, 0.5)
        return scale
    
    def _load_icons(self):
        """Загружает иконки из папки или создаёт заглушки"""
        icon_names = ['gold', 'heart', 'level', 'wave', 'enemy']
        for name in icon_names:
            try:
                path = f"assets/images/ui/{name}.png"
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    self.icons[name] = img
                else:
                    self.icons[name] = self._create_icon(name)
            except Exception as e:
                print(f"⚠️ Error loading icon {name}: {e}")
                self.icons[name] = self._create_icon(name)
    
    def _create_icon(self, name):
        """Создаёт иконку-заглушку"""
        scale = self._get_scale()
        size = int(24 * scale)
        size = max(16, min(40, size))
        
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))

        colors = {
            'gold': GOLD_BRIGHT,
            'heart': DANGER_BRIGHT,
            'level': GOLD,
            'wave': TEAL_GLOW,
            'enemy': PARCHMENT_DIM
        }
        color = colors.get(name, PARCHMENT_DIM)

        for r in range(size // 2 - 1, 2, -2):
            alpha = int(255 * (r / (size // 2)))
            pygame.draw.circle(surf, (*color[:3], alpha), (size // 2, size // 2), r)

        pygame.draw.circle(surf, (*GOLD, 220), (size // 2, size // 2), size // 2 - 2, 1)

        try:
            font = pygame.font.Font(None, size - 6)
            letter = name[0].upper()
            text = font.render(letter, True, STONE_DARK)
            surf.blit(text, (size // 2 - text.get_width() // 2, size // 2 - text.get_height() // 2))
        except Exception:
            pass

        return surf
    
    def get(self, name, size=24):
        """Возвращает иконку с масштабированием"""
        scale = self._get_scale()
        scaled_size = int(size * scale)
        scaled_size = max(16, min(40, scaled_size))
        
        if name in self.icons:
            icon = self.icons[name]
            if icon.get_width() != scaled_size:
                return pygame.transform.scale(icon, (scaled_size, scaled_size))
            return icon
        return None