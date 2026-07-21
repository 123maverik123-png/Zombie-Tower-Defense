# core/states/play/draw/ui.py
import pygame


class UIDraw:
    """Отрисовка UI элементов (HUD, консоль, панель башен)"""
    
    def __init__(self, state):
        self.state = state
    
    def draw(self, screen, ox, oy):
        """Отрисовывает все UI элементы"""
        state = self.state
        
        # 1. HUD
        if hasattr(state.ui_logic, 'draw_hud'):
            state.ui_logic.draw_hud(screen)
        elif hasattr(state.ui_logic, 'draw'):
            state.ui_logic.draw(screen)
        
        # 2. Информация о волнах
        self._draw_wave_info(screen)
        self._draw_level_info(screen)
        
        # 3. UI башни
        state.tower_ui.draw(screen, ox, oy)
        
        # 4. Консоль
        state.console.draw(screen)

        # 5. Редактор баланса (dev)
        if getattr(state, 'balance_editor', None):
            state.balance_editor.draw(screen)
    
    def _draw_wave_info(self, screen):
        """Рисует информацию о волнах"""
        state = self.state
        w, h = state.game.render_width, state.game.render_height
        
        if state.wave_manager.is_all_waves_complete() and len(state.enemies) == 0:
            # Экран победы рисуется отдельно
            return
        
        if (state.wave_manager.is_wave_complete() and
            not state.wave_manager.is_all_waves_complete() and
            not state.wave_manager.is_last_wave()):
            font = pygame.font.Font(None, 40)
            txt = font.render("Wave Complete!", True, (255, 255, 100))
            screen.blit(txt, (w//2 - txt.get_width()//2, h//2 - 100))
    
    def _draw_level_info(self, screen):
        """Рисует информацию об уровне"""
        state = self.state
        w, h = state.game.render_width, state.game.render_height
        
        if not state.level_complete and not state.game_over:
            font = pygame.font.Font(None, 20)
            wave_info = f"Wave {state.wave_manager.get_current_wave_number()}/{state.wave_manager.get_total_waves()}"
            if state.wave_manager.get_current_wave() and state.wave_manager.get_current_wave().get('is_boss_wave', False):
                wave_info += " 🏆 BOSS WAVE!"
            text = font.render(wave_info, True, (255, 200, 100))
            screen.blit(text, (w - 300, 70))