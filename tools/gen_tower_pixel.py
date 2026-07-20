# tools/gen_tower_pixel.py
"""Процедурный пиксель-арт башен: техно тёмное фэнтези (железо + магия).

Каждая башня = клёпаная железная платформа + устройство по типу.
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
    # Кабина
    rect(g, 12, 12, 19, 19, IRON)
    rect(g, 12, 12, 19, 13, IRON_L)
    rect(g, 13, 15, 15, 17, IRON_D)  # смотровая щель
    # Длинный ствол по диагонали вверх-вправо
    ln = 8 + lv
    for i in range(ln):
        px(g, 18 + i, 11 - i // 2, IRON_L)
        px(g, 18 + i, 12 - i // 2, IRON_D)
    # Прицел со светящейся линзой
    rect(g, 15, 8, 17, 10, IRON_D)
    px(g, 16, 9, gl)
    if lv >= 3:
        rect(g, 10, 14, 11, 19, IRON_D)  # опора
    if lv >= 4:
        px(g, 18 + ln - 1, 11 - (ln - 1) // 2 - 1, gl)  # дульная энергия


def dev_turret(g, lv, gl):
    rect(g, 11, 13, 20, 19, IRON)
    rect(g, 11, 13, 20, 14, IRON_L)
    # Два ствола вверх
    n = 2 if lv < 3 else 3
    xs = (13, 18) if n == 2 else (12, 15, 19)
    for x in xs:
        rect(g, x, 6, x + 1, 13, IRON_D)
        rect(g, x, 6, x, 13, IRON_L)
        px(g, x, 5, OUT)
    # Короб с лентой
    rect(g, 8, 15, 10, 19, IRON_D)
    px(g, 9, 16, HAZARD)
    if lv >= 4:
        for x in xs:
            px(g, x, 5, gl)


def dev_flamethrower(g, lv, gl):
    # Два топливных бака
    rect(g, 9, 10, 13, 19, RUST)
    rect(g, 9, 10, 13, 11, RUST_D)
    rect(g, 10, 12, 10, 17, (140, 84, 52))
    rect(g, 17, 10, 21, 19, IRON)
    rect(g, 17, 10, 21, 11, IRON_L)
    # Вентиль и труба к соплу
    rect(g, 13, 13, 17, 14, IRON_D)
    rect(g, 14, 6, 16, 12, IRON_D)
    # Сопло с дежурным пламенем
    rect(g, 14, 5, 16, 6, IRON_L)
    px(g, 15, 4, gl)
    px(g, 15, 3, (255, 220, 120))
    if lv >= 3:
        rect(g, 22, 13, 23, 19, RUST_D)   # третий бак
    if lv >= 4:
        px(g, 10, 13, gl)  # светящийся индикатор


def dev_electric(g, lv, gl):
    # Катушка Теслы: сужающиеся кольца
    rings = [(10, 21, 18), (11, 20, 15), (12, 19, 12), (13, 18, 9)]
    for i, (x0, x1, y) in enumerate(rings[:2 + lv // 2]):
        rect(g, x0, y, x1, y + 1, IRON)
        rect(g, x0, y, x1, y, IRON_L)
    # Сердечник
    rect(g, 15, 8, 16, 19, IRON_D)
    # Энергетический шар
    rect(g, 14, 4, 17, 7, gl)
    px(g, 15, 5, (255, 255, 255))
    px(g, 16, 6, (255, 255, 255))
    if lv >= 3:
        px(g, 12, 6, gl)
        px(g, 19, 8, gl)
    if lv >= 4:
        px(g, 10, 10, gl)
        px(g, 21, 12, gl)


def dev_tank(g, lv, gl, liquid):
    """Бак с светящейся жидкостью (вода/заморозка/кислота)."""
    rect(g, 11, 8, 20, 19, IRON)
    rect(g, 11, 8, 20, 9, IRON_L)
    # Смотровое окно с жидкостью
    rect(g, 13, 11, 18, 16, liquid)
    px(g, 14, 12, (255, 255, 255))
    # Пузыри
    px(g, 16, 14, tuple(min(255, c + 60) for c in liquid))
    px(g, 15, 12, tuple(min(255, c + 60) for c in liquid))
    # Труба сверху
    rect(g, 14, 5, 17, 7, IRON_D)
    rect(g, 14, 5, 17, 5, IRON_L)
    if lv >= 3:
        rect(g, 9, 12, 10, 19, IRON_D)  # доп. труба
        px(g, 9, 14, liquid)
    if lv >= 4:
        px(g, 15, 4, gl)


def dev_pvo(g, lv, gl):
    # Рама
    rect(g, 12, 16, 19, 19, IRON)
    # Ракеты, направленные вверх под углом
    n = 2 if lv < 3 else 3
    xs = (12, 17) if n == 2 else (10, 15, 20)
    for x in xs:
        rect(g, x, 8, x + 1, 15, IRON_L)
        rect(g, x, 8, x, 15, IRON)
        px(g, x, 7, (200, 60, 50))
        px(g, x + 1, 7, (200, 60, 50))
    if lv >= 4:
        for x in xs:
            px(g, x, 6, gl)


def dev_rocket(g, lv, gl):
    n = 2 if lv < 4 else 3
    xs = (11, 17) if n == 2 else (9, 14, 19)
    for x in xs:
        rect(g, x, 6, x + 2, 16, IRON_L)
        rect(g, x, 6, x, 16, IRON)
        rect(g, x, 5, x + 2, 6, (200, 60, 50))
        px(g, x + 1, 4, (200, 60, 50))
        rect(g, x, 17, x + 2, 18, IRON_D)
    rect(g, 9, 18, 22, 19, IRON)
    if lv >= 3:
        px(g, 12, 17, gl)
        px(g, 18, 17, gl)


DEVICES = {
    'sniper': dev_sniper,
    'turret': dev_turret,
    'flamethrower': dev_flamethrower,
    'electric': dev_electric,
    'water': lambda g, lv, gl: dev_tank(g, lv, gl, (60, 120, 210)),
    'freeze': lambda g, lv, gl: dev_tank(g, lv, gl, (140, 210, 235)),
    'acid': lambda g, lv, gl: dev_tank(g, lv, gl, (90, 190, 60)),
    'pvo': dev_pvo,
    'rocket': dev_rocket,
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
            g = [[None] * GW for _ in range(GH)]
            draw_base(g, lv, gl)
            dev(g, lv, gl)
            outline(g)
            grid_to_image(g).save(f"{out_dir}/level_{lv}.png")
        print(f"OK towers_pixel/{tower_id}")


if __name__ == '__main__':
    generate()
