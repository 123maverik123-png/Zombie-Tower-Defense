# tools/gen_zombie_pixel.py
"""Процедурный пиксель-арт зомби: 4 диагональных (изометрических) слота x 4 кадра ходьбы.

Мир рисуется в изометрии (core/iso.py): движение вдоль мировых осей на
экране выглядит как диагональ, поэтому вместо кардинальных поз (анфас/спина/
профиль) рисуются 2 диагональные позы, каждая зеркалится под противоположный
крен:
  right = draw_diag_toward         (к камере, SE, лицо видно в 3/4)
  down  = mirror(draw_diag_toward) (к камере, SW)
  up    = draw_diag_away           (от камеры, NE, спина видна в 3/4)
  left  = mirror(draw_diag_away)   (от камеры, NW)

Рисуем на логической сетке 26x34, масштабируем x4 (NEAREST) для чёткого пикселя.
Запуск: python tools/gen_zombie_pixel.py
"""
import os
from PIL import Image

GW, GH = 26, 34     # логическая сетка
SCALE = 4           # апскейл
CANVAS = 136        # итоговый холст (под формат листов игры)
DIAG_ROTATE_DEG = 14  # финальный лёгкий поворот поверх изо-пропорций/шва (см. generate())

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


def _lighten(c, k=1.3):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def _seam_block(g, y0, y1, x0, x1, seam0, seam_step, front_c, side_c):
    """Двугранный блок (торс/голова в 3/4): передняя и боковая грань разделены
    ДИАГОНАЛЬНЫМ швом (не плоской вертикальной линией) — шов = seam0 +
    seam_step*(y-y0). Это ключевая деталь, которая продаёт "разворот корпуса
    в 3/4" (как в изометрических RPG), а не плоский анфас с тенью сбоку.
    """
    for y in range(y0, y1 + 1):
        seam = int(round(seam0 + seam_step * (y - y0)))
        seam = max(x0 - 1, min(x1, seam))
        if seam >= x0:
            rect(g, x0, y, seam, y, front_c)
        if seam + 1 <= x1:
            rect(g, seam + 1, y, x1, y, side_c)


def draw_diag_toward(P, frame, wings=False):
    """Изометрическая диагональ К камере (SE): вид сверху-сбоку.

    Приземистые пропорции (торс/ноги компрессированы по высоте — камера
    смотрит сверху вниз, а не в упор), широкая диагональная стойка ног
    (ближняя к камере нога — крупнее и дальше от центра, дальняя — уже),
    блики на "верхних" поверхностях (макушка, плечи, ботинки) продают
    угол обзора сверху. Лицо видно в 3/4 (ближняя сторона крупнее).
    """
    g = [[None] * GW for _ in range(GH)]
    cx = GW // 2
    bob = [0, -1, 0, -1][frame]
    cloth_l = _lighten(P['cloth'])
    if wings:
        _wings(g, P, frame, cx, bob, side_view=True)

    # Ноги: широкая диагональная стойка, компрессированы по высоте (18..25),
    # ближняя (левая) нога крупнее/дальше от центра, дальняя (правая) уже.
    spread = [0, 1, 0, 1][frame]
    ly = 18 + bob
    rect(g, cx - 7 - spread, ly, cx - 2, 25, P['pants'])
    rect(g, cx - 7 - spread, 23, cx - 2, 25, P['pants_d'])
    rect(g, cx - 8 - spread, 26, cx - 2, 27, P['out'])
    rect(g, cx - 8 - spread, 26, cx - 2, 26, P['pants_d'])      # блик верха ближнего ботинка
    rect(g, cx + 2, ly, cx + 4 + spread, 24, P['pants_d'])
    rect(g, cx + 2, 26, cx + 5 + spread, 27, P['out'])          # дальний ботинок (уже)

    # Торс (рваная рубаха): передняя грань (cloth) + боковая грань (cloth_d)
    # разделены ДИАГОНАЛЬНЫМ швом — корпус развёрнут в 3/4, не анфас.
    _seam_block(g, 11 + bob, 17 + bob, cx - 6, cx + 5, cx - 2, 0.5, P['cloth'], P['cloth_d'])
    rect(g, cx - 6, 11 + bob, cx + 5, 11 + bob, cloth_l)        # блик верха плеч
    rect(g, cx + 2, 12 + bob, cx + 4, 13 + bob, P['skin_d'])    # дыра до кожи
    rect(g, cx - 3, 14 + bob, cx - 1, 15 + bob, P['blood'])     # кровь

    # Руки: ближняя (левая) свисает крупно, дальняя (правая) короче/выше
    swing = [0, 1, 0, -1][frame]
    rect(g, cx - 9, 11 + bob, cx - 7, 17 + bob + swing, P['cloth_d'])
    rect(g, cx - 9, 15 + bob + swing, cx - 7, 18 + bob + swing, P['skin'])
    rect(g, cx + 5, 12 + bob, cx + 8, 15 + bob - swing, P['cloth_d'])
    rect(g, cx + 5, 14 + bob - swing, cx + 8, 16 + bob - swing, P['skin'])

    # Голова в 3/4: передняя грань лица (skin) + боковая грань щеки (skin_d)
    # разделены диагональным швом (тот же приём, что и в торсе).
    hx = cx
    rect(g, hx - 2, 10 + bob, hx + 2, 10 + bob, P['skin_d'])    # шея
    _seam_block(g, 3 + bob, 9 + bob, hx - 5, hx + 5, hx + 1, 0.45, P['skin'], P['skin_d'])
    rect(g, hx - 5, 2 + bob, hx + 5, 2 + bob, P['skin_l'])      # блик макушки сверху
    rect(g, hx - 3, 5 + bob, hx - 1, 6 + bob, P['out'])         # ближний глаз крупнее
    rect(g, hx + 2, 5 + bob, hx + 3, 6 + bob, P['out'])         # дальний глаз уже
    px(g, hx - 2, 5 + bob, P['eye'])
    px(g, hx + 2, 5 + bob, P['eye'])
    rect(g, hx - 2, 8 + bob, hx + 1, 8 + bob, P['out'])         # рот
    px(g, hx - 1, 8 + bob, P['blood'])

    outline(g, P['out'])
    return g


def draw_diag_away(P, frame, wings=False):
    """Изометрическая диагональ ОТ камеры (NE): вид сверху-сбоку, со спины.

    Та же приземистая геометрия и широкая диагональная стойка, что и в
    draw_diag_toward, но со спины (без лица, гнилые пятна на затылке).
    """
    g = [[None] * GW for _ in range(GH)]
    cx = GW // 2
    bob = [0, -1, 0, -1][frame]
    cloth_l = _lighten(P['cloth'])
    if wings:
        _wings(g, P, frame, cx, bob, side_view=True)

    # Ноги: та же диагональная стойка, что и в toward
    spread = [0, 1, 0, 1][frame]
    ly = 18 + bob
    rect(g, cx - 7 - spread, ly, cx - 2, 25, P['pants'])
    rect(g, cx - 7 - spread, 23, cx - 2, 25, P['pants_d'])
    rect(g, cx - 8 - spread, 26, cx - 2, 27, P['out'])
    rect(g, cx - 8 - spread, 26, cx - 2, 26, P['pants_d'])
    rect(g, cx + 2, ly, cx + 4 + spread, 24, P['pants_d'])
    rect(g, cx + 2, 26, cx + 5 + spread, 27, P['out'])

    # Торс со спины: та же диагональная развёртка граней, что и в toward
    # (кроме плеч — сзади обе грани одного тона тела, спина отличается пятном).
    _seam_block(g, 11 + bob, 17 + bob, cx - 6, cx + 5, cx - 2, 0.5, P['cloth'], P['cloth_d'])
    rect(g, cx - 6, 11 + bob, cx + 5, 11 + bob, cloth_l)        # блик верха плеч
    rect(g, cx - 1, 13 + bob, cx + 2, 16 + bob, P['cloth_d'])   # рваная спина
    rect(g, cx, 14 + bob, cx + 1, 16 + bob, P['skin_d'])        # позвоночник

    # Руки: ближняя (левая) крупнее, дальняя (правая) короче
    swing = [0, 1, 0, -1][frame]
    rect(g, cx - 9, 11 + bob, cx - 7, 17 + bob + swing, P['cloth_d'])
    rect(g, cx - 9, 15 + bob + swing, cx - 7, 18 + bob + swing, P['skin'])
    rect(g, cx + 5, 12 + bob, cx + 8, 18 + bob - swing, P['cloth_d'])
    rect(g, cx + 5, 16 + bob - swing, cx + 8, 19 + bob - swing, P['skin'])

    # Затылок в 3/4: та же диагональная развёртка граней (без лица)
    hx = cx
    rect(g, hx - 2, 10 + bob, hx + 2, 10 + bob, P['skin_d'])
    _seam_block(g, 3 + bob, 9 + bob, hx - 5, hx + 5, hx + 1, 0.45, P['skin'], P['skin_d'])
    rect(g, hx - 5, 2 + bob, hx + 5, 2 + bob, P['skin_l'])      # блик макушки сверху
    rect(g, hx + 1, 4 + bob, hx + 3, 6 + bob, P['skin_d'])      # доп. тень (гнилое пятно)
    rect(g, hx - 1, 6 + bob, hx, 7 + bob, P['blood'])           # рана на затылке

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


def _rotate(img: Image.Image, angle: float) -> Image.Image:
    """Лёгкий финальный поворот всего спрайта (поверх уже изометричного силуэта
    и диагонального шва граней) — усиливает читаемость направления."""
    return img.rotate(angle, resample=Image.NEAREST, expand=False)


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
            # Летучая мышь: собственные функции рисования (пока не диагональные)
            front, back, side = draw_bat_front(P, i), draw_bat_back(P, i), draw_bat_side(P, i)
            _apply_size(grid_to_image(front), mod).save(f"{out_dir}/down_{i}.png")
            _apply_size(grid_to_image(back), mod).save(f"{out_dir}/up_{i}.png")
            right = _apply_size(grid_to_image(side), mod)
            right.save(f"{out_dir}/right_{i}.png")
            mirror(right).save(f"{out_dir}/left_{i}.png")
        else:
            toward = _apply_size(_rotate(grid_to_image(draw_diag_toward(P, i)), -DIAG_ROTATE_DEG), mod)
            away = _apply_size(_rotate(grid_to_image(draw_diag_away(P, i)), -DIAG_ROTATE_DEG), mod)
            toward.save(f"{out_dir}/right_{i}.png")
            mirror(toward).save(f"{out_dir}/down_{i}.png")
            away.save(f"{out_dir}/up_{i}.png")
            mirror(away).save(f"{out_dir}/left_{i}.png")
    print(f"OK {out_dir}")


if __name__ == '__main__':
    for v in PALETTES:
        generate(v)
