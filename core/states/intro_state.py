# core/states/intro_state.py
"""Интро-сцена между выбором сложности / кликом «Играть» и боем.

Сглаживает резкий переход в игру. Два режима:

  * 'long' — длинное сюжетное интро (3 слайда лора). Показывается один
    раз на профиль (profile.intro_seen), когда игрок впервые входит в бой.
  * 'card' — короткая карточка «УРОВЕНЬ N» перед остальными заходами.

Рисуется чистым pygame поверх очищенного GL-экрана (как меню), своего
draw_scene нет. По окончании или скипу само делает change_state('PLAYING').

Вся тайминг-логика (какой слайд активен, альфа текста/фейда, готовность
перейти в бой) вынесена в IntroTimeline — её можно тестировать без OpenGL.
"""
import os
import math
import pygame

from core.state_manager import State
from core.audio import AudioManager
from core.font_loader import load_ui_font, load_title_font
from core.theme import (
    GOLD, GOLD_BRIGHT, PARCHMENT, PARCHMENT_DIM,
    TEAL_GLOW, DANGER_BRIGHT,
)


# --- Лор (правится здесь) -----------------------------------------------
# Длинное интро: список слайдов, каждый — строки текста.
LORE_SLIDES = [
    [
        "Мир держался на свете Кристалла-Сердца.",
        "Пока в глубине не проснулся разлом...",
    ],
    [
        "Древняя печать треснула.",
        "Из мёртвых земель потянуло холодом и тлением.",
    ],
    [
        "Портал разорвал ткань земель.",
        "Из тьмы хлынули те, кто не знает смерти.",
    ],
    [
        "Орда идёт лишь к одному —",
        "поглотить свет Кристалла и погасить его навсегда.",
    ],
    [
        "Стены пали. Армии рассеяны.",
        "Остался лишь ты и путь, что ведёт к Сердцу.",
    ],
    [
        "Ты — последний хранитель.",
        "Возведи оборону. Кристалл не должен погаснуть.",
    ],
]

# Подзаголовок карточки уровня (по номеру; иначе — общий).
LEVEL_SUBTITLES = {
    1: "Первая волна на подходе",
}
DEFAULT_LEVEL_SUBTITLE = "Орда наступает. Держи оборону."


class IntroTimeline:
    """Чистая тайминг-логика интро (без pygame-рендера).

    slide_times — длительность показа каждого слайда (сек). Внутри слайда:
    fade-in -> hold -> fade-out. Между стартом сцены и первым слайдом, а
    также после последнего слайда — общий чёрный фейд (intro_fade).
    """

    FADE_IN = 1.6    # проявление текста слайда
    FADE_OUT = 1.4   # затухание текста слайда
    BLACK_FADE = 1.2  # общий чёрный фейд в начале и в конце

    def __init__(self, slide_count, hold=5.2):
        self.slide_count = max(0, slide_count)
        # Длительность каждого слайда целиком (fade-in + hold + fade-out).
        self.slide_dur = self.FADE_IN + hold + self.FADE_OUT
        self.elapsed = 0.0
        self.skipped_to = 0     # индекс слайда, на который перескочили кликом
        self.finished = False   # пора запускать PLAYING
        self.finish_fade = 0.0  # прогресс финального чёрного фейда 0..1

    @property
    def total(self):
        return self.BLACK_FADE + self.slide_count * self.slide_dur

    def current_slide(self):
        """Индекс активного слайда или None (во время стартового фейда)."""
        if self.slide_count == 0:
            return None
        t = self.elapsed - self.BLACK_FADE
        if t < 0:
            return None
        idx = int(t // self.slide_dur)
        return min(idx, self.slide_count - 1)

    def slide_text_alpha(self):
        """Альфа текста активного слайда 0..1 (fade-in/hold/fade-out)."""
        if self.current_slide() is None:
            return 0.0
        t = self.elapsed - self.BLACK_FADE
        local = t - self.current_slide() * self.slide_dur
        if local < self.FADE_IN:
            return max(0.0, min(1.0, local / self.FADE_IN))
        if local < self.FADE_IN + (self.slide_dur - self.FADE_IN - self.FADE_OUT):
            return 1.0
        # fade-out
        out = local - (self.slide_dur - self.FADE_OUT)
        return max(0.0, 1.0 - out / self.FADE_OUT)

    def start_fade_alpha(self):
        """Альфа стартового чёрного оверлея 1..0 в первые BLACK_FADE сек."""
        if self.elapsed >= self.BLACK_FADE:
            return 0.0
        return 1.0 - self.elapsed / self.BLACK_FADE

    def begin_finish(self):
        """Запустить финальный чёрный фейд перед боем (идемпотентно)."""
        if not self._finishing():
            self._finish_start = self.elapsed

    def _finishing(self):
        return getattr(self, '_finish_start', None) is not None

    def update(self, dt):
        """Продвинуть время. Возвращает True, когда финальный фейд завершён."""
        self.elapsed += dt

        if self._finishing():
            self.finish_fade = min(1.0, (self.elapsed - self._finish_start) / self.BLACK_FADE)
            if self.finish_fade >= 1.0:
                self.finished = True
            return self.finished

        # Естественное завершение всех слайдов -> запустить финальный фейд.
        if self.elapsed >= self.total:
            self.begin_finish()
        return False

    def next_slide(self):
        """ЛКМ: перескочить к следующему слайду; если он последний — финиш."""
        if self._finishing():
            return
        cur = self.current_slide()
        if cur is None:
            # перескочить стартовый фейд
            self.elapsed = self.BLACK_FADE
            return
        if cur >= self.slide_count - 1:
            self.begin_finish()
        else:
            # к hold-фазе следующего слайда (сразу полностью видимый текст);
            # +0.05 уводит от границы fade-in, чтобы альфа гарантированно 1.0
            self.elapsed = self.BLACK_FADE + (cur + 1) * self.slide_dur + self.FADE_IN + 0.05

    def skip_all(self):
        """Пробел/ESC/ПКМ: пропустить всё интро — сразу финальный фейд."""
        self.begin_finish()


class IntroState(State):
    def __init__(self, game, level, level_data, mode='card', on_done=None):
        """mode: 'long' (сюжет) | 'card' (карточка уровня).

        on_done() вызывается, когда интро отыграло/пропущено — в нём
        перехватчик запускает PLAYING. Если None — переходим сами.
        """
        super().__init__(game)
        self.game = game
        self.level = level
        self.level_data = level_data
        self.mode = mode
        self.on_done = on_done
        self.audio = AudioManager()

        self.title_font = load_title_font(56)
        self.sub_font = load_ui_font(26)
        self.hint_font = load_ui_font(18)

        slide_count = len(LORE_SLIDES) if mode == 'long' else 1
        hold = 5.2 if mode == 'long' else 3.2
        self.timeline = IntroTimeline(slide_count, hold=hold)

        self._done_fired = False
        self._load_scene_assets()

    # --- загрузка ассетов сцены (портал/кристалл/зомби/фон) --------------
    def _load_scene_assets(self):
        self.bg = self._try_load("assets/images/menu_bg.jpg", convert=True)
        portal_path, castle_path = self._tile_paths()
        self.portal_img = self._try_load(portal_path)
        self.castle_img = self._try_load(castle_path)
        self.zombie_imgs = []
        for i in range(4):
            img = self._try_load(f"assets/sprites/pzombie_normal/right_{i}.png")
            if img:
                self.zombie_imgs.append(img)

    def _tile_paths(self):
        """Пути к тем же тайлам портала/кристалла, что показываются в бою.

        При теме 'kenney' тайлы лежат в подпапке биома (выбор по уровню);
        корневые tile_*.png — старые classic-ассеты, фолбэк.
        """
        portal = "assets/images/tiles/tile_portal.png"
        castle = "assets/images/tiles/tile_castle.png"
        try:
            from core.graphics_theme import THEME, biome_for_level
            if THEME == 'kenney':
                biome = biome_for_level(self.level)
                bp = f"assets/images/tiles/{biome}/tile_portal.png"
                bc = f"assets/images/tiles/{biome}/tile_castle.png"
                if os.path.exists(bp):
                    portal = bp
                if os.path.exists(bc):
                    castle = bc
        except Exception:
            pass
        return portal, castle

    def _try_load(self, path, convert=False):
        if not os.path.exists(path):
            return None
        try:
            img = pygame.image.load(path)
            return img.convert() if convert else img.convert_alpha()
        except Exception:
            return None

    # --- ввод ------------------------------------------------------------
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN):
                    self.timeline.skip_all()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:            # ЛКМ — следующий слайд
                    self.timeline.next_slide()
                elif event.button == 3:          # ПКМ — пропустить всё
                    self.timeline.skip_all()

    def update(self, dt):
        if self.timeline.update(dt) and not self._done_fired:
            self._done_fired = True
            self._go_to_game()

    def _go_to_game(self):
        if self.on_done:
            self.on_done()
            return
        # Фолбэк: сами создаём PlayState (если перехватчик не задал колбэк).
        from .play.state import PlayState
        sm = self.game.state_manager
        if 'PLAYING' in sm._states:
            del sm._states['PLAYING']
        sm.add_state('PLAYING', PlayState(self.game, self.level, self.level_data))
        sm.change_state('PLAYING')

    # --- рендер ----------------------------------------------------------
    def draw(self, screen):
        sw, sh = self.game.render_width, self.game.render_height
        if self.mode == 'long':
            self._draw_scene(screen, sw, sh)
            self._draw_lore_text(screen, sw, sh)
        else:
            self._draw_scene(screen, sw, sh, dim=230)
            self._draw_level_card(screen, sw, sh)

        self._draw_hint(screen, sw, sh)
        self._draw_fades(screen, sw, sh)

    def _draw_scene(self, screen, sw, sh, dim=170):
        screen.fill((10, 9, 12))
        if self.bg:
            screen.blit(pygame.transform.scale(self.bg, (sw, sh)), (0, 0))
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((6, 4, 10, dim))
        screen.blit(overlay, (0, 0))

        t = self.timeline.elapsed
        cy = int(sh * 0.52)

        # Портал слева — пульсирующий, с красно-фиолетовым свечением.
        if self.portal_img:
            pulse = 1.0 + 0.08 * math.sin(t * 2.2)
            psize = int(sh * 0.34 * pulse)
            portal = pygame.transform.smoothscale(self.portal_img, (psize, psize))
            px = int(sw * 0.16) - psize // 2
            py = cy - psize // 2
            self._blit_glow(screen, (px + psize // 2, cy), int(psize * 0.72),
                            (150, 40, 160), alpha=70 + int(30 * math.sin(t * 2.2)))
            screen.blit(portal, (px, py))

        # Кристалл справа — лазурное мягкое свечение.
        if self.castle_img:
            csize = int(sh * 0.30)
            castle = pygame.transform.smoothscale(self.castle_img, (csize, csize))
            crx = int(sw * 0.84) - csize // 2
            cry = cy - csize // 2
            glow = 60 + int(25 * math.sin(t * 1.5))
            self._blit_glow(screen, (crx + csize // 2, cy), int(csize * 0.7),
                            TEAL_GLOW, alpha=glow)
            screen.blit(castle, (crx, cry))

        # Зомби бредут из портала к кристаллу (только в сюжетном режиме,
        # заметны со 2-го слайда — «из тьмы хлынули»).
        if self.mode == 'long' and self.zombie_imgs:
            self._draw_marching_zombies(screen, sw, sh, cy, t)

    def _draw_marching_zombies(self, screen, sw, sh, cy, t):
        start_x = sw * 0.20
        end_x = sw * 0.78
        span = end_x - start_x
        cur = self.timeline.current_slide()
        # Плотность и видимость нарастают ко 2-3 слайду.
        visible = 0.0 if (cur is None or cur == 0) else 1.0
        if visible <= 0:
            return
        zsize = int(sh * 0.11)
        count = 6
        for i in range(count):
            # Каждый зомби на своей фазе марша, зациклен.
            phase = (t * 0.06 + i / count) % 1.0
            zx = start_x + phase * span
            row = (i % 3) - 1
            zy = cy + row * int(sh * 0.06) + int(4 * math.sin(t * 3 + i))
            frame = self.zombie_imgs[int((t * 6 + i) % len(self.zombie_imgs))]
            z = pygame.transform.smoothscale(frame, (zsize, zsize))
            # Силуэт: затемняем и делаем полупрозрачным у краёв пути.
            edge = min(phase, 1.0 - phase) * 2.0      # 0 у краёв, 1 в центре
            alpha = int(60 + 150 * min(1.0, edge * 1.4) * visible)
            dark = z.copy()
            dark.fill((25, 20, 30, 255), special_flags=pygame.BLEND_RGBA_MULT)
            dark.set_alpha(alpha)
            screen.blit(dark, (int(zx - zsize // 2), int(zy - zsize // 2)))

    def _blit_glow(self, screen, center, radius, color, alpha=80):
        d = radius * 2
        glow = pygame.Surface((d, d), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, max(0, min(255, alpha))), (radius, radius), radius)
        screen.blit(glow, (center[0] - radius, center[1] - radius),
                    special_flags=pygame.BLEND_PREMULTIPLIED if False else 0)

    def _draw_lore_text(self, screen, sw, sh):
        alpha = self.timeline.slide_text_alpha()
        idx = self.timeline.current_slide()
        if idx is None or alpha <= 0.0:
            return
        lines = LORE_SLIDES[idx]
        a = int(255 * alpha)
        y = int(sh * 0.74)
        for line in lines:
            surf = self.sub_font.render(line, True, PARCHMENT)
            surf.set_alpha(a)
            shadow = self.sub_font.render(line, True, (0, 0, 0))
            shadow.set_alpha(a)
            x = (sw - surf.get_width()) // 2
            screen.blit(shadow, (x + 2, y + 2))
            screen.blit(surf, (x, y))
            y += surf.get_height() + 10

        # Точки-прогресс слайдов.
        self._draw_slide_dots(screen, sw, sh, idx)

    def _draw_slide_dots(self, screen, sw, sh, active):
        n = self.timeline.slide_count
        if n <= 1:
            return
        r = 5
        gap = 22
        total_w = (n - 1) * gap
        x0 = sw // 2 - total_w // 2
        y = int(sh * 0.88)
        for i in range(n):
            col = GOLD_BRIGHT if i == active else (90, 80, 60)
            pygame.draw.circle(screen, col, (x0 + i * gap, y), r)

    def _draw_level_card(self, screen, sw, sh):
        alpha = self.timeline.slide_text_alpha()
        if alpha <= 0.0:
            return
        a = int(255 * alpha)
        title = f"УРОВЕНЬ {self.level}"
        sub = LEVEL_SUBTITLES.get(self.level, DEFAULT_LEVEL_SUBTITLE)

        t_surf = self.title_font.render(title, True, GOLD)
        t_shadow = self.title_font.render(title, True, (0, 0, 0))
        t_surf.set_alpha(a); t_shadow.set_alpha(a)
        tx = (sw - t_surf.get_width()) // 2
        ty = int(sh * 0.40)
        screen.blit(t_shadow, (tx + 3, ty + 3))
        screen.blit(t_surf, (tx, ty))

        # Декоративная линия под заголовком.
        line_w = t_surf.get_width() + 40
        lx = sw // 2 - line_w // 2
        ly = ty + t_surf.get_height() + 12
        line = pygame.Surface((line_w, 3), pygame.SRCALPHA)
        line.fill((*GOLD, a))
        screen.blit(line, (lx, ly))

        s_surf = self.sub_font.render(sub, True, PARCHMENT_DIM)
        s_surf.set_alpha(a)
        screen.blit(s_surf, ((sw - s_surf.get_width()) // 2, ly + 18))

    def _draw_hint(self, screen, sw, sh):
        if self.timeline._finishing():
            return
        if self.mode == 'long':
            txt = "ЛКМ — далее   •   Пробел / ПКМ — пропустить"
        else:
            txt = "ЛКМ / Пробел — в бой"
        surf = self.hint_font.render(txt, True, (140, 130, 110))
        # мягкое мерцание подсказки
        surf.set_alpha(120 + int(60 * math.sin(self.timeline.elapsed * 2.0)))
        screen.blit(surf, ((sw - surf.get_width()) // 2, int(sh * 0.94)))

    def _draw_fades(self, screen, sw, sh):
        # Стартовый чёрный фейд.
        sa = self.timeline.start_fade_alpha()
        if sa > 0:
            ov = pygame.Surface((sw, sh), pygame.SRCALPHA)
            ov.fill((0, 0, 0, int(255 * sa)))
            screen.blit(ov, (0, 0))
        # Финальный чёрный фейд перед боем.
        if self.timeline.finish_fade > 0:
            ov = pygame.Surface((sw, sh), pygame.SRCALPHA)
            ov.fill((0, 0, 0, int(255 * self.timeline.finish_fade)))
            screen.blit(ov, (0, 0))

    def on_resolution_changed(self, screen_w, screen_h):
        pass


def launch_game_with_intro(game, profile, audio):
    """Единая точка входа в бой через интро-сцену.

    Вызывается из меню (сложность уже выбрана) и из окна выбора сложности.
    Режим интро: 'long' один раз на профиль (profile.intro_seen == False),
    иначе короткая карточка уровня 'card'. По окончании интро колбэк
    создаёт PlayState и переключает на PLAYING.

    game        — Game
    profile     — текущий Profile (уже с выбранной difficulty)
    audio       — AudioManager (для запуска музыки)
    """
    from core.event_bus import EventBus
    from core.level_loader import build_level

    EventBus.clear()
    level = profile.current_level
    level_data = build_level(level)

    # Музыку запускаем уже на интро — мягче входит в бой.
    if audio.settings.music_enabled:
        audio.play_music("game_theme.wav")

    long_intro = not getattr(profile, 'intro_seen', True)
    if long_intro:
        # Помечаем как просмотренное сразу — второй раз длинное не покажем.
        profile.intro_seen = True
        try:
            from services.profile_manager import ProfileManager
            ProfileManager().save_profile(profile)
        except Exception:
            pass
    mode = 'long' if long_intro else 'card'

    sm = game.state_manager

    def _on_done():
        from .play.state import PlayState
        if 'PLAYING' in sm._states:
            del sm._states['PLAYING']
        sm.add_state('PLAYING', PlayState(game, level, level_data))
        sm.change_state('PLAYING')

    intro = IntroState(game, level, level_data, mode=mode, on_done=_on_done)
    sm.add_state('INTRO', intro)
    sm.change_state('INTRO')
