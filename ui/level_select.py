# ui/level_select.py
import pygame
import os
import json
from typing import Optional, List, Dict
from services.profile_manager import Profile
from core.font_loader import load_ui_font, load_title_font
from core.theme import (
    GOLD, GOLD_BRIGHT, GOLD_DIM, STONE_DARK, STONE_MID, STONE_LIGHT,
    PARCHMENT, PARCHMENT_DIM, TEAL_GLOW, SUCCESS, DANGER
)


def _draw_glow(screen, rect, color, pad=6, alpha=40, radius=8):
    glow = pygame.Surface((rect.width + pad * 2, rect.height + pad * 2), pygame.SRCALPHA)
    pygame.draw.rect(glow, (*color, alpha), glow.get_rect(), border_radius=radius)
    screen.blit(glow, (rect.x - pad, rect.y - pad))


class LevelSelectUI:
    def __init__(self, profile, game):  # ✅ Добавлен game
        self.profile = profile
        self.game = game  # ✅ Сохраняем ссылку
        self.font = load_ui_font(24)
        self.big_font = load_title_font(44)
        self.small_font = load_ui_font(18)

        self.unlocked_level = profile.unlocked_level
        self.completed_levels = profile.completed_levels

        # Константы
        self.columns = 10
        self.total_levels = 50
        self.rows = 5

        # Базовые параметры (будут пересчитаны в draw)
        self.cell_size = 52
        self.cell_spacing = 6
        self.grid_start_x = 80
        self.grid_start_y = 160

        self.custom_maps = []
        self._load_custom_maps()
        self.selected_custom_index = 0
        self.show_custom = False

        self.selected_level = None
        self.hovered_level = None

        self.back_btn = pygame.Rect(540, 650, 200, 50)
        self.custom_btn = pygame.Rect(540, 590, 200, 50)

        self.scroll_offset = 0
        self.custom_scroll = 0
        self.back_custom_btn = None

        self._last_screen_w = 0
        self._last_screen_h = 0

    def _calculate_layout(self, screen_w, screen_h):
        """Пересчитывает размеры сетки так, чтобы было ровно 5 строк"""
        top_margin = 160
        bottom_margin = 180
        side_margin = 80

        available_width = screen_w - side_margin * 2
        available_height = screen_h - top_margin - bottom_margin

        cell_from_width = (available_width - (self.columns - 1) * self.cell_spacing) // self.columns
        cell_from_height = (available_height - (self.rows - 1) * self.cell_spacing) // self.rows

        self.cell_size = min(cell_from_width, cell_from_height)
        self.cell_size = max(30, self.cell_size)

        total_width = self.columns * self.cell_size + (self.columns - 1) * self.cell_spacing
        total_height = self.rows * self.cell_size + (self.rows - 1) * self.cell_spacing

        self.grid_start_x = (screen_w - total_width) // 2
        self.grid_start_y = top_margin + (available_height - total_height) // 2

        scale = min(screen_w / 1920, screen_h / 1080, 1.5)
        font_size = max(16, int(24 * scale))
        small_size = max(12, int(18 * scale))
        self.font = load_ui_font(font_size)
        self.small_font = load_ui_font(small_size)

        btn_scale = min(scale, 1.2)
        btn_w = int(200 * btn_scale)
        btn_h = int(50 * btn_scale)
        spacing_btn = int(10 * btn_scale)

        self.back_btn = pygame.Rect(
            screen_w // 2 - btn_w // 2,
            screen_h - bottom_margin + 20,
            btn_w,
            btn_h
        )
        self.custom_btn = pygame.Rect(
            screen_w // 2 - btn_w // 2,
            screen_h - bottom_margin - btn_h - spacing_btn,
            btn_w,
            btn_h
        )

    def _load_custom_maps(self):
        maps_dir = 'data/maps'
        if not os.path.exists(maps_dir):
            os.makedirs(maps_dir, exist_ok=True)
            return

        self.custom_maps = []
        for filename in os.listdir(maps_dir):
            if filename.endswith('.json'):
                try:
                    with open(f"{maps_dir}/{filename}", 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.custom_maps.append({
                            'name': data.get('name', filename.replace('.json', '')),
                            'filename': filename,
                            'data': data
                        })
                except Exception as e:
                    print(f"Error loading custom map {filename}: {e}")

        self.custom_maps.sort(key=lambda x: x['name'])

    def is_unlocked(self, level: int) -> bool:
        return level <= self.unlocked_level

    def is_completed(self, level: int) -> bool:
        return level in self.completed_levels

    def get_level_at_pos(self, pos: tuple) -> Optional[int]:
        if self.show_custom:
            return None

        x, y = pos
        for level in range(1, 51):
            col = (level - 1) % self.columns
            row = (level - 1) // self.columns
            cell_x = self.grid_start_x + col * (self.cell_size + self.cell_spacing)
            cell_y = self.grid_start_y + row * (self.cell_size + self.cell_spacing)
            rect = pygame.Rect(cell_x, cell_y, self.cell_size, self.cell_size)
            if rect.collidepoint(x, y):
                return level
        return None

    def get_custom_at_pos(self, pos: tuple) -> Optional[int]:
        if not self.show_custom or not self.custom_maps:
            return None

        x, y = pos
        start_x = 100
        start_y = 160
        item_height = 48
        item_width = 400

        for i in range(len(self.custom_maps)):
            rect = pygame.Rect(start_x, start_y + i * (item_height + 8) - self.custom_scroll,
                               item_width, item_height)
            if rect.collidepoint(x, y):
                return i
        return None

    def update_hover(self, pos: tuple):
        if self.show_custom:
            self.hovered_level = self.get_custom_at_pos(pos)
        else:
            self.hovered_level = self.get_level_at_pos(pos)

    def handle_click(self, pos: tuple) -> bool:
        if self.show_custom:
            idx = self.get_custom_at_pos(pos)
            if idx is not None and 0 <= idx < len(self.custom_maps):
                self.selected_custom_index = idx
                return True
        else:
            level = self.get_level_at_pos(pos)
            if level and self.is_unlocked(level):
                self.selected_level = level
                return True
        return False

    def toggle_custom(self):
        self.show_custom = not self.show_custom
        self._load_custom_maps()

    def handle_delete_click(self, pos: tuple) -> Optional[str]:
        if not self.show_custom:
            return None

        for custom_map in self.custom_maps:
            if 'delete_btn' in custom_map and custom_map['delete_btn'].collidepoint(pos):
                return custom_map['filename']
        return None

    def get_custom_maps(self) -> List[Dict]:
        return self.custom_maps

    def draw(self, screen):
        screen_w, screen_h = self.game.render_width, self.game.render_height  # ✅ Теперь работает

        if screen_w != self._last_screen_w or screen_h != self._last_screen_h:
            self._calculate_layout(screen_w, screen_h)
            self._last_screen_w = screen_w
            self._last_screen_h = screen_h

        title = self.big_font.render("CUSTOM LEVELS" if self.show_custom else "SELECT LEVEL", True, GOLD)
        shadow = self.big_font.render("CUSTOM LEVELS" if self.show_custom else "SELECT LEVEL", True, (0, 0, 0))
        tx = screen_w // 2 - title.get_width() // 2
        screen.blit(shadow, (tx + 2, 32))
        screen.blit(title, (tx, 30))

        if not self.show_custom:
            progress = len(self.completed_levels)
            info = self.font.render(f"Progress: {progress}/50", True, PARCHMENT_DIM)
            screen.blit(info, (screen_w // 2 - info.get_width() // 2, 88))
        else:
            info = self.font.render(f"Custom maps: {len(self.custom_maps)}", True, PARCHMENT_DIM)
            screen.blit(info, (screen_w // 2 - info.get_width() // 2, 88))

        if not self.show_custom:
            legend_x = screen_w - 220
            legend_y = 70

            pygame.draw.rect(screen, SUCCESS, (legend_x, legend_y, 14, 14))
            t = self.small_font.render("Completed", True, PARCHMENT_DIM)
            screen.blit(t, (legend_x + 20, legend_y - 2))

            pygame.draw.rect(screen, GOLD, (legend_x, legend_y + 22, 14, 14))
            t = self.small_font.render("Available", True, PARCHMENT_DIM)
            screen.blit(t, (legend_x + 20, legend_y + 20))

            pygame.draw.rect(screen, STONE_DARK, (legend_x, legend_y + 44, 14, 14))
            pygame.draw.rect(screen, STONE_MID, (legend_x, legend_y + 44, 14, 14), 1)
            t = self.small_font.render("Locked", True, PARCHMENT_DIM)
            screen.blit(t, (legend_x + 20, legend_y + 42))

        if not self.show_custom:
            for level in range(1, 51):
                col = (level - 1) % self.columns
                row = (level - 1) // self.columns
                cell_x = self.grid_start_x + col * (self.cell_size + self.cell_spacing)
                cell_y = self.grid_start_y + row * (self.cell_size + self.cell_spacing)

                is_unlocked = self.is_unlocked(level)
                is_completed = self.is_completed(level)
                is_hovered = self.hovered_level == level

                if is_completed:
                    bg_color = SUCCESS
                    border = GOLD_BRIGHT
                elif is_unlocked:
                    bg_color = STONE_LIGHT
                    border = GOLD
                else:
                    bg_color = STONE_DARK
                    border = STONE_MID

                rect = pygame.Rect(cell_x, cell_y, self.cell_size, self.cell_size)

                if is_hovered and is_unlocked:
                    _draw_glow(screen, rect, TEAL_GLOW, pad=4, alpha=50)

                pygame.draw.rect(screen, bg_color, rect, border_radius=4)
                pygame.draw.rect(screen, border, rect, 2, border_radius=4)

                text = self.font.render(str(level), True, PARCHMENT)
                screen.blit(text, (cell_x + (self.cell_size - text.get_width()) // 2,
                                   cell_y + (self.cell_size - text.get_height()) // 2))

                if is_completed:
                    check = self.small_font.render("✓", True, GOLD_BRIGHT)
                    screen.blit(check, (cell_x + 4, cell_y + 2))

        else:
            if self.custom_maps:
                start_x = 100
                start_y = 160
                item_width = 420
                item_height = 48

                for i, custom_map in enumerate(self.custom_maps):
                    rect = pygame.Rect(start_x, start_y + i * (item_height + 8) - self.custom_scroll,
                                       item_width, item_height)

                    is_hovered = self.hovered_level == i
                    color = STONE_LIGHT if is_hovered else STONE_MID

                    if is_hovered:
                        _draw_glow(screen, rect, TEAL_GLOW, pad=4, alpha=40)

                    pygame.draw.rect(screen, color, rect, border_radius=6)
                    pygame.draw.rect(screen, GOLD_DIM if is_hovered else GOLD_DIM, rect, 2, border_radius=6)

                    name_text = self.font.render(custom_map['name'], True, PARCHMENT)
                    screen.blit(name_text, (rect.x + 16, rect.y + 12))

                    size_text = self.small_font.render(
                        f"{custom_map['data'].get('width', 0)}x{custom_map['data'].get('height', 0)}",
                        True, PARCHMENT_DIM)
                    screen.blit(size_text, (rect.x + 260, rect.y + 14))

                    del_btn = pygame.Rect(rect.x + rect.width - 44, rect.y + 10, 28, 28)
                    pygame.draw.rect(screen, DANGER, del_btn, border_radius=4)
                    pygame.draw.rect(screen, GOLD, del_btn, 2, border_radius=4)
                    del_text = self.small_font.render("X", True, PARCHMENT)
                    screen.blit(del_text, (del_btn.x + 8, del_btn.y + 5))
                    custom_map['delete_btn'] = del_btn

                self.back_custom_btn = pygame.Rect(screen_w // 2 - 100, screen_h - 100, 200, 50)
                self._draw_stone_button(screen, self.back_custom_btn, "BACK TO LEVELS")

            else:
                no_maps = self.font.render("No custom maps found. Create one in MAP EDITOR!", True, PARCHMENT_DIM)
                screen.blit(no_maps, (screen_w // 2 - no_maps.get_width() // 2, 300))

        self._draw_stone_button(screen, self.back_btn, "BACK TO MENU")

        custom_label = "CUSTOM MAPS" if not self.show_custom else "STANDARD LEVELS"
        self._draw_stone_button(screen, self.custom_btn, custom_label)

    def _draw_stone_button(self, screen, rect, text):
        if rect is None:
            return

        hovered = rect.collidepoint(pygame.mouse.get_pos())

        shadow_rect = rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 3
        shadow_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 100))
        screen.blit(shadow_surf, shadow_rect.topleft)

        base_color = STONE_LIGHT if hovered else STONE_MID
        btn_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        btn_surf.fill((*base_color, 235))
        screen.blit(btn_surf, rect.topleft)

        if hovered:
            _draw_glow(screen, rect, TEAL_GLOW, pad=6, alpha=55, radius=10)

        border_color = GOLD_BRIGHT if hovered else GOLD
        pygame.draw.rect(screen, border_color, rect, 2, border_radius=6)

        text_color = GOLD_BRIGHT if hovered else PARCHMENT
        btn_text = self.font.render(text, True, text_color)
        screen.blit(btn_text, (rect.x + (rect.width - btn_text.get_width()) // 2,
                                rect.y + (rect.height - btn_text.get_height()) // 2))