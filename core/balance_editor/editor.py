# core/balance_editor/editor.py
"""Панель редактора баланса (dev-инструмент).

Оверлей поверх игры, рисуется через pygame на UI-поверхность (как консоль).
Открывается командой `balance` в dev-консоли.

Управление (мышь):
  Клик по вкладке          — сменить категорию (Башни / Враги / Волны)
  Клик по имени объекта     — выбрать башню/врага (стрелки < > листают)
  Перетаскивание ползунка   — менять значение (со снапом к шагу поля)
  Кнопки  -  /  +           — шаг значения вниз/вверх
Клавиатура (запасное):
  Tab — категория, ↑/↓ — объект, R — перечитать с диска, Esc — закрыть
"""
import pygame

from .model import BalanceModel, TOWER_FIELDS, ENEMY_FIELDS, FIELD_SPEC, snap

CATEGORIES = ["Towers", "Enemies", "Waves"]

# Геометрия панели
PANEL_X = 20
PANEL_Y = 20
PANEL_W = 620
ROW_H = 30
SLIDER_X = 210      # смещение начала дорожки ползунка от левого края панели
SLIDER_W = 250
BTN_W = 26          # ширина кнопок -/+


class BalanceEditor:
    def __init__(self, game):
        self.game = game
        self.active = False
        self.model = BalanceModel()

        self.cat_index = 0
        self.obj_index = 0
        self.status = ""

        self.dragging_field = None  # имя поля, чей ползунок сейчас тянут

        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)

        # Прямоугольники интерактивных зон, пересчитываются в draw()
        self._tab_rects = []       # [(rect, cat_index)]
        self._slider_rects = {}    # field -> track rect
        self._minus_rects = {}     # field -> rect
        self._plus_rects = {}      # field -> rect
        self._obj_prev_rect = None
        self._obj_next_rect = None

    # --- Открытие/закрытие ---

    def toggle(self):
        self.active = not self.active
        if self.active:
            self.model.reload()
            self.dragging_field = None
            self.status = "drag=set   -/+ =step   click tabs/arrows"

    # --- Контекст ---

    def _category(self):
        return CATEGORIES[self.cat_index]

    def _object_ids(self):
        cat = self._category()
        if cat == "Towers":
            return self.model.tower_ids()
        if cat == "Enemies":
            return self.model.enemy_ids()
        return []

    def _fields(self):
        cat = self._category()
        if cat == "Towers":
            return TOWER_FIELDS
        if cat == "Enemies":
            return ENEMY_FIELDS
        return []

    def _current_object(self):
        ids = self._object_ids()
        if not ids:
            return None
        self.obj_index = max(0, min(self.obj_index, len(ids) - 1))
        return ids[self.obj_index]

    def _get_value(self, obj_id, field):
        cat = self._category()
        if cat == "Towers":
            return self.model.get_tower_value(obj_id, field)
        if cat == "Enemies":
            return self.model.get_enemy_value(obj_id, field)
        return None

    def _set_value(self, obj_id, field, value):
        value = snap(value, field)
        cat = self._category()
        if cat == "Towers":
            self.model.set_tower_value(obj_id, field, value)
        elif cat == "Enemies":
            self.model.set_enemy_value(obj_id, field, value)
        if self.model.error:
            self.status = "ERR: " + self.model.error
            self.model.error = ""
        else:
            self.status = f"{obj_id}.{field} = {value} (saved)"

    # --- Ввод ---

    def handle_event(self, event):
        """Возвращает True, если событие поглощено панелью."""
        if not self.active:
            return False

        if event.type == pygame.KEYDOWN:
            return self._handle_key(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_mouse_down(event.pos)
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_field = None
            return True
        if event.type == pygame.MOUSEMOTION and self.dragging_field:
            self._drag_to(event.pos[0])
            return True
        # Прочие события мыши гасим, чтобы не рулить игрой под панелью
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                          pygame.MOUSEMOTION, pygame.MOUSEWHEEL):
            return True
        return False

    def _handle_key(self, event):
        key = event.key
        if key == pygame.K_ESCAPE:
            self.active = False
        elif key == pygame.K_TAB:
            self.cat_index = (self.cat_index + 1) % len(CATEGORIES)
            self.obj_index = 0
        elif key == pygame.K_r:
            self.model.reload()
            self.status = "Перечитано с диска"
        elif key == pygame.K_UP:
            self.obj_index -= 1
        elif key == pygame.K_DOWN:
            self.obj_index += 1
        return True

    def _handle_mouse_down(self, pos):
        # Вкладки категорий
        for rect, idx in self._tab_rects:
            if rect.collidepoint(pos):
                self.cat_index = idx
                self.obj_index = 0
                return
        # Стрелки листания объекта
        if self._obj_prev_rect and self._obj_prev_rect.collidepoint(pos):
            self.obj_index -= 1
            return
        if self._obj_next_rect and self._obj_next_rect.collidepoint(pos):
            self.obj_index += 1
            return
        # Кнопки шага -/+
        for field, rect in self._minus_rects.items():
            if rect.collidepoint(pos):
                self._nudge(field, -1)
                return
        for field, rect in self._plus_rects.items():
            if rect.collidepoint(pos):
                self._nudge(field, +1)
                return
        # Дорожки ползунков — начать перетаскивание
        for field, rect in self._slider_rects.items():
            if rect.collidepoint(pos):
                self.dragging_field = field
                self._drag_to(pos[0])
                return

    def _nudge(self, field, direction):
        obj_id = self._current_object()
        if obj_id is None:
            return
        cur = self._get_value(obj_id, field)
        if cur is None:
            return
        spec = FIELD_SPEC.get(field)
        step = spec[2] if spec else 1
        self._set_value(obj_id, field, cur + direction * step)

    def _drag_to(self, mouse_x):
        field = self.dragging_field
        if not field:
            return
        obj_id = self._current_object()
        if obj_id is None:
            return
        spec = FIELD_SPEC.get(field)
        if not spec:
            return
        lo, hi, _step, _is_int = spec
        track = self._slider_rects.get(field)
        if not track:
            return
        frac = (mouse_x - track.x) / max(1, track.w)
        frac = max(0.0, min(1.0, frac))
        self._set_value(obj_id, field, lo + frac * (hi - lo))

    # --- Отрисовка ---

    def draw(self, screen):
        if not self.active:
            return

        self._tab_rects = []
        self._slider_rects = {}
        self._minus_rects = {}
        self._plus_rects = {}
        self._obj_prev_rect = None
        self._obj_next_rect = None

        cat = self._category()
        fields = self._fields()
        rows = 0
        obj_id = self._current_object()
        if obj_id is not None:
            rows = sum(1 for f in fields if self._get_value(obj_id, f) is not None)

        panel_h = 130 + rows * ROW_H
        x, y = PANEL_X, PANEL_Y

        overlay = pygame.Surface((PANEL_W, panel_h), pygame.SRCALPHA)
        overlay.fill((15, 15, 25, 235))
        pygame.draw.rect(overlay, (120, 160, 220), overlay.get_rect(), 2)
        screen.blit(overlay, (x, y))

        pad = 12
        cy = y + pad

        # Заголовок
        title = self.font.render("BALANCE EDITOR", True, (255, 255, 255))
        screen.blit(title, (x + pad, cy))
        cy += 30

        # Вкладки категорий (кликабельные)
        tx = x + pad
        for i, name in enumerate(CATEGORIES):
            selected = (i == self.cat_index)
            col = (140, 255, 160) if selected else (170, 190, 210)
            surf = self.small_font.render(f"[{name}]", True, col)
            rect = pygame.Rect(tx, cy, surf.get_width(), surf.get_height())
            screen.blit(surf, (tx, cy))
            self._tab_rects.append((rect, i))
            tx += surf.get_width() + 10
        cy += 30

        if cat == "Waves":
            info = self.small_font.render("(Волны — на следующем шаге)", True, (200, 200, 160))
            screen.blit(info, (x + pad, cy))
            self._draw_status(screen, x + pad, y + panel_h - 24)
            return

        ids = self._object_ids()
        if obj_id is None:
            warn = self.small_font.render("Нет данных (конфиг не загружен?)", True, (255, 150, 150))
            screen.blit(warn, (x + pad, cy))
            self._draw_status(screen, x + pad, y + panel_h - 24)
            return

        # Строка выбора объекта: < имя [i/n] >
        prev_surf = self.font.render("<", True, (255, 230, 140))
        self._obj_prev_rect = pygame.Rect(x + pad, cy, prev_surf.get_width() + 6, 24)
        screen.blit(prev_surf, (x + pad, cy))

        name_surf = self.font.render(f"{obj_id}  [{self.obj_index + 1}/{len(ids)}]",
                                     True, (255, 230, 140))
        screen.blit(name_surf, (x + pad + 26, cy))

        next_x = x + pad + 26 + name_surf.get_width() + 12
        next_surf = self.font.render(">", True, (255, 230, 140))
        self._obj_next_rect = pygame.Rect(next_x, cy, next_surf.get_width() + 6, 24)
        screen.blit(next_surf, (next_x, cy))
        cy += 32

        # Поля-ползунки
        for field in fields:
            val = self._get_value(obj_id, field)
            if val is None:
                continue
            self._draw_slider_row(screen, x, cy, field, val)
            cy += ROW_H

        self._draw_status(screen, x + pad, y + panel_h - 24)

    def _draw_slider_row(self, screen, x, cy, field, val):
        pad = 12
        # Название поля
        label = self.small_font.render(field, True, (200, 200, 210))
        screen.blit(label, (x + pad, cy + 4))

        spec = FIELD_SPEC.get(field)
        track_x = x + SLIDER_X
        track_rect = pygame.Rect(track_x, cy + 10, SLIDER_W, 6)

        if spec:
            lo, hi, _step, _is_int = spec
            # Дорожка
            pygame.draw.rect(screen, (70, 80, 100), track_rect, border_radius=3)
            # Заполнение и ручка
            frac = 0.0
            if hi > lo:
                frac = max(0.0, min(1.0, (float(val) - lo) / (hi - lo)))
            fill_w = int(SLIDER_W * frac)
            pygame.draw.rect(screen, (120, 200, 255),
                             pygame.Rect(track_x, cy + 10, fill_w, 6), border_radius=3)
            knob_x = track_x + fill_w
            pygame.draw.circle(screen, (230, 240, 255), (knob_x, cy + 13), 7)
            self._slider_rects[field] = track_rect

            # Кнопки -/+
            minus_rect = pygame.Rect(track_x + SLIDER_W + 10, cy + 4, BTN_W, 22)
            plus_rect = pygame.Rect(track_x + SLIDER_W + 10 + BTN_W + 6, cy + 4, BTN_W, 22)
            self._minus_rects[field] = minus_rect
            self._plus_rects[field] = plus_rect
            for rect, sym in ((minus_rect, "-"), (plus_rect, "+")):
                pygame.draw.rect(screen, (60, 70, 95), rect, border_radius=4)
                pygame.draw.rect(screen, (120, 140, 180), rect, 1, border_radius=4)
                sym_surf = self.small_font.render(sym, True, (230, 240, 255))
                screen.blit(sym_surf, (rect.centerx - sym_surf.get_width() // 2,
                                       rect.centery - sym_surf.get_height() // 2))

            # Текущее значение
            val_surf = self.small_font.render(str(val), True, (255, 255, 160))
            screen.blit(val_surf, (plus_rect.right + 10, cy + 4))
        else:
            # Поле без спецификации ползунка — просто значение
            val_surf = self.small_font.render(str(val), True, (255, 255, 160))
            screen.blit(val_surf, (track_x, cy + 4))

    def _draw_status(self, screen, x, y):
        if self.status:
            surf = self.small_font.render(self.status, True, (160, 200, 255))
            screen.blit(surf, (x, y))
