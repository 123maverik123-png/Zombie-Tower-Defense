# core/states/play/ui/ui.py
import pygame
from core.font_loader import load_ui_font
from .icons import IconsManager
from .hud import HUD
from .tower_panel import TowerPanel


class PlayUI:
    """Основной UI для игрового состояния (HUD + панель башен)"""
    
    def __init__(self, state):
        self.state = state
        
        self.screen_w = 0
        self.screen_h = 0
        
        # Шрифты
        self.font = None
        self.small_font = None
        self.tiny_font = None
        
        # Менеджеры
        self.icons = IconsManager(state)
        self.hud = None
        self.tower_panel = None
        
        self._update_sizes()
    
    def _get_scale(self):
        screen_w = self.state.game.render_width
        screen_h = self.state.game.render_height
        scale_x = screen_w / 1920
        scale_y = screen_h / 1080
        scale = min(scale_x, scale_y)
        scale = min(scale, 1.5)
        scale = max(scale, 0.5)
        return scale
    
    def _update_sizes(self):
        scale = self._get_scale()
        
        # ✅ Увеличенные шрифты для панели (в 1.5 раза)
        panel_scale = scale * 1.5
        
        font_size = max(12, int(20 * panel_scale))
        small_size = max(10, int(16 * panel_scale))
        tiny_size = max(8, int(12 * panel_scale))
        
        self.font = load_ui_font(font_size)
        self.small_font = load_ui_font(small_size)
        self.tiny_font = load_ui_font(tiny_size)
        
        # Создаём компоненты
        self.hud = HUD(self.state, self.icons, self.font, self.small_font)
        self.tower_panel = TowerPanel(self.state, self.small_font, self.tiny_font)
        
        self.hud.update_sizes()
        self.tower_panel.update_sizes()
    
    def _convert_mouse_pos(self, pos):
        state = self.state
        if hasattr(state, 'game') and hasattr(state.game, '_convert_mouse_pos'):
            converted = state.game._convert_mouse_pos(pos)
            if converted is not None:
                return (int(converted[0]), int(converted[1]))
        return pos
    
    def handle_tower_panel_hover(self, pos):
        pos = self._convert_mouse_pos(pos)
        hovered = -1
        for i, btn in enumerate(self.tower_panel.get_buttons()):
            if btn['rect'].collidepoint(pos):
                hovered = i
                break
        self.tower_panel.set_hover(hovered)
        return hovered
    
    def handle_tower_panel_click(self, pos):
        pos = self._convert_mouse_pos(pos)
        state = self.state
        
        for btn in self.tower_panel.get_buttons():
            if btn['rect'].collidepoint(pos):
                tower_id = btn['tower_id']
                unlock_level = btn.get('unlock_level', 1)
                
                if state.level_number < unlock_level:
                    state.feedback_logic.show_error(pos[0], pos[1], f"Unlocked at level {unlock_level}!")
                    state.audio.play_sound("button_click", volume_override=0.3)
                    return True
                
                if tower_id in ['gate', 'wall']:
                    state.wall_placement_mode = True
                    state.selected_wall_type = tower_id
                    state.building_mode = False
                    state.audio.play_sound("button_click", volume_override=0.3)
                    print(f"🏗️ Wall mode: {tower_id}")
                    return True
                
                config = state._get_tower_config(tower_id)
                cost = config.get('cost', 100)
                if state.player.gold >= cost:
                    state.selected_tower = tower_id
                    state.wall_placement_mode = False
                    state.building_mode = True
                    state.audio.play_sound("button_click", volume_override=0.3)
                else:
                    state.feedback_logic.show_error(pos[0], pos[1], f"Not enough gold! Need ${cost}")
                    state.audio.play_sound("button_click", volume_override=0.3)
                return True
        return False
    
    def draw_hud(self, screen):
        """Отрисовывает HUD и панель башен"""
        screen_w = self.state.game.render_width
        screen_h = self.state.game.render_height
        
        if screen_w != self.screen_w or screen_h != self.screen_h:
            self.screen_w = screen_w
            self.screen_h = screen_h
            self._update_sizes()
        
        self.hud.draw(screen)
        self.tower_panel.draw(screen)
    
    # === СВОЙСТВА ДЛЯ СОВМЕСТИМОСТИ ===
    
    @property
    def tower_buttons(self):
        return self.tower_panel.get_buttons()
    
    @tower_buttons.setter
    def tower_buttons(self, value):
        pass  # Для обратной совместимости