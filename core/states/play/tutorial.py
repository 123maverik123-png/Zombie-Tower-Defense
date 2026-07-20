# core/states/play/tutorial.py
"""Подсказки обучающего уровня (level 1).

Показывает поочерёдные подсказки на оверлее, реагируя на события игры.
Никакой логики игры не меняет — только текст поверх экрана.
"""
import pygame

from core.event_bus import EventBus


class TutorialHints:
    """Последовательность подсказок для первого уровня."""

    def __init__(self, state):
        self.state = state
        self.active = getattr(state, 'is_tutorial', False)
        self.current = None          # активная подсказка (dict)
        self.queue = []
        self.shown = set()           # id уже показанных
        self.timer = 0.0

        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 22)

        if not self.active:
            return

        # Стартовая подсказка — сразу
        self._push(
            'welcome',
            "Зомби идут по дороге к замку!",
            "Выбери башню на панели внизу и построй её рядом с дорогой",
            duration=8.0,
        )

        EventBus.subscribe('tower_built', self._on_tower_built)
        EventBus.subscribe('enemy_killed', self._on_enemy_killed)
        EventBus.subscribe('enemy_reached_end', self._on_enemy_leaked)
        EventBus.subscribe('wave_complete', self._on_wave_complete)

    # ===== События =====

    def _on_tower_built(self, data):
        self._push(
            'first_tower',
            "Отличная башня!",
            "Кликни по ней, чтобы посмотреть радиус атаки и улучшить её",
            duration=6.0,
        )

    def _on_enemy_killed(self, data):
        if data.get('gold', 0) > 0:
            self._push(
                'first_kill',
                "Первый враг повержен! +золото",
                "За каждого убитого зомби платят. Копи на новые башни и апгрейды",
                duration=6.0,
            )

    def _on_enemy_leaked(self, data):
        self._push(
            'first_leak',
            "Зомби прорвался к замку!",
            "Каждый прорыв отнимает жизни. Перекрывай башнями всю дорогу",
            duration=6.0,
        )

    def _on_wave_complete(self, data):
        self._push(
            'wave_bonus',
            "Волна отбита! Бонус золота получен",
            "Между волнами есть пауза — успей достроить оборону. Апгрейд дешевле новой башни",
            duration=7.0,
        )

    # ===== Механика показа =====

    def _push(self, hint_id, title, text, duration=6.0):
        if not self.active or hint_id in self.shown:
            return
        self.shown.add(hint_id)
        self.queue.append({'id': hint_id, 'title': title, 'text': text, 'duration': duration})

    def update(self, dt):
        if not self.active:
            return
        if self.current:
            self.timer -= dt
            if self.timer <= 0:
                self.current = None
        if self.current is None and self.queue:
            self.current = self.queue.pop(0)
            self.timer = self.current['duration']

    def draw(self, screen):
        """Плашка с подсказкой вверху по центру экрана."""
        if not self.active or not self.current:
            return

        w = screen.get_width()
        title_surf = self.font.render(self.current['title'], True, (255, 220, 120))
        text_surf = self.small_font.render(self.current['text'], True, (230, 230, 230))

        pad = 14
        box_w = max(title_surf.get_width(), text_surf.get_width()) + pad * 2
        box_h = title_surf.get_height() + text_surf.get_height() + pad * 2 + 6
        box_x = (w - box_w) // 2
        box_y = 66

        # Плавное появление/исчезание по краям времени показа
        life = self.timer
        total = self.current['duration']
        fade = min(1.0, min(life, total - life) / 0.4) if total > 0.8 else 1.0
        alpha = int(230 * max(0.0, fade))

        box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        box.fill((15, 14, 12, min(200, alpha)))
        pygame.draw.rect(box, (255, 220, 120, alpha), box.get_rect(), 2, border_radius=6)
        box.blit(title_surf, (pad, pad))
        box.blit(text_surf, (pad, pad + title_surf.get_height() + 6))
        screen.blit(box, (box_x, box_y))
