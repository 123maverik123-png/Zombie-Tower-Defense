# ui/tower_ui.py
import pygame
from core.font_loader import load_ui_font
from core.theme import GOLD, GOLD_BRIGHT, STONE_DARK, STONE_MID, PARCHMENT, TEAL_GLOW, DANGER, DANGER_BRIGHT


class TowerUI:
    """Интерфейс для взаимодействия с башнями (улучшение/продажа)"""

    def __init__(self):
        self.font = load_ui_font(18)
        self.small_font = load_ui_font(14)
        self.active = False
        self.tower = None
        self.position = (0, 0)

        self.upgrade_btn = None
        self.sell_btn = None
        self.hovered_btn = None
        self.show_tooltip = False
        self.tooltip_text = ""
        self.tooltip_pos = (0, 0)

        self._upgrade_rect = None
        self._repair_rect = None
        self._sell_rect = None

    def _is_fort(self):
        """Стена/ворота — у них есть ремонт (в отличие от башен)."""
        return self.tower is not None and hasattr(self.tower.upgrades, 'repair')

    def show(self, tower, pos):
        self.active = True
        self.tower = tower
        self.position = pos
        self.hovered_btn = None
        self._upgrade_rect = None
        self._sell_rect = None

        btn_size = 40
        spacing = 10
        total_width = btn_size * 2 + spacing

        self.upgrade_btn = pygame.Rect(
            pos[0] - total_width // 2,
            pos[1] - btn_size - 5,
            btn_size,
            btn_size
        )

        self.sell_btn = pygame.Rect(
            self.upgrade_btn.x + btn_size + spacing,
            pos[1] - btn_size - 5,
            btn_size,
            btn_size
        )

    def hide(self):
        self.active = False
        self.tower = None
        self.upgrade_btn = None
        self.sell_btn = None
        self._upgrade_rect = None
        self._repair_rect = None
        self._sell_rect = None
        self.hovered_btn = None
        self.show_tooltip = False

    def handle_click(self, pos) -> str:
        if not self.active or not self.tower:
            return None

        if self._upgrade_rect and self._upgrade_rect.collidepoint(pos):
            return 'upgrade'

        if self._repair_rect and self._repair_rect.collidepoint(pos):
            return 'repair'

        if self._sell_rect and self._sell_rect.collidepoint(pos):
            return 'sell'

        return None

    def handle_hover(self, pos):
        self.hovered_btn = None
        self.show_tooltip = False

        if not self.active or not self.tower:
            return

        if self._upgrade_rect and self._upgrade_rect.collidepoint(pos):
            self.hovered_btn = 'upgrade'
            self.show_tooltip = True
            self.tooltip_text = f"Upgrade: ${self.tower.upgrades.upgrade_cost}"
            self.tooltip_pos = (pos[0] + 10, pos[1] - 20)
            return

        if self._repair_rect and self._repair_rect.collidepoint(pos):
            self.hovered_btn = 'repair'
            self.show_tooltip = True
            self.tooltip_text = f"Repair: ${self.tower.upgrades.repair_cost()}"
            self.tooltip_pos = (pos[0] + 10, pos[1] - 20)
            return

        if self._sell_rect and self._sell_rect.collidepoint(pos):
            self.hovered_btn = 'sell'
            self.show_tooltip = True
            sell_price = int(self.tower.upgrades.cost * 0.5)
            for level in range(2, self.tower.upgrades.level + 1):
                sell_price += int(self.tower.upgrades.cost * 0.5 * (1.5 ** (level - 2)))
            self.tooltip_text = f"Sell: ${sell_price}"
            self.tooltip_pos = (pos[0] + 10, pos[1] - 20)
            return

    def _draw_glow(self, screen, center, radius, color, alpha=90):
        glow = pygame.Surface((radius * 2 + 12, radius * 2 + 12), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, alpha), (radius + 6, radius + 6), radius + 6)
        screen.blit(glow, (center[0] - radius - 6, center[1] - radius - 6))

    def draw(self, screen, offset_x=0, offset_y=0):
        if not self.active or not self.tower:
            return

        btn_offset_x = self.position[0] + offset_x
        btn_offset_y = self.position[1] + offset_y

        btn_size = 40
        spacing = 10
        is_fort = self._is_fort()
        n_btns = 3 if is_fort else 2
        total_width = btn_size * n_btns + spacing * (n_btns - 1)

        upgrade_x = btn_offset_x - total_width // 2
        row_y = btn_offset_y - btn_size - 5

        self._upgrade_rect = pygame.Rect(upgrade_x, row_y, btn_size, btn_size)
        if is_fort:
            repair_x = upgrade_x + btn_size + spacing
            self._repair_rect = pygame.Rect(repair_x, row_y, btn_size, btn_size)
            sell_x = repair_x + btn_size + spacing
        else:
            self._repair_rect = None
            sell_x = upgrade_x + btn_size + spacing
        self._sell_rect = pygame.Rect(sell_x, row_y, btn_size, btn_size)

        # === КНОПКА УЛУЧШЕНИЯ ===
        upgrade_hovered = self.hovered_btn == 'upgrade'
        if upgrade_hovered:
            self._draw_glow(screen, self._upgrade_rect.center, 22, TEAL_GLOW, alpha=80)
        pygame.draw.circle(screen, STONE_MID, self._upgrade_rect.center, 22)
        pygame.draw.circle(screen, GOLD_BRIGHT if upgrade_hovered else GOLD, self._upgrade_rect.center, 22, 2)

        points = [
            (self._upgrade_rect.centerx, self._upgrade_rect.centery - 12),
            (self._upgrade_rect.centerx - 10, self._upgrade_rect.centery + 4),
            (self._upgrade_rect.centerx + 10, self._upgrade_rect.centery + 4)
        ]
        pygame.draw.polygon(screen, GOLD_BRIGHT if upgrade_hovered else PARCHMENT, points)

        level_text = self.small_font.render(str(self.tower.upgrades.level), True, PARCHMENT)
        screen.blit(level_text, (self._upgrade_rect.centerx - level_text.get_width() // 2,
                                  self._upgrade_rect.centery + 14))

        # === КНОПКА РЕМОНТА (стены/ворота) ===
        if self._repair_rect is not None:
            repair_hovered = self.hovered_btn == 'repair'
            if repair_hovered:
                self._draw_glow(screen, self._repair_rect.center, 22, TEAL_GLOW, alpha=80)
            pygame.draw.circle(screen, STONE_MID, self._repair_rect.center, 22)
            pygame.draw.circle(screen, GOLD_BRIGHT if repair_hovered else GOLD, self._repair_rect.center, 22, 2)
            # иконка «гаечный крест» — плюс (ремонт/восстановление)
            cx, cy = self._repair_rect.center
            col = GOLD_BRIGHT if repair_hovered else PARCHMENT
            pygame.draw.rect(screen, col, (cx - 3, cy - 11, 6, 22))
            pygame.draw.rect(screen, col, (cx - 11, cy - 3, 22, 6))

        # === КНОПКА ПРОДАЖИ ===
        sell_hovered = self.hovered_btn == 'sell'
        if sell_hovered:
            self._draw_glow(screen, self._sell_rect.center, 22, DANGER_BRIGHT, alpha=70)
        pygame.draw.circle(screen, STONE_MID, self._sell_rect.center, 22)
        pygame.draw.circle(screen, DANGER_BRIGHT if sell_hovered else DANGER, self._sell_rect.center, 22, 2)

        dollar_text = self.font.render("$", True, GOLD_BRIGHT)
        screen.blit(dollar_text, (self._sell_rect.centerx - dollar_text.get_width() // 2,
                                   self._sell_rect.centery - dollar_text.get_height() // 2))

        # === ТУЛТИП ===
        if self.show_tooltip and self.tooltip_text:
            tooltip_surf = self.small_font.render(self.tooltip_text, True, PARCHMENT)
            tooltip_rect = tooltip_surf.get_rect()
            tooltip_rect.x = self.tooltip_pos[0] + 15
            tooltip_rect.y = self.tooltip_pos[1] - 10

            bg_rect = tooltip_rect.inflate(14, 10)
            bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            bg_surf.fill((*STONE_DARK, 230))
            screen.blit(bg_surf, bg_rect.topleft)
            pygame.draw.rect(screen, GOLD, bg_rect, 2, border_radius=5)

            screen.blit(tooltip_surf, tooltip_rect)