# core/states/play/ui/tower_panel.py
import pygame
import os
from core.font_loader import load_ui_font
from core.theme import (
    GOLD, GOLD_BRIGHT, GOLD_DIM, STONE_DARK, STONE_MID, STONE_LIGHT,
    PARCHMENT, PARCHMENT_DIM, TEAL_GLOW, DANGER, DANGER_BRIGHT, SUCCESS
)


class TowerPanel:
    """Нижняя панель с башнями"""
    
    def __init__(self, state, small_font, tiny_font):
        self.state = state
        self.small_font = small_font
        self.tiny_font = tiny_font
        
        self.tower_buttons = []
        self.hovered_tower_index = -1
        
        self.panel_height = 0
        self.tower_cell_width = 0
        
        self._tower_sprites_cache = {}
        
        self.tower_data = [
            ('sniper', 'Снайпер', 100, 1),
            ('turret', 'Пулемёт', 80, 1),
            ('flamethrower', 'Огнемёт', 150, 5),
            ('electric', 'Электрическая', 120, 10),
            ('water', 'Водяная', 130, 12),
            ('acid', 'Кислотная', 140, 12),
            ('pvo', 'ПВО', 100, 15),
            ('freeze', 'Замораживающая', 140, 20),
            ('rocket', 'Ракетная', 180, 25),
            ('gate', 'Ворота', 150, 5),
            ('wall', 'Стена', 80, 5)
        ]
    
    def _get_scale(self):
        screen_w = self.state.game.render_width
        screen_h = self.state.game.render_height
        scale_x = screen_w / 1920
        scale_y = screen_h / 1080
        scale = min(scale_x, scale_y)
        scale = min(scale, 1.5)
        scale = max(scale, 0.5)
        return scale
    
    def update_sizes(self):
        scale = self._get_scale()
        
        # ✅ УВЕЛИЧЕНИЕ В 1.5 РАЗА
        panel_scale = scale * 1.5
        
        self.panel_height = int(95 * panel_scale)       # было 85 * scale
        self.tower_cell_width = int(105 * panel_scale)  # было 95 * scale
    
    def _load_tower_sprites(self):
        if self._tower_sprites_cache:
            return self._tower_sprites_cache
        
        sprites = {}
        tower_ids = ['sniper', 'turret', 'flamethrower', 'electric', 'water', 'pvo', 'freeze', 'acid', 'rocket']
        for tower_id in tower_ids:
            try:
                path = f"assets/images/towers/{tower_id}/level_1.png"
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    sprites[tower_id] = img
            except Exception:
                pass
        
        self._tower_sprites_cache = sprites
        return sprites
    
    def _draw_glow(self, screen, rect, color, pad=4, alpha=60, radius=6):
        glow = pygame.Surface((rect.width + pad * 2, rect.height + pad * 2), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*color, alpha), glow.get_rect(), border_radius=radius)
        screen.blit(glow, (rect.x - pad, rect.y - pad))
    
    def draw(self, screen):
        state = self.state
        screen_w = self.state.game.render_width
        screen_h = self.state.game.render_height
        
        scale = self._get_scale()
        panel_height = self.panel_height
        panel_y = screen_h - panel_height
        
        # Фон панели
        panel_surf = pygame.Surface((screen_w, panel_height), pygame.SRCALPHA)
        panel_surf.fill((*STONE_DARK, 225))
        screen.blit(panel_surf, (0, panel_y))
        pygame.draw.line(screen, GOLD, (0, panel_y), (screen_w, panel_y), 2)
        
        cell_width = self.tower_cell_width
        spacing = int(8 * scale)
        total_width = len(self.tower_data) * (cell_width + spacing) - spacing
        
        if total_width > screen_w - 20:
            cell_width = (screen_w - 20 - (len(self.tower_data) - 1) * spacing) // len(self.tower_data)
            cell_width = max(55, cell_width)
            total_width = len(self.tower_data) * (cell_width + spacing) - spacing
        
        start_x = (screen_w - total_width) // 2
        margin_y = int(6 * scale)
        inner_height = panel_height - margin_y * 2
        
        tower_sprites = self._load_tower_sprites()
        
        # ✅ Увеличенный размер спрайтов
        sprite_size = int(42 * scale)      # было 32 * scale
        sprite_size = max(28, min(60, sprite_size))
        
        self.tower_buttons = []
        
        for i, (tower_id, name, cost, unlock_level) in enumerate(self.tower_data):
            x = start_x + i * (cell_width + spacing)
            y = panel_y + margin_y
            
            is_unlocked = state.level_number >= unlock_level
            is_selected = state.selected_tower == tower_id and is_unlocked
            is_hovered = self.hovered_tower_index == i
            can_afford = state.player.gold >= cost
            
            rect = pygame.Rect(x, y, cell_width, inner_height)
            self.tower_buttons.append({
                'rect': rect,
                'tower_id': tower_id,
                'name': name,
                'cost': cost,
                'unlock_level': unlock_level,
                'is_unlocked': is_unlocked,
                'index': i
            })
            
            # Цвета
            if not is_unlocked:
                bg_color = STONE_DARK
                border_color = GOLD_DIM
                text_color = PARCHMENT_DIM
            elif is_selected:
                bg_color = STONE_LIGHT
                border_color = GOLD_BRIGHT
                text_color = GOLD_BRIGHT
                self._draw_glow(screen, rect, TEAL_GLOW, pad=4, alpha=55, radius=6)
            elif is_hovered and can_afford:
                bg_color = STONE_LIGHT
                border_color = GOLD_BRIGHT
                text_color = PARCHMENT
            else:
                bg_color = STONE_MID if can_afford else (35, 22, 20)
                border_color = GOLD if can_afford else DANGER
                text_color = PARCHMENT if can_afford else DANGER_BRIGHT
            
            # Фон ячейки
            bg_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            bg_surf.fill((*bg_color, 235))
            screen.blit(bg_surf, (rect.x, rect.y))
            pygame.draw.rect(screen, border_color, rect, 2, border_radius=int(4 * scale))
            
            # Спрайт башни
            sprite_x = x + int(4 * scale)
            sprite_y = y + int(4 * scale)
            sprite_rect = pygame.Rect(sprite_x, sprite_y, sprite_size, sprite_size)
            
            if tower_id in tower_sprites and is_unlocked:
                sprite = tower_sprites[tower_id]
                scaled = pygame.transform.scale(sprite, (sprite_size, sprite_size))
                screen.blit(scaled, (sprite_rect.x, sprite_rect.y))
            else:
                pygame.draw.rect(screen, STONE_DARK, sprite_rect, border_radius=int(3 * scale))
                pygame.draw.rect(screen, GOLD_DIM, sprite_rect, 2, border_radius=int(3 * scale))
                letter = name[0].upper()
                letter_font = load_ui_font(max(8, int(16 * scale)))
                letter_text = letter_font.render(letter, True, PARCHMENT_DIM)
                screen.blit(letter_text, (sprite_rect.x + sprite_rect.width // 2 - letter_text.get_width() // 2,
                                           sprite_rect.y + sprite_rect.height // 2 - letter_text.get_height() // 2))
                
                if not is_unlocked:
                    lv_font = load_ui_font(max(6, int(12 * scale)))
                    lv_text = lv_font.render(f"Lv.{unlock_level}", True, GOLD_DIM)
                    screen.blit(lv_text, (sprite_rect.x + sprite_rect.width // 2 - lv_text.get_width() // 2,
                                           sprite_rect.y + sprite_rect.height - int(4 * scale)))
            
            # Название башни
            name_x = x + sprite_size + int(6 * scale)
            name_y = y + int(4 * scale)
            name_text = self.small_font.render(name, True, text_color)
            screen.blit(name_text, (name_x, name_y))
            
            # Стоимость
            cost_y = name_y + int(18 * scale)
            cost_color = GOLD_BRIGHT if can_afford and is_unlocked else DANGER_BRIGHT
            cost_text = self.small_font.render(f"${cost}", True, cost_color)
            screen.blit(cost_text, (name_x, cost_y))
            
            # Клавиша
            key_y = cost_y + int(18 * scale)
            key_text = self.tiny_font.render(f"[{i + 1}]", True, PARCHMENT_DIM)
            screen.blit(key_text, (name_x, key_y))
            
            # Индикатор разблокировки
            if is_unlocked:
                indicator_size = int(8 * scale)
                indicator_size = max(4, min(12, indicator_size))
                pygame.draw.circle(screen, SUCCESS, (x + cell_width - indicator_size - 4, y + indicator_size + 4), indicator_size)
            else:
                lock_size = int(12 * scale)
                lock_size = max(8, min(18, lock_size))
                lock_font = load_ui_font(lock_size)
                lock_text = lock_font.render("🔒", True, GOLD_DIM)
                screen.blit(lock_text, (x + cell_width - lock_size - 4, y + 2))
    
    def get_height(self):
        return self.panel_height
    
    def get_buttons(self):
        return self.tower_buttons
    
    def set_hover(self, index):
        self.hovered_tower_index = index
    
    def get_hover(self):
        return self.hovered_tower_index