# core/balance_editor/editor.py
"""Панель редактора баланса (dev-инструмент).

Оверлей поверх игры, рисуется через pygame на UI-поверхность (как консоль).
Открывается командой `balance` в dev-консоли.

Управление:
  Tab            — переключить категорию (Башни / Враги / Волны)
  ↑/↓            — выбрать объект (башню/врага)
  ←/→            — выбрать поле
  цифры/точка/-  — ввод нового значения
  Enter          — применить (записать в конфиг)
  Backspace      — стереть символ ввода
  R              — перечитать конфиги с диска (сброс несохранённого в буфере)
  Esc            — закрыть панель
"""
import pygame

from .model import BalanceModel, TOWER_FIELDS, ENEMY_FIELDS

CATEGORIES = ["Towers", "Enemies", "Waves"]


class BalanceEditor:
    def __init__(self, game):
        self.game = game
        self.active = False
        self.model = BalanceModel()

        self.cat_index = 0        # индекс категории
        self.obj_index = 0        # индекс объекта (башня/враг)
        self.field_index = 0      # индекс поля
        self.input_buffer = ""    # набираемое значение
        self.status = ""          # строка статуса (результат применения)

        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)

    # --- Открытие/закрытие ---

    def toggle(self):
        self.active = not self.active
        if self.active:
            self.model.reload()
            self.input_buffer = ""
            self.status = "R=reload  Tab=category  arrows=nav  Enter=apply"

    # --- Текущий контекст ---

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

    def _current_field(self):
        fields = self._fields()
        if not fields:
            return None
        self.field_index = max(0, min(self.field_index, len(fields) - 1))
        return fields[self.field_index]

    def _get_value(self, obj_id, field):
        cat = self._category()
        if cat == "Towers":
            return self.model.get_tower_value(obj_id, field)
        if cat == "Enemies":
            return self.model.get_enemy_value(obj_id, field)
        return None

    # --- Ввод ---

    def handle_event(self, event):
        """Возвращает True, если событие поглощено панелью."""
        if not self.active:
            return False
        if event.type != pygame.KEYDOWN:
            return False

        key = event.key

        if key == pygame.K_ESCAPE:
            self.active = False
            return True
        if key == pygame.K_TAB:
            self.cat_index = (self.cat_index + 1) % len(CATEGORIES)
            self.obj_index = 0
            self.field_index = 0
            self.input_buffer = ""
            return True
        if key == pygame.K_r:
            self.model.reload()
            self.input_buffer = ""
            self.status = "Перечитано с диска"
            return True
        if key == pygame.K_UP:
            self.obj_index -= 1
            self.input_buffer = ""
            return True
        if key == pygame.K_DOWN:
            self.obj_index += 1
            self.input_buffer = ""
            return True
        if key == pygame.K_LEFT:
            self.field_index -= 1
            self.input_buffer = ""
            return True
        if key == pygame.K_RIGHT:
            self.field_index += 1
            self.input_buffer = ""
            return True
        if key == pygame.K_BACKSPACE:
            self.input_buffer = self.input_buffer[:-1]
            return True
        if key == pygame.K_RETURN:
            self._apply()
            return True

        # Набор числа
        ch = event.unicode
        if ch and ch in "0123456789.-":
            self.input_buffer += ch
            return True

        return True  # панель активна — поглощаем всё, чтобы не рулить игрой

    def _apply(self):
        obj_id = self._current_object()
        field = self._current_field()
        if obj_id is None or field is None:
            self.status = "Нечего применять"
            return
        if not self.input_buffer:
            self.status = "Пустой ввод"
            return
        try:
            value = self._parse(self.input_buffer)
        except ValueError:
            self.status = f"Не число: {self.input_buffer}"
            return

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
        self.input_buffer = ""

    @staticmethod
    def _parse(text):
        """Целое остаётся int, дробное — float."""
        if "." in text:
            return float(text)
        return int(text)

    # --- Отрисовка ---

    def draw(self, screen):
        if not self.active:
            return

        sw, sh = screen.get_size()
        panel_w = min(560, sw - 40)
        panel_h = min(520, sh - 40)
        x = 20
        y = 20

        overlay = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        overlay.fill((15, 15, 25, 235))
        pygame.draw.rect(overlay, (120, 160, 220), overlay.get_rect(), 2)
        screen.blit(overlay, (x, y))

        pad = 12
        cy = y + pad

        # Заголовок + вкладки категорий
        title = self.font.render("BALANCE EDITOR", True, (255, 255, 255))
        screen.blit(title, (x + pad, cy))
        cy += 30

        tabs = []
        for i, name in enumerate(CATEGORIES):
            mark = ">" if i == self.cat_index else " "
            tabs.append(f"{mark}{name}")
        tab_surf = self.small_font.render("  ".join(tabs), True, (180, 220, 255))
        screen.blit(tab_surf, (x + pad, cy))
        cy += 28

        cat = self._category()

        if cat == "Waves":
            info = self.small_font.render("(Волны — на следующем шаге)", True, (200, 200, 160))
            screen.blit(info, (x + pad, cy))
            self._draw_status(screen, x + pad, y + panel_h - 26)
            return

        obj_id = self._current_object()
        ids = self._object_ids()
        if obj_id is None:
            warn = self.small_font.render("Нет данных (конфиг не загружен?)", True, (255, 150, 150))
            screen.blit(warn, (x + pad, cy))
            self._draw_status(screen, x + pad, y + panel_h - 26)
            return

        # Текущий объект + позиция в списке
        obj_line = self.font.render(
            f"{obj_id}   [{self.obj_index + 1}/{len(ids)}]  (up/down)",
            True, (255, 230, 140))
        screen.blit(obj_line, (x + pad, cy))
        cy += 30

        # Поля объекта
        fields = self._fields()
        for i, field in enumerate(fields):
            val = self._get_value(obj_id, field)
            if val is None:
                continue  # у этой сущности такого поля нет
            selected = (i == self.field_index)
            mark = ">" if selected else " "
            color = (140, 255, 160) if selected else (200, 200, 210)
            line = f"{mark} {field:<20} {val}"
            if selected and self.input_buffer:
                line += f"   ->  {self.input_buffer}_"
            surf = self.small_font.render(line, True, color)
            screen.blit(surf, (x + pad, cy))
            cy += 22

        self._draw_status(screen, x + pad, y + panel_h - 26)

    def _draw_status(self, screen, x, y):
        if self.status:
            surf = self.small_font.render(self.status, True, (160, 200, 255))
            screen.blit(surf, (x, y))
