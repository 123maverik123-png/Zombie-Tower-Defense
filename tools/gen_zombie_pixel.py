# tools/gen_zombie_pixel.py
"""Процедурный пиксель-арт зомби: 4 направления x 4 кадра ходьбы.

Перспектива:
  down  — вид спереди (лицо)
  up    — вид сзади (спина)
  left/right — профиль (руки вытянуты вперёд, шаркающая походка)

Рисуем на логической сетке 26x34, масштабируем x4 (NEAREST) для чёткого пикселя.
Запуск: python tools/gen_zombie_pixel.py
"""
import os
from PIL import Image

GW, GH = 26, 34     # логическая сетка
SCALE = 4           # апскейл
CANVAS = 136        # итоговый холст (под формат листов игры)

# ===== Палитры тёмного фэнтези (по типам врагов) =====

def _pal(skin, cloth, pants, eye, blood=(102, 28, 28)):
    def shade(c, k):
        return tuple(max(0, min(255, int(v * k))) for v in c)
    return {
        'skin': skin, 'skin_d': shade(skin, 0.72), 'skin_l': shade(skin, 1.25),
        'cloth': cloth, 'cloth_d': shade(cloth, 0.7),
        'pants': pants, 'pants_d': shade(pants, 0.72),
        'eye': eye, 'blood': blood, 'out': (22, 18, 20),
    }


PALETTES = {
    'normal': _pal((106, 140, 92), (78, 62, 50), (56, 52, 62), (196, 255, 150)),
    'fast':   _pal((150, 158, 96), (96, 78, 40), (70, 60, 46), (255, 240, 130)),
    'tank':   _pal((110, 116, 122), (60, 64, 76), (44, 46, 54), (255, 120, 90)),
    'night':  _pal((88, 74, 122), (44, 38, 66), (34, 30, 50), (235, 235, 255)),
    'flying': _pal((132, 108, 138), (70, 50, 74), (52, 40, 58), (255, 190, 240)),
    'boss':   _pal((132, 68, 58), (58, 40, 40), (44, 32, 34), (255, 80, 60)),
}

# Модификаторы размера и крылья
SIZE_MOD = {'normal': 1.0, 'fast': 0.88, 'tank': 1.28, 'night': 1.0,
            'flying': 0.92, 'boss': 1.6}
HAS_WINGS = {'flying'}


def px(g, x, y, c):
    if 0 <= x < GW and 0 <= y < GH:
        g[y][x] = c


def rect(g, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px(g, x, y, c)


def outline(g, out_color):
    """Однопиксельный контур вокруг непустых пикселей."""
    marks = []
    for y in range(GH):
        for x in range(GW):
            if g[y][x] is None:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < GW and 0 <= ny < GH and g[ny][nx] is not None and g[ny][nx] != out_color:
                        marks.append((x, y))
                        break
    for x, y in marks:
        g[y][x] = out_color


def _legs(g, P, frame, cx):
    """Ноги для фронтальных ракурсов: шаг = ноги расходятся."""
    spread = [0, 1, 0, 1][frame]
    bob = [0, -1, 0, -1][frame]
    ly = 21 + bob
    # левая нога
    rect(g, cx - 4 - spread, ly, cx - 1, 29, P['pants'])
    rect(g, cx - 4 - spread, 26, cx - 1, 29, P['pants_d'])
    rect(g, cx - 5 - spread, 30, cx - 1, 31, P['out'])      # ботинок
    # правая нога
    rect(g, cx + 1, ly, cx + 4 + spread, 29, P['pants'])
    rect(g, cx + 1, ly, cx + 4 + spread, 24, P['pants_d'])
    rect(g, cx + 1, 30, cx + 5 + spread, 31, P['out'])
    return bob


def _wings(g, P, frame, cx, bob, side_view=False):
    """Рваные крылья за спиной (для летающего типа)."""
    flap = [0, -2, 0, 2][frame]
    wing = P['pants_d']
    edge = P['skin_d']
    if side_view:
        # одно крыло видно за торсом, машет вверх-вниз
        for i in range(6):
            y = 6 + bob + flap + i
            rect(g, cx - 9 + i, y, cx - 4, y, wing)
        rect(g, cx - 9, 6 + bob + flap, cx - 8, 7 + bob + flap, edge)
    else:
        for i in range(6):
            y = 7 + bob + flap + i
            rect(g, cx - 13 + i, y, cx - 7, y, wing)
            rect(g, cx + 7, y, cx + 13 - i, y, wing)
        rect(g, cx - 13, 7 + bob + flap, cx - 12, 8 + bob + flap, edge)
        rect(g, cx + 12, 7 + bob + flap, cx + 13, 8 + bob + flap, edge)


def draw_front(P, frame, wings=False):
    g = [[None] * GW for _ in range(GH)]
    cx = GW // 2
    bob = [0, -1, 0, -1][frame]
    if wings:
        _wings(g, P, frame, cx, bob)
    bob = _legs(g, P, frame, cx)

    # Торс (рваная рубаха)
    rect(g, cx - 6, 11 + bob, cx + 6, 20 + bob, P['cloth'])
    rect(g, cx - 6, 17 + bob, cx + 6, 20 + bob, P['cloth_d'])
    rect(g, cx + 3, 12 + bob, cx + 5, 14 + bob, P['skin_d'])   # дыра до кожи
    rect(g, cx - 4, 16 + bob, cx - 2, 17 + bob, P['blood'])    # кровь

    # Руки: одна свисает, вторая полусогнута вперёд
    swing = [0, 1, 0, -1][frame]
    rect(g, cx - 9, 11 + bob, cx - 7, 18 + bob + swing, P['cloth_d'])
    rect(g, cx - 9, 17 + bob + swing, cx - 7, 19 + bob + swing, P['skin'])
    rect(g, cx + 7, 11 + bob, cx + 9, 15 + bob - swing, P['cloth_d'])
    rect(g, cx + 7, 14 + bob - swing, cx + 9, 16 + bob - swing, P['skin'])

    # Шея и голова
    rect(g, cx - 2, 10 + bob, cx + 2, 10 + bob, P['skin_d'])
    rect(g, cx - 5, 2 + bob, cx + 5, 9 + bob, P['skin'])
    rect(g, cx + 3, 2 + bob, cx + 5, 9 + bob, P['skin_d'])      # тень справа
    rect(g, cx - 5, 2 + bob, cx - 4, 3 + bob, P['skin_d'])      # гнилая макушка
    # Глаза: провалы со светящейся точкой
    rect(g, cx - 4, 5 + bob, cx - 2, 6 + bob, P['out'])
    rect(g, cx + 2, 5 + bob, cx + 4, 6 + bob, P['out'])
    px(g, cx - 3, 5 + bob, P['eye'])
    px(g, cx + 3, 5 + bob, P['eye'])
    # Рот: рваная челюсть
    rect(g, cx - 2, 8 + bob, cx + 2, 8 + bob, P['out'])
    px(g, cx - 1, 8 + bob, P['blood'])

    outline(g, P['out'])
    return g


def draw_back(P, frame, wings=False):
    g = [[None] * GW for _ in range(GH)]
    cx = GW // 2
    bob = [0, -1, 0, -1][frame]
    if wings:
        _wings(g, P, frame, cx, bob)
    bob = _legs(g, P, frame, cx)

    # Торс со спины
    rect(g, cx - 6, 11 + bob, cx + 6, 20 + bob, P['cloth'])
    rect(g, cx - 6, 11 + bob, cx + 6, 13 + bob, P['cloth_d'])
    rect(g, cx - 1, 14 + bob, cx + 2, 18 + bob, P['cloth_d'])   # рваная спина
    rect(g, cx, 15 + bob, cx + 1, 17 + bob, P['skin_d'])        # позвоночник

    # Руки
    swing = [0, 1, 0, -1][frame]
    rect(g, cx - 9, 11 + bob, cx - 7, 18 + bob + swing, P['cloth_d'])
    rect(g, cx - 9, 17 + bob + swing, cx - 7, 19 + bob + swing, P['skin'])
    rect(g, cx + 7, 11 + bob, cx + 9, 18 + bob - swing, P['cloth_d'])
    rect(g, cx + 7, 17 + bob - swing, cx + 9, 19 + bob - swing, P['skin'])

    # Затылок: без лица, гнилые пятна
    rect(g, cx - 2, 10 + bob, cx + 2, 10 + bob, P['skin_d'])
    rect(g, cx - 5, 2 + bob, cx + 5, 9 + bob, P['skin'])
    rect(g, cx - 5, 2 + bob, cx - 3, 9 + bob, P['skin_d'])
    rect(g, cx + 1, 3 + bob, cx + 3, 5 + bob, P['skin_d'])
    rect(g, cx - 1, 6 + bob, cx, 7 + bob, P['blood'])           # рана на затылке

    outline(g, P['out'])
    return g


def draw_side(P, frame, wings=False):
    """Профиль, смотрит ВПРАВО: руки вытянуты вперёд, шаркает."""
    g = [[None] * GW for _ in range(GH)]
    cx = GW // 2 - 2
    bob = [0, -1, 0, -1][frame]
    stride = [2, 0, -2, 0][frame]
    if wings:
        _wings(g, P, frame, cx, bob, side_view=True)

    # Ноги: шаг вперёд/назад
    front_x = cx + 1 + stride
    back_x = cx - 2 - stride
    rect(g, front_x, 21 + bob, front_x + 2, 29, P['pants'])
    rect(g, front_x, 30, front_x + 3, 31, P['out'])
    rect(g, back_x, 21 + bob, back_x + 2, 29, P['pants_d'])
    rect(g, back_x - 1, 30, back_x + 2, 31, P['out'])

    # Торс (узкий, наклонён вперёд)
    rect(g, cx - 3, 11 + bob, cx + 3, 20 + bob, P['cloth'])
    rect(g, cx - 3, 17 + bob, cx + 3, 20 + bob, P['cloth_d'])
    rect(g, cx + 1, 12 + bob, cx + 3, 13 + bob, P['skin_d'])

    # Обе руки вытянуты вперёд (вправо)
    arm_wob = [0, 1, 0, -1][frame]
    rect(g, cx + 3, 12 + bob, cx + 10, 13 + bob, P['cloth_d'])
    rect(g, cx + 10, 12 + bob, cx + 11, 13 + bob, P['skin'])
    rect(g, cx + 2, 15 + bob + arm_wob, cx + 8, 16 + bob + arm_wob, P['cloth'])
    rect(g, cx + 8, 15 + bob + arm_wob, cx + 9, 16 + bob + arm_wob, P['skin'])

    # Голова в профиль (наклонена вперёд)
    hx = cx + 1
    rect(g, hx - 4, 2 + bob, hx + 4, 9 + bob, P['skin'])
    rect(g, hx - 4, 2 + bob, hx - 2, 9 + bob, P['skin_d'])      # затылок в тени
    rect(g, hx + 4, 6 + bob, hx + 5, 7 + bob, P['skin'])        # нос
    rect(g, hx + 1, 5 + bob, hx + 2, 6 + bob, P['out'])         # глазница
    px(g, hx + 2, 5 + bob, P['eye'])
    rect(g, hx + 2, 8 + bob, hx + 4, 8 + bob, P['out'])         # рот
    rect(g, hx - 2, 10 + bob, hx + 1, 10 + bob, P['skin_d'])    # шея

    outline(g, P['out'])
    return g


# ============================================================
# ЛЕТУЧАЯ МЫШЬ (flying): компактное тело + огромные перепончатые крылья
# ============================================================

def _bat_wing_pts(span, fold):
    """Контур перепончатого крыла: список (dx, y_top, y_bot) от тела наружу.

    span — размах в пикселях, fold — насколько крыло поднято/опущено (кадр).
    Перепонка провисает между "пальцами" — нижняя кромка волнистая.
    """
    pts = []
    for i in range(span):
        t = i / max(1, span - 1)
        y_top = fold * t * t * 6                     # кромка уходит вверх/вниз
        sag = [0, 1, 0, 2, 0, 1][int(t * 5.99) % 6]  # провис между пальцами
        y_bot = y_top + 4 + int(3 * (1 - t)) + sag
        pts.append((i, int(round(y_top)), int(round(y_bot))))
    return pts


def _bat_wings(g, P, frame, cx, cy, side_view=False):
    """Большие машущие крылья. frame задаёт фазу взмаха."""
    wing = P['cloth_d']
    membrane = P['cloth']
    bone = P['skin_l']
    fold = [-1.0, -0.4, 0.6, -0.4][frame]  # взмах: вверх -> вниз
    span = 10 if side_view else 9
    for dx, y_top, y_bot in _bat_wing_pts(span, fold):
        # левое крыло
        for y in range(y_top, y_bot + 1):
            px(g, cx - 4 - dx, cy + y, membrane if y > y_top else wing)
        # правое крыло
        if not side_view:
            for y in range(y_top, y_bot + 1):
                px(g, cx + 4 + dx, cy + y, membrane if y > y_top else wing)
    # Косточки-"пальцы" по верхней кромке
    for fx in (3, 6, span - 1):
        _, y_top, _ = _bat_wing_pts(span, fold)[fx]
        px(g, cx - 4 - fx, cy + y_top, bone)
        if not side_view:
            px(g, cx + 4 + fx, cy + y_top, bone)
    # Коготок на сгибе крыла
    _, tip_top, _ = _bat_wing_pts(span, fold)[span - 1]
    px(g, cx - 4 - span, cy + tip_top - 1, bone)
    if not side_view:
        px(g, cx + 4 + span, cy + tip_top - 1, bone)


def draw_bat_front(P, frame):
    """Летучая мышь спереди: тельце, огромные крылья, уши, лапки поджаты."""
    g = [[None] * GW for _ in range(GH)]
    cx = GW // 2
    bob = [0, -1, 0, 1][frame]
    cy = 12 + bob
    _bat_wings(g, P, frame, cx, cy)
    # Тельце (компактное, пушистое)
    rect(g, cx - 3, cy - 1, cx + 3, cy + 8, P['skin'])
    rect(g, cx - 3, cy + 5, cx + 3, cy + 8, P['skin_d'])
    px(g, cx - 2, cy + 1, P['skin_l'])  # блик груди
    # Поджатые лапки
    px(g, cx - 2, cy + 9, P['skin_d'])
    px(g, cx + 2, cy + 9, P['skin_d'])
    # Голова
    rect(g, cx - 3, cy - 6, cx + 3, cy - 1, P['skin'])
    # Уши — большие треугольные
    px(g, cx - 3, cy - 8, P['skin'])
    px(g, cx - 3, cy - 7, P['skin'])
    px(g, cx - 4, cy - 9, P['skin_d'])
    px(g, cx + 3, cy - 8, P['skin'])
    px(g, cx + 3, cy - 7, P['skin'])
    px(g, cx + 4, cy - 9, P['skin_d'])
    # Морда: глаза-огоньки, нос, клыки
    px(g, cx - 2, cy - 4, P['eye'])
    px(g, cx + 2, cy - 4, P['eye'])
    px(g, cx, cy - 3, P['out'])          # нос
    px(g, cx - 1, cy - 2, (235, 235, 235))  # клыки
    px(g, cx + 1, cy - 2, (235, 235, 235))
    outline(g, P['out'])
    return g


def draw_bat_back(P, frame):
    """Летучая мышь со спины: то же, но без морды, видна спинка."""
    g = [[None] * GW for _ in range(GH)]
    cx = GW // 2
    bob = [0, -1, 0, 1][frame]
    cy = 12 + bob
    _bat_wings(g, P, frame, cx, cy)
    # Тельце со спины
    rect(g, cx - 3, cy - 1, cx + 3, cy + 8, P['skin_d'])
    rect(g, cx - 1, cy, cx + 1, cy + 7, P['skin'])  # хребет
    px(g, cx - 2, cy + 9, P['skin_d'])
    px(g, cx + 2, cy + 9, P['skin_d'])
    # Затылок и уши
    rect(g, cx - 3, cy - 6, cx + 3, cy - 1, P['skin_d'])
    px(g, cx - 3, cy - 8, P['skin_d'])
    px(g, cx - 3, cy - 7, P['skin_d'])
    px(g, cx + 3, cy - 8, P['skin_d'])
    px(g, cx + 3, cy - 7, P['skin_d'])
    outline(g, P['out'])
    return g


def draw_bat_side(P, frame):
    """Летучая мышь в профиль (летит вправо): вытянутая морда, одно крыло."""
    g = [[None] * GW for _ in range(GH)]
    cx = GW // 2
    bob = [0, -1, 0, 1][frame]
    cy = 12 + bob
    fold = [-1.0, -0.4, 0.6, -0.4][frame]
    wing = P['cloth_d']
    membrane = P['cloth']
    # Одно крыло над телом, машет размашисто
    span = 11
    for dx, y_top, y_bot in _bat_wing_pts(span, fold):
        for y in range(y_top, y_bot + 1):
            px(g, cx + 3 - dx, cy - 3 + y, membrane if y > y_top else wing)
    px(g, cx + 3 - span, cy - 4 + int(fold * 6), P['skin_l'])  # коготь
    # Тельце горизонтально (летит)
    rect(g, cx - 4, cy + 2, cx + 4, cy + 6, P['skin'])
    rect(g, cx - 4, cy + 5, cx + 4, cy + 6, P['skin_d'])
    # Голова впереди (справа)
    rect(g, cx + 4, cy, cx + 8, cy + 5, P['skin'])
    px(g, cx + 9, cy + 3, P['skin_d'])   # вытянутая мордочка
    px(g, cx + 7, cy + 2, P['eye'])      # глаз
    px(g, cx + 8, cy + 5, (235, 235, 235))  # клык
    # Ухо
    px(g, cx + 5, cy - 2, P['skin'])
    px(g, cx + 5, cy - 1, P['skin'])
    px(g, cx + 4, cy - 3, P['skin_d'])
    # Хвостовая перепонка
    px(g, cx - 5, cy + 4, P['cloth_d'])
    px(g, cx - 6, cy + 3, P['cloth_d'])
    outline(g, P['out'])
    return g


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


def mirror(img: Image.Image) -> Image.Image:
    return img.transpose(Image.FLIP_LEFT_RIGHT)


def _apply_size(img: Image.Image, mod: float) -> Image.Image:
    if mod == 1.0:
        return img
    new = int(CANVAS * mod)
    scaled = img.resize((new, new), Image.NEAREST)
    canvas = Image.new('RGBA', (new, new), (0, 0, 0, 0))
    canvas.paste(scaled, (0, 0), scaled)
    return canvas


def generate(variant='normal', out_dir=None):
    P = PALETTES[variant]
    wings = variant in HAS_WINGS
    mod = SIZE_MOD.get(variant, 1.0)
    out_dir = out_dir or f"assets/sprites/pzombie_{variant}"
    os.makedirs(out_dir, exist_ok=True)
    for i in range(4):
        if wings:
            # Летучая мышь: собственные функции рисования
            front, back, side = draw_bat_front(P, i), draw_bat_back(P, i), draw_bat_side(P, i)
        else:
            front, back, side = draw_front(P, i), draw_back(P, i), draw_side(P, i)
        _apply_size(grid_to_image(front), mod).save(f"{out_dir}/down_{i}.png")
        _apply_size(grid_to_image(back), mod).save(f"{out_dir}/up_{i}.png")
        right = _apply_size(grid_to_image(side), mod)
        right.save(f"{out_dir}/right_{i}.png")
        mirror(right).save(f"{out_dir}/left_{i}.png")
    print(f"OK {out_dir}")


if __name__ == '__main__':
    for v in PALETTES:
        generate(v)
