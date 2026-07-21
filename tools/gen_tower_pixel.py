# tools/gen_tower_pixel.py
"""Процедурный пиксель-арт башен: техно тёмное фэнтези (железо + магия).

Каждая башня = клёпаная железная платформа + устройство по типу.
Силуэты уникальны: пулемёт — станковый с горизонтальным стволом,
огнемёт — бак со шлангом и соплом, электро — катушка Теслы,
ПВО — радар с ракетами, ракетная — пакет направляющих РСЗО.
Уровни 1-4 наращивают обвес: броневые плиты -> кабели/усиление ->
шипы и светящиеся руны.

9 типов x 4 уровня -> assets/images/towers_pixel/<id>/level_N.png
Запуск: python tools/gen_tower_pixel.py
"""
import os
from PIL import Image

GW = GH = 32
SCALE = 4
CANVAS = 128

# ===== Палитра железа =====
IRON = (52, 55, 62)
IRON_D = (36, 38, 45)
IRON_L = (80, 85, 96)
RUST = (108, 62, 38)
RUST_D = (78, 45, 30)
HAZARD = (164, 136, 46)
COPPER = (152, 94, 54)
COPPER_D = (110, 66, 38)
WOOD = (96, 66, 40)
RED = (200, 60, 50)
OUT = (16, 15, 18)

# Цвет энергии по типу башни (магическая составляющая)
GLOW = {
    'sniper':       (255, 96, 64),
    'turret':       (240, 210, 130),
    'flamethrower': (255, 150, 40),
    'electric':     (120, 220, 255),
    'water':        (90, 170, 255),
    'pvo':          (200, 215, 235),
    'freeze':       (170, 235, 255),
    'acid':         (150, 255, 90),
    'rocket':       (255, 90, 60),
}


def px(g, x, y, c):
    if 0 <= x < GW and 0 <= y < GH:
        g[y][x] = c


def rect(g, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px(g, x, y, c)


def outline(g):
    marks = []
    for y in range(GH):
        for x in range(GW):
            if g[y][x] is None:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < GW and 0 <= ny < GH and g[ny][nx] is not None and g[ny][nx] != OUT:
                        marks.append((x, y))
                        break
    for x, y in marks:
        g[y][x] = OUT


# ============================================================
# ПЛАТФОРМА (общая для всех башен)
# ============================================================

def draw_base(g, level, glow):
    # Верхняя грань платформы
    rect(g, 5, 20, 26, 23, IRON)
    rect(g, 5, 20, 26, 20, IRON_L)
    # Передняя (нижняя) грань
    rect(g, 5, 24, 26, 29, IRON_D)
    # Заклёпки
    for x, y in ((6, 21), (25, 21), (6, 28), (25, 28)):
        px(g, x, y, IRON_L)
    # Ржавчина (фиксированные пятна)
    rect(g, 8, 25, 10, 26, RUST_D)
    px(g, 9, 27, RUST)
    rect(g, 21, 24, 22, 25, RUST_D)
    px(g, 12, 20, RUST)
    # Аварийная полоса по кромке
    for i, x in enumerate(range(6, 26, 2)):
        px(g, x, 24, HAZARD if i % 2 == 0 else IRON_D)

    if level >= 2:
        # Боковые броневые плиты
        rect(g, 2, 21, 4, 28, IRON)
        rect(g, 2, 21, 4, 22, IRON_L)
        rect(g, 27, 21, 29, 28, IRON)
        rect(g, 27, 21, 29, 22, IRON_L)
        px(g, 3, 24, IRON_L)
        px(g, 28, 24, IRON_L)

    if level >= 3:
        # Кабели от платформы к устройству
        rect(g, 4, 15, 4, 20, IRON_D)
        rect(g, 27, 15, 27, 20, IRON_D)
        px(g, 4, 17, glow)
        px(g, 27, 18, glow)

    if level >= 4:
        # Шипы по углам
        px(g, 4, 19, IRON_L)
        px(g, 4, 18, IRON)
        px(g, 27, 19, IRON_L)
        px(g, 27, 18, IRON)
        # Светящиеся руны на передней грани
        for x in (11, 15, 19):
            px(g, x, 27, glow)
            px(g, x, 26, glow)
            px(g, x + 1, 27, glow)


# ============================================================
# УСТРОЙСТВА ПО ТИПАМ
# ============================================================

def dev_sniper(g, lv, gl):
    """Снайперская винтовка на треноге: очень длинный ствол по диагонали."""
    # Тренога
    rect(g, 14, 15, 16, 19, IRON)
    rect(g, 11, 18, 12, 19, IRON_D)
    rect(g, 18, 18, 19, 19, IRON_D)
    px(g, 13, 17, IRON_D)
    px(g, 17, 17, IRON_D)
    # Деревянный приклад
    rect(g, 6, 14, 9, 17, WOOD)
    rect(g, 6, 14, 9, 14, RUST_D)
    # Ствольная коробка
    rect(g, 10, 12, 15, 16, IRON)
    rect(g, 10, 12, 15, 12, IRON_L)
    # Очень длинный ствол по диагонали вверх-вправо
    ln = 12 + lv
    for i in range(ln):
        x, y = 15 + i, 12 - i // 2
        px(g, x, y, IRON_L)
        px(g, x, y + 1, IRON_D)
    # Оптический прицел со светящейся линзой
    rect(g, 11, 9, 14, 10, IRON_D)
    px(g, 14, 9, gl)
    if lv >= 3:
        # Дульный тормоз
        tx, ty = 15 + ln - 1, 12 - (ln - 1) // 2
        rect(g, tx, ty - 1, tx + 1, ty + 2, IRON_D)
    if lv >= 4:
        px(g, 15 + ln, 12 - ln // 2, gl)  # дульная энергия


def dev_turret(g, lv, gl):
    """Станковый пулемёт: тренога, горизонтальный ствол с кожухом, короб ленты."""
    # Тренога
    rect(g, 14, 15, 16, 19, IRON)
    rect(g, 11, 18, 12, 19, IRON_D)
    rect(g, 18, 18, 19, 19, IRON_D)
    # Ствольная коробка
    rect(g, 10, 11, 18, 15, IRON)
    rect(g, 10, 11, 18, 11, IRON_L)
    # Рукоятки сзади
    px(g, 9, 12, IRON_D)
    px(g, 9, 14, IRON_D)
    # Горизонтальный ствол с кожухом охлаждения
    blen = 8 + lv
    rect(g, 19, 12, 18 + blen, 13, IRON_L)
    for x in range(20, 18 + blen, 2):
        px(g, x, 12, IRON_D)  # отверстия кожуха
    # Дульный срез
    rect(g, 18 + blen, 11, 18 + blen, 14, IRON_D)
    # Короб с патронной лентой
    rect(g, 6, 12, 9, 17, IRON_D)
    rect(g, 6, 12, 9, 12, IRON)
    px(g, 7, 13, HAZARD)
    px(g, 8, 14, HAZARD)  # лента в коробе
    px(g, 9, 13, HAZARD)  # лента в приёмник
    if lv >= 2:
        # Бронещиток над коробкой
        rect(g, 12, 6, 13, 11, IRON)
        rect(g, 12, 6, 12, 11, IRON_L)
    if lv >= 4:
        px(g, 19 + blen, 12, gl)  # вспышка на срезе
        px(g, 19 + blen, 13, gl)


def dev_flamethrower(g, lv, gl):
    """Стационарный огнемёт: топливный бак, шланг, сопло с дежурным пламенем."""
    # Большой ржавый бак
    rect(g, 8, 7, 14, 19, RUST)
    rect(g, 9, 6, 13, 6, RUST_D)  # скруглённый верх
    rect(g, 8, 7, 14, 8, RUST_D)
    rect(g, 9, 9, 9, 17, (140, 84, 52))  # блик
    # Полоса опасности на баке
    for i, x in enumerate(range(8, 15)):
        px(g, x, 13, HAZARD if i % 2 == 0 else IRON_D)
    # Вентиль сверху
    rect(g, 10, 5, 12, 5, IRON_D)
    px(g, 11, 4, IRON_L)
    # Шланг от бака к соплу
    rect(g, 15, 14, 19, 15, IRON_D)
    px(g, 15, 13, IRON_D)
    # Сопло направлено вправо
    rect(g, 20, 13, 24, 16, IRON)
    rect(g, 20, 13, 24, 13, IRON_L)
    rect(g, 25, 13, 26, 16, IRON_L)  # раструб
    # Дежурное пламя
    px(g, 27, 14, gl)
    px(g, 27, 15, gl)
    px(g, 28, 15, (255, 220, 120))
    if lv >= 2:
        # Второй бак поменьше
        rect(g, 15, 8, 18, 12, IRON)
        rect(g, 15, 8, 18, 8, IRON_L)
    if lv >= 3:
        # Третий бак
        rect(g, 5, 10, 7, 19, RUST_D)
        px(g, 6, 12, RUST)
    if lv >= 4:
        px(g, 12, 10, gl)  # индикатор давления
        px(g, 29, 14, gl)  # пламя мощнее
        px(g, 28, 13, gl)


def dev_electric(g, lv, gl):
    """Катушка Теслы: медные обмотки, сердечник, шар-разрядник с дугами."""
    # Сердечник
    rect(g, 14, 8, 17, 19, IRON_D)
    # Медные обмотки (сужаются кверху); больше витков с уровнем
    coils = [(11, 20, 18), (11, 20, 16), (12, 19, 14), (12, 19, 12), (13, 18, 10)]
    for x0, x1, y in coils[:3 + lv // 2]:
        rect(g, x0, y, x1, y, COPPER)
        px(g, x0, y, COPPER_D)
        px(g, x1, y, COPPER_D)
    # Тороид-разрядник (шар со скруглением)
    rect(g, 13, 3, 18, 3, gl)
    rect(g, 12, 4, 19, 6, gl)
    rect(g, 13, 7, 18, 7, gl)
    px(g, 15, 4, (255, 255, 255))
    px(g, 16, 4, (255, 255, 255))
    px(g, 15, 5, (255, 255, 255))
    if lv >= 2:
        # Электрические дуги
        px(g, 10, 5, gl)
        px(g, 21, 4, gl)
    if lv >= 3:
        px(g, 9, 8, gl)
        px(g, 22, 7, gl)
        px(g, 11, 2, (255, 255, 255))
    if lv >= 4:
        px(g, 8, 3, gl)
        px(g, 23, 2, gl)
        px(g, 20, 1, (255, 255, 255))


def _tank_body(g, liquid):
    """Общий корпус бака со смотровым окном."""
    rect(g, 11, 9, 20, 19, IRON)
    rect(g, 11, 9, 20, 10, IRON_L)
    rect(g, 13, 12, 18, 17, liquid)
    px(g, 14, 13, (255, 255, 255))


def dev_water(g, lv, gl):
    """Водяная: бак + водомёт сверху со струёй капель."""
    liquid = (60, 120, 210)
    _tank_body(g, liquid)
    # Пузыри в окне
    px(g, 16, 15, (140, 190, 255))
    px(g, 15, 13, (140, 190, 255))
    # Водомёт сверху, направлен вправо-вверх
    rect(g, 14, 6, 17, 8, IRON_D)
    rect(g, 18, 5, 21, 6, IRON_L)
    # Струя капель
    px(g, 22, 4, liquid)
    px(g, 24, 3, (140, 190, 255))
    px(g, 26, 4, liquid)
    if lv >= 3:
        rect(g, 9, 13, 10, 19, IRON_D)  # доп. труба
        px(g, 9, 15, liquid)
    if lv >= 4:
        px(g, 28, 3, (200, 230, 255))
        px(g, 25, 5, liquid)


def dev_freeze(g, lv, gl):
    """Заморозка: криобак с инеем, сосульками и снежинками."""
    liquid = (140, 210, 235)
    _tank_body(g, liquid)
    # Морозильная установка сверху с инеем
    rect(g, 13, 6, 18, 8, IRON_L)
    rect(g, 13, 6, 18, 6, (220, 245, 255))
    # Сосульки по нижней кромке бака
    for x in (12, 15, 19):
        px(g, x, 20, (200, 240, 255))
        px(g, x, 21, (170, 225, 250))
    px(g, 15, 22, (200, 240, 255))
    # Снежинки вокруг
    px(g, 9, 8, (230, 250, 255))
    px(g, 22, 11, (230, 250, 255))
    if lv >= 3:
        px(g, 8, 14, (230, 250, 255))
        px(g, 23, 6, (230, 250, 255))
    if lv >= 4:
        px(g, 15, 4, gl)
        px(g, 12, 21, (230, 250, 255))


def dev_acid(g, lv, gl):
    """Кислота: открытый чан с кипящей жижей, пузырями и подтёком."""
    liquid = (90, 190, 60)
    liquid_l = (150, 240, 110)
    # Открытый чан
    rect(g, 10, 10, 21, 19, IRON)
    rect(g, 10, 10, 21, 11, IRON_L)
    # Кипящая поверхность
    rect(g, 12, 9, 19, 10, liquid)
    px(g, 14, 9, liquid_l)
    px(g, 17, 9, liquid_l)
    # Пузыри над чаном
    px(g, 13, 7, liquid_l)
    px(g, 17, 6, liquid)
    # Смотровое окно
    rect(g, 13, 13, 18, 16, liquid)
    px(g, 14, 14, liquid_l)
    # Подтёк по стенке
    px(g, 21, 12, liquid)
    px(g, 21, 13, liquid)
    px(g, 22, 14, (70, 150, 45))
    if lv >= 3:
        px(g, 15, 5, liquid_l)  # пузыри активнее
        px(g, 19, 7, liquid)
    if lv >= 4:
        px(g, 11, 6, liquid_l)
        px(g, 20, 4, liquid)


def dev_pvo(g, lv, gl):
    """ПВО: большая радарная тарелка на мачте + зенитные ракеты под углом."""
    # Мачта
    rect(g, 8, 13, 9, 19, IRON_D)
    # Большая тарелка (вогнутая, смотрит вверх-влево)
    rect(g, 3, 8, 13, 9, IRON_L)
    rect(g, 4, 10, 12, 11, IRON)
    rect(g, 6, 12, 11, 12, IRON_D)
    # Излучатель на штанге
    px(g, 8, 7, IRON_D)
    px(g, 8, 6, gl)
    # Зенитные ракеты (толстые, под углом вверх-вправо)
    starts = ((15, 18), (20, 19)) if lv < 3 else ((14, 18), (19, 19), (24, 19))
    for sx, sy in starts:
        for i in range(9):
            x, y = sx + i // 2, sy - i
            px(g, x, y, IRON_L)
            px(g, x + 1, y, IRON_L)
            px(g, x + 2, y, IRON)
        # Красная БЧ (2 пикселя)
        px(g, sx + 4, sy - 9, RED)
        px(g, sx + 5, sy - 9, RED)
        px(g, sx + 5, sy - 10, RED)
        # Стабилизаторы у хвоста
        px(g, sx - 1, sy, IRON_D)
        px(g, sx + 3, sy, IRON_D)
    if lv >= 4:
        for sx, sy in starts:
            px(g, sx + 6, sy - 11, gl)
        px(g, 8, 5, gl)  # радар активен


def dev_rocket(g, lv, gl):
    """Ракетная: наклонённый пакет труб РСЗО на поворотном лафете."""
    n = 3 if lv < 3 else 4
    # Наклонённые направляющие трубы (вверх-вправо), торцы с носами ракет
    for t in range(n):
        sx, sy = 8 + t * 3, 17 + (t % 2)
        for i in range(11):
            x, y = sx + i // 2, sy - i
            px(g, x, y, IRON_L)
            px(g, x + 1, y, IRON)
            px(g, x + 2, y, IRON_D)
        # Нос ракеты в трубе
        px(g, sx + 5, sy - 11, RED)
        px(g, sx + 6, sy - 11, RED)
    # Поворотный лафет
    rect(g, 11, 17, 20, 19, IRON)
    rect(g, 11, 17, 20, 17, IRON_L)
    px(g, 13, 18, HAZARD)
    px(g, 18, 18, HAZARD)
    if lv >= 4:
        for t in range(n):
            sx, sy = 8 + t * 3, 17 + (t % 2)
            px(g, sx + 6, sy - 12, gl)  # заряжены, светятся


DEVICES = {
    'sniper': dev_sniper,
    'turret': dev_turret,
    'flamethrower': dev_flamethrower,
    'electric': dev_electric,
    'water': dev_water,
    'freeze': dev_freeze,
    'acid': dev_acid,
    'pvo': dev_pvo,
    'rocket': dev_rocket,
}


# ============================================================
# ПОВОРОТНЫЕ ГОЛОВЫ (оружие смотрит ВПРАВО, ось вращения = центр 16,16)
# Для башен, которые целятся стволом: пулемёт и огнемёт.
# База рисуется отдельно (платформа + статичные части).
# ============================================================

def head_turret(g, lv, gl):
    """Пулемёт в плане: короб + ствол вправо, лента слева."""
    # Короб с патронной лентой (сзади, слева от оси)
    rect(g, 7, 13, 10, 18, IRON_D)
    rect(g, 7, 13, 10, 13, IRON)
    px(g, 8, 14, HAZARD)
    px(g, 9, 16, HAZARD)
    # Ствольная коробка на оси
    rect(g, 11, 12, 19, 19, IRON)
    rect(g, 11, 12, 19, 12, IRON_L)
    px(g, 12, 18, IRON_L)  # заклёпка
    px(g, 18, 18, IRON_L)
    # Ствол с кожухом охлаждения (вправо)
    blen = 8 + lv
    rect(g, 20, 14, 19 + blen, 17, IRON_L)
    rect(g, 20, 15, 19 + blen, 16, IRON)
    for x in range(21, 18 + blen, 2):
        px(g, x, 14, IRON_D)  # отверстия кожуха
        px(g, x, 17, IRON_D)
    # Дульный срез
    rect(g, 19 + blen, 13, 20 + blen, 18, IRON_D)
    if lv >= 2:
        # Бронещиток спереди короба
        rect(g, 19, 10, 20, 21, IRON)
        rect(g, 19, 10, 19, 21, IRON_L)
    if lv >= 4:
        px(g, 21 + blen, 15, gl)  # вспышка
        px(g, 21 + blen, 16, gl)


def head_flamethrower(g, lv, gl):
    """Сопло огнемёта в плане: подводка + раструб вправо, бачок сзади."""
    # Малый расходный бачок (сзади)
    rect(g, 7, 12, 10, 19, RUST)
    rect(g, 7, 12, 10, 13, RUST_D)
    px(g, 8, 15, (140, 84, 52))
    # Подводящая труба на оси
    rect(g, 11, 14, 16, 17, IRON_D)
    px(g, 13, 14, IRON)  # хомут
    px(g, 13, 17, IRON)
    # Сопло
    rect(g, 17, 13, 23, 18, IRON)
    rect(g, 17, 13, 23, 13, IRON_L)
    # Раструб
    rect(g, 24, 12, 26, 19, IRON_L)
    rect(g, 24, 12, 24, 19, IRON)
    # Дежурное пламя
    px(g, 27, 15, gl)
    px(g, 27, 16, gl)
    px(g, 28, 15, (255, 220, 120))
    if lv >= 3:
        rect(g, 5, 13, 6, 18, RUST_D)  # бачок больше
    if lv >= 4:
        px(g, 9, 14, gl)   # индикатор давления
        px(g, 29, 16, gl)  # пламя мощнее


def base_turret(g, lv, gl):
    """База пулемёта: платформа + поворотная тумба."""
    draw_base(g, lv, gl)
    rect(g, 13, 16, 18, 19, IRON_D)
    rect(g, 14, 15, 17, 15, IRON)
    px(g, 15, 17, IRON_L)  # ось
    px(g, 16, 17, IRON_L)


def base_flamethrower(g, lv, gl):
    """База огнемёта: платформа + большой топливный бак (статичный)."""
    draw_base(g, lv, gl)
    # Большой бак слева на платформе
    rect(g, 5, 12, 10, 21, RUST)
    rect(g, 6, 11, 9, 11, RUST_D)
    rect(g, 5, 12, 10, 13, RUST_D)
    rect(g, 6, 14, 6, 19, (140, 84, 52))
    for i, x in enumerate(range(5, 11)):
        px(g, x, 17, HAZARD if i % 2 == 0 else IRON_D)
    # Вентиль
    px(g, 7, 10, IRON_D)
    px(g, 8, 10, IRON_D)
    # Поворотная тумба по центру
    rect(g, 14, 16, 19, 19, IRON_D)
    px(g, 16, 17, IRON_L)
    if lv >= 3:
        rect(g, 25, 14, 26, 21, RUST_D)  # запасной баллон справа
        px(g, 25, 16, RUST)


def head_sniper(g, lv, gl):
    """Ствол снайперки в плане: длинный ствол вправо, приклад слева."""
    # Деревянный приклад (сзади, слева от оси)
    rect(g, 6, 14, 9, 18, WOOD)
    rect(g, 6, 14, 9, 14, RUST_D)
    # Ствольная коробка на оси
    rect(g, 10, 13, 16, 18, IRON)
    rect(g, 10, 13, 16, 13, IRON_L)
    px(g, 11, 17, IRON_L)  # заклёпка
    px(g, 15, 17, IRON_L)
    # Оптический прицел сверху коробки
    rect(g, 11, 11, 15, 12, IRON_D)
    px(g, 14, 11, gl)
    # Очень длинный ствол вправо
    blen = 12 + lv
    rect(g, 17, 15, 16 + blen, 16, IRON_L)
    rect(g, 17, 15, 16 + blen, 15, IRON)
    # Дульный тормоз
    if lv >= 3:
        rect(g, 16 + blen, 14, 17 + blen, 17, IRON_D)
    if lv >= 4:
        px(g, 18 + blen, 15, gl)  # дульная энергия
        px(g, 18 + blen, 16, gl)


def base_sniper(g, lv, gl):
    """База снайперки: платформа + тренога с поворотной тумбой."""
    draw_base(g, lv, gl)
    # Тренога
    rect(g, 14, 16, 17, 19, IRON)
    rect(g, 11, 18, 12, 19, IRON_D)
    rect(g, 19, 18, 20, 19, IRON_D)
    # Поворотная тумба по центру
    rect(g, 14, 15, 17, 16, IRON_D)
    px(g, 15, 16, IRON_L)  # ось
    px(g, 16, 16, IRON_L)


def head_water(g, lv, gl):
    """Водомёт в плане: ствол-брандспойт вправо, бачок сзади."""
    liquid = (60, 120, 210)
    # Насосный бачок (сзади, слева от оси)
    rect(g, 7, 12, 10, 18, IRON)
    rect(g, 7, 12, 10, 12, IRON_L)
    rect(g, 8, 14, 9, 16, liquid)  # смотровое окно
    # Корпус помпы на оси
    rect(g, 11, 13, 17, 18, IRON)
    rect(g, 11, 13, 17, 13, IRON_L)
    px(g, 12, 17, IRON_L)
    px(g, 16, 17, IRON_L)
    # Ствол-брандспойт вправо
    blen = 7 + lv
    rect(g, 18, 14, 17 + blen, 17, IRON_D)
    rect(g, 18, 14, 17 + blen, 14, IRON_L)
    # Раструб-сопло
    rect(g, 18 + blen, 13, 19 + blen, 18, IRON_L)
    # Капли воды на срезе
    px(g, 20 + blen, 15, (140, 190, 255))
    px(g, 21 + blen, 16, liquid)
    if lv >= 4:
        px(g, 22 + blen, 15, (200, 230, 255))


def base_water(g, lv, gl):
    """База водомёта: платформа + бак-резервуар + поворотная тумба."""
    draw_base(g, lv, gl)
    liquid = (60, 120, 210)
    # Резервуар слева на платформе
    rect(g, 5, 12, 10, 21, IRON)
    rect(g, 5, 12, 10, 13, IRON_L)
    rect(g, 6, 15, 9, 19, liquid)  # вода в баке
    px(g, 7, 16, (140, 190, 255))
    # Поворотная тумба по центру
    rect(g, 14, 16, 19, 19, IRON_D)
    px(g, 16, 17, IRON_L)
    if lv >= 3:
        rect(g, 25, 15, 26, 21, IRON)  # доп. труба справа
        px(g, 25, 17, liquid)


ROTATING = {
    'turret': (base_turret, head_turret),
    'flamethrower': (base_flamethrower, head_flamethrower),
    'sniper': (base_sniper, head_sniper),
    'water': (base_water, head_water),
}


def grid_to_image(g) -> Image.Image:
    img = Image.new('RGBA', (GW, GH), (0, 0, 0, 0))
    for y in range(GH):
        for x in range(GW):
            if g[y][x] is not None:
                img.putpixel((x, y), (*g[y][x], 255))
    img = img.resize((GW * SCALE, GH * SCALE), Image.NEAREST)
    canvas = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    canvas.paste(img, ((CANVAS - GW * SCALE) // 2, (CANVAS - GH * SCALE) // 2), img)
    return canvas


def generate():
    for tower_id, dev in DEVICES.items():
        out_dir = f"assets/images/towers_pixel/{tower_id}"
        os.makedirs(out_dir, exist_ok=True)
        gl = GLOW[tower_id]
        for lv in range(1, 5):
            if tower_id in ROTATING:
                # База и голова отдельными файлами (голова вращается в игре)
                base_fn, head_fn = ROTATING[tower_id]
                g = [[None] * GW for _ in range(GH)]
                base_fn(g, lv, gl)
                outline(g)
                grid_to_image(g).save(f"{out_dir}/level_{lv}.png")
                g = [[None] * GW for _ in range(GH)]
                head_fn(g, lv, gl)
                outline(g)
                grid_to_image(g).save(f"{out_dir}/head_{lv}.png")
            else:
                g = [[None] * GW for _ in range(GH)]
                draw_base(g, lv, gl)
                dev(g, lv, gl)
                outline(g)
                grid_to_image(g).save(f"{out_dir}/level_{lv}.png")
        print(f"OK towers_pixel/{tower_id}")


if __name__ == '__main__':
    generate()
