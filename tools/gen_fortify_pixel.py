# tools/gen_fortify_pixel.py
"""Процедурные спрайты укреплений: ворота и стены (камень + железо).

Единый стиль с башнями (tools/gen_tower_pixel.py): та же палитра железа,
сетка 32×32, апскейл ×4. Спрайты занимают весь тайл (заполняют клетку),
чтобы стыковаться друг с другом без зазоров.

Ворота (2): gate_h, gate_v — деревянные створки поперёк прохода + жел. рама.
Стены (6): wall_h, wall_v (прямые), wall_tl/tr/bl/br (угловые) — каменная
кладка со сплошной «балкой» по оси. Балка стены и рама ворот лежат на одной
линии и одинаковой толщины → плавный переход стена↔ворота.

8 файлов -> assets/images/fortify/<name>.png
Запуск: python tools/gen_fortify_pixel.py
"""
import os
from PIL import Image

GW = GH = 32
SCALE = 4
CANVAS = 128

# ===== Палитра (общая с башнями) =====
IRON = (52, 55, 62)
IRON_D = (36, 38, 45)
IRON_L = (80, 85, 96)
RUST = (108, 62, 38)
RUST_D = (78, 45, 30)
HAZARD = (164, 136, 46)
WOOD = (96, 66, 40)
WOOD_L = (128, 90, 54)
WOOD_D = (68, 46, 28)
STONE = (120, 116, 110)
STONE_L = (150, 146, 138)
STONE_D = (84, 80, 76)
OUT = (16, 15, 18)

# Толщина осевой «балки» (общая для стен и рамы ворот) — залог стыковки
BEAM_HALF = 11   # балка [16-11 .. 16+11) = 22 px из 32 (~69% тайла)


def px(g, x, y, c):
    if 0 <= x < GW and 0 <= y < GH:
        g[y][x] = c


def rect(g, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px(g, x, y, c)


def outline(g):
    """Контур вокруг непустых пикселей, НО не по самим краям тайла.

    Крайние пиксели (x=0/GW-1, y=0/GH-1) — линия стыковки с соседним
    тайлом; чёрный контур там даёт видимые полосы между стенами.
    """
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
        if x == 0 or x == GW - 1 or y == 0 or y == GH - 1:
            continue  # не обводим кромку тайла — там стык
        g[y][x] = OUT


# ============================================================
# КАМЕННАЯ БАЛКА С ЖЕЛЕЗНОЙ РАМКОЙ (единый вид для стен)
# ============================================================

def _stone_fill(g, mask):
    """Каменная кладка: блоки со швами и объёмом (тень снизу/справа, блик
    сверху/слева). Выровнена по мировой сетке (модуль координат), поэтому
    у соседних тайлов кладка совпадает и не даёт «полос» на стыках.

    Блок 6×4 px, ряды сдвинуты в шахматном порядке — без диагоналей.
    """
    BW, BH = 6, 4
    for (x, y) in mask:
        row = y // BH
        # шахматный сдвиг рядов
        sx = (x + (BW // 2 if row % 2 else 0))
        in_col_seam = (sx % BW == 0)      # вертикальный шов между блоками
        in_row_seam = (y % BH == 0)       # горизонтальный шов между рядами
        on_edge = (x == 0 or x == GW - 1 or y == 0 or y == GH - 1)
        if on_edge:
            g[y][x] = STONE              # кромка тайла — ровный камень (стык)
        elif in_col_seam or in_row_seam:
            g[y][x] = STONE_D             # затенённый шов
        elif (sx % BW == 1) or (y % BH == 1):
            g[y][x] = STONE_L             # блик по верх-левой кромке камня
        else:
            g[y][x] = STONE


def _iron_frame(g, mask):
    """Железная рамка по внутренним кромкам балки — как рама створок ворот.

    Кромка = клетка балки, у которой есть сосед ВНУТРИ тайла, но ВНЕ балки.
    На краях тайла (сосед за границей 0..31) рамки нет — там камень торчит
    для бесшовной стыковки с соседней стеной/воротами.
    """
    mset = mask
    edge1 = set()
    for (x, y) in mset:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < GW and 0 <= ny < GH and (nx, ny) not in mset:
                edge1.add((x, y))
                break
    # второй слой рамки внутрь — толщина 2px и объём
    edge2 = set()
    for (x, y) in mset:
        if (x, y) in edge1:
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) in edge1:
                edge2.add((x, y))
                break
    for (x, y) in edge2:
        g[y][x] = IRON_D
    for (x, y) in edge1:
        g[y][x] = IRON
    # блик по верхней/левой кромке рамки (там, где снаружи балки)
    for (x, y) in edge1:
        if (x, y - 1) not in mset:
            g[y][x] = IRON_L


def _mask_straight(horizontal):
    lo, hi = 16 - BEAM_HALF, 16 + BEAM_HALF - 1
    if horizontal:
        return {(x, y) for x in range(GW) for y in range(lo, hi + 1)}
    return {(x, y) for x in range(lo, hi + 1) for y in range(GH)}


def _mask_corner(corner):
    """L-образная маска балки. corner: 'tl','tr','bl','br'."""
    lo, hi = 16 - BEAM_HALF, 16 + BEAM_HALF - 1
    hx = range(0, hi + 1) if corner in ('tl', 'bl') else range(lo, GW)   # плечо влево/вправо
    vy = range(0, hi + 1) if corner in ('tl', 'tr') else range(lo, GH)   # плечо вверх/вниз
    m = set()
    for x in hx:
        for y in range(lo, hi + 1):
            m.add((x, y))
    for y in vy:
        for x in range(lo, hi + 1):
            m.add((x, y))
    return m


def iron_band(g, x0, y0, x1, y1):
    """Железная окантовка (для рамы ворот)."""
    rect(g, x0, y0, x1, y1, IRON)
    rect(g, x0, y0, x1, y0, IRON_L)
    rect(g, x0, y1, x1, y1, IRON_D)
    for x in range(x0 + 1, x1, 5):
        px(g, x, y0 + 1, IRON_L)
        px(g, x, y1 - 1, IRON_L)


# ============================================================
# СТЕНЫ
# ============================================================

def wall_straight(g, horizontal=True):
    """Прямая стена: каменная балка с железной рамкой во всю клетку."""
    mask = _mask_straight(horizontal)
    _stone_fill(g, mask)
    _iron_frame(g, mask)


def wall_corner(g, corner):
    """Угловая стена: L-образная каменная балка с чистой железной рамкой.

    Рамка строится по контуру L (сосед-тест), поэтому пунктирных
    артефактов нет, а на торцах (края тайла) камень торчит для стыковки.
    """
    mask = _mask_corner(corner)
    _stone_fill(g, mask)
    _iron_frame(g, mask)


# ============================================================
# ВОРОТА
# ============================================================

def gate_oriented(g, horizontal=True):
    """Ворота: железная рама (как торцы стен) + деревянные створки внутри.

    Рама лежит на той же оси и ширине, что балка стены → стыкуется.
    Створки открываются поперёк прохода.
    """
    lo, hi = 16 - BEAM_HALF, 16 + BEAM_HALF - 1
    if horizontal:
        # проход вертикальный (враги идут вниз/вверх) — ворота поперёк, во всю ширину
        # железная рама сверху и снизу
        iron_band(g, 0, lo, GW - 1, lo + 2)
        iron_band(g, 0, hi - 2, GW - 1, hi)
        # деревянные створки (две половины, вертикальные доски)
        for x in range(2, GW - 2):
            shade = WOOD if (x // 3) % 2 == 0 else WOOD_L
            rect(g, x, lo + 3, x, hi - 3, shade)
        # шов посередине (створки смыкаются)
        rect(g, GW // 2 - 1, lo + 3, GW // 2, hi - 3, WOOD_D)
        # металлические поперечины
        rect(g, 3, 16 - 1, GW - 4, 16, IRON_D)
        # заклёпки-усиление
        for x in (5, GW - 6):
            px(g, x, lo + 4, HAZARD)
            px(g, x, hi - 4, HAZARD)
    else:
        # проход горизонтальный — ворота вертикальные
        iron_band_v(g, lo, 0, lo + 2, GH - 1)
        iron_band_v(g, hi - 2, 0, hi, GH - 1)
        for y in range(2, GH - 2):
            shade = WOOD if (y // 3) % 2 == 0 else WOOD_L
            rect(g, lo + 3, y, hi - 3, y, shade)
        rect(g, lo + 3, GH // 2 - 1, hi - 3, GH // 2, WOOD_D)
        rect(g, 16 - 1, 3, 16, GH - 4, IRON_D)
        for y in (5, GH - 6):
            px(g, lo + 4, y, HAZARD)
            px(g, hi - 4, y, HAZARD)


def iron_band_v(g, x0, y0, x1, y1):
    """Вертикальная железная окантовка."""
    rect(g, x0, y0, x1, y1, IRON)
    rect(g, x0, y0, x0, y1, IRON_L)
    rect(g, x1, y0, x1, y1, IRON_D)
    for y in range(y0 + 1, y1, 5):
        px(g, x0 + 1, y, IRON_L)


# ============================================================
# ГЕНЕРАЦИЯ
# ============================================================

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


SPRITES = {
    'gate_h': lambda g: gate_oriented(g, horizontal=True),
    'gate_v': lambda g: gate_oriented(g, horizontal=False),
    'wall_h': lambda g: wall_straight(g, horizontal=True),
    'wall_v': lambda g: wall_straight(g, horizontal=False),
    'wall_tl': lambda g: wall_corner(g, 'tl'),
    'wall_tr': lambda g: wall_corner(g, 'tr'),
    'wall_bl': lambda g: wall_corner(g, 'bl'),
    'wall_br': lambda g: wall_corner(g, 'br'),
}


def generate():
    out_dir = "assets/images/fortify"
    os.makedirs(out_dir, exist_ok=True)
    for name, fn in SPRITES.items():
        g = [[None] * GW for _ in range(GH)]
        fn(g)
        outline(g)
        grid_to_image(g).save(f"{out_dir}/{name}.png")
    print(f"OK fortify: {', '.join(SPRITES)}")


if __name__ == '__main__':
    generate()
