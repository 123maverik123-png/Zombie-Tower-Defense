# core/states/play/draw/effects.py
import pygame

from core.opengl.batch import BLEND_ADDITIVE


class EffectsDraw:
    """Эффекты: попадания и молнии — GPU-батч; текстовый фидбек — pygame-оверлей"""

    def __init__(self, state):
        self.state = state

    def draw_scene(self, renderer, ox, oy):
        """GPU-часть: эффекты попадания и молнии"""
        state = self.state

        # 1. Эффекты попадания (только видимые)
        for effect in state.hit_effects:
            if -100 < effect.x + ox < state.game.render_width + 100 and -100 < effect.y + oy < state.game.render_height + 100:
                effect.draw_batch(renderer, ox, oy)

        # 2. Круги фидбека строительства
        self._draw_feedback_circles(renderer, ox, oy)

        # 3. Молнии
        self._draw_lightning_effects(renderer, ox, oy)

    def _draw_feedback_circles(self, renderer, ox, oy):
        """Круговые индикаторы ошибки/успеха строительства (GPU)"""
        state = self.state
        batch = renderer.batch
        soft = renderer.get_region('__soft__')

        if state.build_error:
            x, y = state.build_error_pos
            batch.draw(soft, x + ox, y + oy, 44, 44,
                       color=(255, 0, 0, 180), blend=BLEND_ADDITIVE)

        if state.build_success:
            x, y = state.build_success_pos
            progress = 1 - (state.build_success_timer / 0.3)
            radius = max(5, int(40 * progress + 10))
            alpha = int(255 * (1 - progress))
            if radius > 0 and alpha > 0:
                batch.draw(soft, x + ox, y + oy, radius * 2, radius * 2,
                           color=(0, 255, 0, alpha), blend=BLEND_ADDITIVE)

    def draw_feedback(self, screen, ox, oy):
        """Pygame-часть фидбека: текст ошибки (шрифты остаются на оверлее)"""
        state = self.state

        if state.build_error:
            x, y = state.build_error_pos
            txt = state.small_font.render(state.build_error_msg, True, (255, 50, 50))
            screen.blit(txt, (x + ox - txt.get_width()//2, y + oy - 40))

    def _draw_lightning_effects(self, renderer, offset_x=0, offset_y=0):
        """Рисует молнии: линии-квады + аддитивные свечения"""
        state = self.state
        batch = renderer.batch
        soft = renderer.get_region('__soft__')

        for effect in state.lightning_effects:
            from_pos = effect['from']
            to_pos = effect['to']
            timer = effect['timer']
            is_chain = effect.get('is_chain', False)
            max_timer = 0.25 if not is_chain else 0.2
            alpha = int(255 * (timer / max_timer))
            x1 = from_pos[0] + offset_x
            y1 = from_pos[1] + offset_y
            x2 = to_pos[0] + offset_x
            y2 = to_pos[1] + offset_y

            # Ядро и широкий ореол
            batch.draw_line(x1, y1, x2, y2, 3, (255, 255, 255, alpha), blend=BLEND_ADDITIVE)
            batch.draw_line(x1, y1, x2, y2, 8, (100, 200, 255, alpha // 2), blend=BLEND_ADDITIVE)

            # Свечения на концах
            batch.draw(soft, x1, y1, 12, 12, color=(255, 255, 255, alpha), blend=BLEND_ADDITIVE)
            batch.draw(soft, x2, y2, 12, 12, color=(255, 255, 255, alpha), blend=BLEND_ADDITIVE)

            if is_chain:
                mx = (x1 + x2) * 0.5
                my = (y1 + y2) * 0.5
                batch.draw(soft, mx, my, 20, 20,
                           color=(255, 255, 200, alpha // 2), blend=BLEND_ADDITIVE)
