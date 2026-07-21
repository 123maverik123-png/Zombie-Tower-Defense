# core/states/play/ui/hud.py
import pygame
from core.theme import GOLD, GOLD_BRIGHT, GOLD_DIM, STONE_DARK, STONE_MID, STONE_LIGHT, PARCHMENT, SUCCESS, TEAL_GLOW, DANGER_BRIGHT


class HUD:
    """Верхняя панель с информацией о игроке"""
    
    def __init__(self, state, icons_manager, font, small_font):
        self.state = state
        self.icons = icons_manager
        self.font = font
        self.small_font = small_font
        
        self.top_panel_height = 0
    
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
        self.top_panel_height = int(50 * scale)
    
    def draw(self, screen):
        state = self.state
        screen_w = self.state.game.render_width
        screen_h = self.state.game.render_height
        
        scale = self._get_scale()
        top_panel_height = self.top_panel_height
        
        # Фон панели
        top_rect = pygame.Rect(0, 0, screen_w, top_panel_height)
        top_surf = pygame.Surface((screen_w, top_panel_height), pygame.SRCALPHA)
        top_surf.fill((*STONE_DARK, 225))
        screen.blit(top_surf, (0, 0))
        pygame.draw.line(screen, GOLD, (0, top_panel_height), (screen_w, top_panel_height), 2)

        # Иконки и информация
        icon_size = int(24 * scale)
        icon_size = max(16, min(40, icon_size))
        y_offset = int((top_panel_height - icon_size) / 2)

        items = [
            ('gold', f"{state.player.gold}", GOLD_BRIGHT),
            ('heart', f"{state.player.lives}", DANGER_BRIGHT),
            ('level', f"Lv.{state.level_number}", GOLD),
            ('wave', f"{state.wave_manager.get_current_wave_number()}/{state.wave_manager.get_total_waves()}", TEAL_GLOW),
            ('enemy', f"{len(state.enemies)}", PARCHMENT),
        ]

        x_offset = int(15 * scale)
        spacing = int(6 * scale)
        text_spacing = int(25 * scale)

        for icon_name, text, color in items:
            icon = self.icons.get(icon_name, 24)
            if icon:
                screen.blit(icon, (x_offset, y_offset))
            x_offset += icon_size + spacing

            text_surf = self.font.render(text, True, color)
            screen.blit(text_surf, (x_offset, int(y_offset + (icon_size - text_surf.get_height()) / 2)))
            x_offset += text_surf.get_width() + text_spacing

        # Режим
        mode_text = "BUILD" if state.building_mode else "PLAY"
        mode_color = SUCCESS if state.building_mode else PARCHMENT
        if state.wall_placement_mode:
            if state.selected_wall_type == 'wall':
                variant = getattr(state, 'selected_wall_variant', 'h').upper()
                mode_text = f"WALL: {variant} [wheel]"
            else:
                ov = getattr(state, 'gate_orientation_override', None)
                gate_mode = ov.upper() if ov else 'AUTO'
                mode_text = f"GATE: {gate_mode} [wheel]"
            mode_color = GOLD_BRIGHT
        
        mode_surf = self.font.render(f"[{mode_text}]", True, mode_color)
        screen.blit(mode_surf, (screen_w - mode_surf.get_width() - int(15 * scale),
                                 int((top_panel_height - mode_surf.get_height()) / 2)))
    
    def get_height(self):
        return self.top_panel_height