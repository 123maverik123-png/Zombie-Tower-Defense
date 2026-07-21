# tools/gen_kenney_assets.py
"""Генерирует игровые ассеты из исходников Kenney (assets/kenney_src/).

Создаёт:
  assets/images/tiles/{forest,desert,city}/  — 10 тайлов на биом
  assets/images/decorations/{биом}/          — декорации
  assets/sprites/kzombie_*/                  — 4-направленные листы зомби
  assets/images/towers_kenney/{id}/          — башни (4 уровня)

Запуск: python tools/gen_kenney_assets.py  (из корня проекта)
Исходники: CC0 1.0, kenney.nl
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance

SRC_TILES = "assets/kenney_src/tiles"
SRC_ZOMBIE = "assets/kenney_src/zombie"
T = 128  # рабочий размер тайла


def load_tile(n: int) -> Image.Image:
    return Image.open(f"{SRC_TILES}/towerDefense_tile{n:03d}.png").convert("RGBA").resize((T, T))


def load_clean(n: int) -> Image.Image:
    """Тайл без угловых артефактов: берём центр 50% и растягиваем.

    У многих тайлов пака в углах лежат кромки соседних текстур —
    центральная часть всегда чистая.
    """
    img = load_tile(n)
    q = T // 4
    return img.crop((q, q, T - q, T - q)).resize((T, T), Image.LANCZOS)


def tint(img: Image.Image, mul: tuple) -> Image.Image:
    """Покомпонентное умножение цвета (простая перекраска)."""
    r, g, b, a = img.split()
    r = r.point(lambda v: min(255, int(v * mul[0])))
    g = g.point(lambda v: min(255, int(v * mul[1])))
    b = b.point(lambda v: min(255, int(v * mul[2])))
    return Image.merge("RGBA", (r, g, b, a))


# ============================================================
# ТАЙЛЫ БИОМОВ
# ============================================================

BIOMES = {
    # Тёмное фэнтези: приглушённые холодные тона (под заставку меню).
    # base/road — номера тайлов Kenney, *_mul — перекраска (R,G,B множители)
    'forest': {'base': 24, 'road': 50, 'base_mul': (0.38, 0.52, 0.40),
               'road_mul': (0.55, 0.48, 0.42)},
    'desert': {'base': 98, 'road': 51, 'base_mul': (0.72, 0.58, 0.42),
               'road_mul': (0.52, 0.42, 0.34)},
    'city':   {'base': 148, 'road': 253, 'base_mul': (0.42, 0.42, 0.50),
               'road_mul': (0.50, 0.50, 0.58)},
}

# Здание замка и цвет портала на биом
CASTLE_SPRITE = {'forest': 269, 'desert': 268, 'city': 269}


def edge_shadow(road: Image.Image, horizontal: bool) -> Image.Image:
    """Едва заметная тень вдоль краёв дороги, добавляет объём."""
    d = ImageDraw.Draw(road, 'RGBA')
    if horizontal:
        d.rectangle((0, 0, T, 3), fill=(0, 0, 0, 18))
        d.rectangle((0, T - 4, T, T), fill=(0, 0, 0, 18))
    else:
        d.rectangle((0, 0, 3, T), fill=(0, 0, 0, 18))
        d.rectangle((T - 4, 0, T, T), fill=(0, 0, 0, 18))
    return road


def corner_tile(base: Image.Image, road: Image.Image, corner: str) -> Image.Image:
    """Полнотайловая дорога с закруглённым внешним углом.

    corner — угол, где остаётся ЗЕМЛЯ: 'tl'|'tr'|'bl'|'br'.
    """
    out = road.copy()
    mask = Image.new("L", (T, T), 0)
    d = ImageDraw.Draw(mask)
    R = 116  # радиус внешнего закругления
    centers = {
        'tl': (0, 0), 'tr': (T, 0), 'bl': (0, T), 'br': (T, T),
    }
    cx, cy = centers[corner]
    # Всё, что дальше R от противоположного угла — земля
    opp = (T - cx, T - cy)
    d.rectangle((0, 0, T, T), fill=255)
    d.ellipse((opp[0] - R, opp[1] - R, opp[0] + R, opp[1] + R), fill=0)
    out.paste(base, (0, 0), mask)
    # Тень по границе дуги
    ring = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    dr = ImageDraw.Draw(ring)
    dr.ellipse((opp[0] - R, opp[1] - R, opp[0] + R, opp[1] + R), outline=(0, 0, 0, 30), width=5)
    out = Image.alpha_composite(out, ring)
    return out


def make_portal(road: Image.Image) -> Image.Image:
    """Красно-фиолетовый портал: тёмное жерло, светящееся кольцо, вихрь."""
    out = road.copy()
    # Слой свечения (аддитивно накладываем)
    glow = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    dg = ImageDraw.Draw(glow)
    cx = cy = T // 2
    # Внешнее фиолетовое сияние -> к центру ярко-розовое -> тёмное жерло
    rings = [
        (52, (70, 20, 90, 70)),     # тусклый фиолетовый ореол
        (44, (120, 30, 140, 150)),  # фиолет
        (37, (180, 40, 130, 220)),  # пурпур
        (30, (230, 60, 90, 255)),   # красно-розовое кольцо
        (23, (255, 110, 140, 255)), # яркая кромка
        (18, (90, 20, 70, 255)),    # переход к жерлу
        (12, (40, 10, 50, 255)),    # тёмное жерло
        (6,  (15, 5, 25, 255)),     # чёрная сердцевина
    ]
    for r, col in rings:
        dg.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)
    # Вихревые блики-искры по кольцу
    import math
    for i in range(10):
        a = i * (2 * math.pi / 10)
        rr = 27 + (3 if i % 2 else -2)
        x = cx + int(rr * math.cos(a))
        y = cy + int(rr * math.sin(a))
        dg.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(255, 180, 210, 255))
    out = Image.alpha_composite(out, glow)
    return out


def _crystal(size: int) -> Image.Image:
    """Бело-лазурно-голубой кристалл (самоцвет-октаэдр) с гранями и бликом."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = size // 2
    top = int(size * 0.10)
    bot = int(size * 0.94)
    midy = int(size * 0.46)
    half = int(size * 0.30)
    outl = (18, 40, 70, 255)
    # Основные грани октаэдра
    LAZ = (90, 175, 235)      # лазурный
    LAZ_D = (52, 120, 190)    # тень грани
    LAZ_L = (170, 225, 250)   # светлая грань
    WHITE = (235, 250, 255)   # блик
    # Левая (тёмная) и правая (светлая) верхние грани
    d.polygon([(cx, top), (cx - half, midy), (cx, midy)], fill=LAZ_D)
    d.polygon([(cx, top), (cx + half, midy), (cx, midy)], fill=LAZ_L)
    # Нижние грани
    d.polygon([(cx - half, midy), (cx, bot), (cx, midy)], fill=(70, 145, 210))
    d.polygon([(cx + half, midy), (cx, bot), (cx, midy)], fill=LAZ)
    # Контур
    d.line([(cx, top), (cx - half, midy), (cx, bot), (cx + half, midy), (cx, top)],
           fill=outl, width=2)
    d.line([(cx, top), (cx, bot)], fill=(120, 190, 235, 180), width=1)
    d.line([(cx - half, midy), (cx + half, midy)], fill=(120, 190, 235, 180), width=1)
    # Белый блик на правой верхней грани
    d.polygon([(cx + 3, top + 4), (cx + half - 6, midy - 3), (cx + 3, midy - 3)],
              fill=WHITE)
    return img


def make_castle(base: Image.Image, biome: str) -> Image.Image:
    """Конечная точка пути — кристалл, который защищаем (бело-лазурный)."""
    out = base.copy()
    # Свечение-ореол под/вокруг кристалла
    glow = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    dg = ImageDraw.Draw(glow)
    cx = cy = T // 2
    for r, col in ((50, (120, 200, 240, 40)), (40, (150, 220, 250, 60)),
                   (30, (200, 240, 255, 80))):
        dg.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)
    # Тень-подставка
    dg.ellipse((34, 92, 94, 116), fill=(20, 40, 70, 90))
    out = Image.alpha_composite(out, glow)
    # Сам кристалл по центру, чуть приподнят
    cr = _crystal(96)
    out.paste(cr, (T // 2 - 48, T // 2 - 54), cr)
    return out


def gen_biome_tiles():
    for biome, cfg in BIOMES.items():
        out_dir = f"assets/images/tiles/{biome}"
        os.makedirs(out_dir, exist_ok=True)
        # У desert/city базовые тайлы имеют кромки в углах — чистим кропом
        if biome == 'forest':
            base = load_tile(cfg['base'])
        else:
            base = load_clean(cfg['base'])
        base = tint(base, cfg['base_mul'])
        road = tint(load_clean(cfg['road']), cfg['road_mul'])

        tiles = {
            'tile_grass': base,
            'tile_road_straight_h': edge_shadow(road.copy(), True),
            'tile_road_straight_v': edge_shadow(road.copy(), False),
            'tile_road_cross': road.copy(),
            # имена углов в игре: tr = соединяет верх и право → земля в bl
            'tile_road_turn_top_right': corner_tile(base, road, 'bl'),
            'tile_road_turn_top_left': corner_tile(base, road, 'br'),
            'tile_road_turn_bottom_right': corner_tile(base, road, 'tl'),
            'tile_road_turn_bottom_left': corner_tile(base, road, 'tr'),
            'tile_portal': make_portal(road),
            'tile_castle': make_castle(base, biome),
        }
        for name, img in tiles.items():
            img.save(f"{out_dir}/{name}.png")
        print(f"✅ tiles/{biome}: {len(tiles)}")


# ============================================================
# ДЕКОРАЦИИ
# ============================================================

DECOR = {
    'forest': {'tree': (130, 1.35), 'bush': (131, 0.75), 'bush_small': (132, 0.45),
               'rock': (135, 0.55), 'plant': (132, 0.55)},
    'desert': {'cactus': (134, 0.8), 'cactus_small': (132, 0.6), 'rock': (136, 0.6),
               'rock_small': (137, 0.45), 'crater': (20, 0.9)},
    'city':   {'building_a': (227, 1.3), 'building_b': (228, 1.3), 'building_c': (229, 1.3),
               'building_d': (269, 1.25), 'crate': (267, 0.5)},
}


# Затемнение декораций под тёмное фэнтези (в тон base_mul биома)
DECOR_MUL = {
    'forest': (0.45, 0.60, 0.50),
    'desert': (0.72, 0.60, 0.46),
    'city':   (0.52, 0.52, 0.60),
}


def gen_decorations():
    for biome, items in DECOR.items():
        out_dir = f"assets/images/decorations/{biome}"
        os.makedirs(out_dir, exist_ok=True)
        for name, (n, scale) in items.items():
            img = tint(load_tile(n), DECOR_MUL[biome])
            img.save(f"{out_dir}/{name}.png")
        print(f"✅ decorations/{biome}: {len(items)}")


# ============================================================
# ЗОМБИ (4 направления x 4 кадра, перекраска по типам)
# ============================================================

ZOMBIE_VARIANTS = {
    'kzombie_normal': {'mul': (1.0, 1.0, 1.0), 'scale': 1.0},
    'kzombie_fast':   {'mul': (1.2, 1.1, 0.55), 'scale': 0.9},
    'kzombie_tank':   {'mul': (0.72, 0.78, 0.85), 'scale': 1.3},
    'kzombie_night':  {'mul': (0.55, 0.6, 1.05), 'scale': 1.0},
    'kzombie_flying': {'mul': (1.0, 0.72, 1.15), 'scale': 0.85},
    'kzombie_boss':   {'mul': (1.25, 0.55, 0.55), 'scale': 1.6},
}

# Спрайт смотрит ВПРАВО; PIL rotate — против часовой
DIR_ANGLE = {'right': 0, 'up': 90, 'left': 180, 'down': -90}
WOBBLE = [-7, 0, 7, 0]  # кадры ходьбы


def gen_zombies():
    src = Image.open(f"{SRC_ZOMBIE}/zoimbie1_hold.png").convert("RGBA")
    src = src.resize((src.width * 2, src.height * 2), Image.LANCZOS)  # 70x86

    for folder, cfg in ZOMBIE_VARIANTS.items():
        out_dir = f"assets/sprites/{folder}"
        os.makedirs(out_dir, exist_ok=True)
        base = tint(src, cfg['mul'])
        s = cfg['scale']
        base = base.resize((int(base.width * s), int(base.height * s)), Image.LANCZOS)

        canvas_size = int(110 * s) + 20
        for direction, angle in DIR_ANGLE.items():
            for i, wob in enumerate(WOBBLE):
                frame = base.rotate(angle + wob, expand=True, resample=Image.BICUBIC)
                canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
                canvas.paste(frame, ((canvas_size - frame.width) // 2,
                                     (canvas_size - frame.height) // 2), frame)
                canvas.save(f"{out_dir}/{direction}_{i}.png")
        print(f"✅ sprites/{folder}")


# ============================================================
# БАШНИ (площадка + турель + цвет типа, 4 уровня)
# ============================================================

TOWER_DEFS = {
    #            спрайт турели, множитель цвета
    'sniper':       (291, (1.0, 1.0, 1.0)),
    'turret':       (203, (0.95, 0.95, 0.95)),
    'flamethrower': (249, (1.35, 0.75, 0.35)),
    'electric':     (250, (0.55, 0.75, 1.45)),
    'water':        (250, (0.45, 1.05, 1.45)),
    'pvo':          (204, (0.9, 0.95, 1.05)),
    'freeze':       (249, (0.7, 1.05, 1.45)),
    'acid':         (249, (0.75, 1.3, 0.45)),
    'rocket':       (205, (1.25, 0.6, 0.5)),
}


def make_pad(size: int) -> Image.Image:
    """Каменная площадка под башню (плоский стиль)."""
    img = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = (T - size) // 2
    # тень
    d.rounded_rectangle((m + 5, m + 7, m + size + 5, m + size + 7), 18, fill=(0, 0, 0, 70))
    d.rounded_rectangle((m, m, m + size, m + size), 18, fill=(120, 117, 110, 255))
    d.rounded_rectangle((m + 7, m + 7, m + size - 7, m + size - 7), 13, fill=(150, 146, 138, 255))
    return img


def gen_towers():
    for tower_id, (turret_n, mul) in TOWER_DEFS.items():
        out_dir = f"assets/images/towers_kenney/{tower_id}"
        os.makedirs(out_dir, exist_ok=True)
        turret_src = tint(load_tile(turret_n), mul)

        for level in range(1, 5):
            pad_size = 96 + level * 4
            canvas = make_pad(pad_size)
            ts = int(72 + level * 7)
            turret = turret_src.resize((ts, ts), Image.LANCZOS)
            canvas.paste(turret, ((T - ts) // 2, (T - ts) // 2), turret)
            # Пипсы уровня
            d = ImageDraw.Draw(canvas)
            for i in range(level):
                x = T // 2 - (level * 10) // 2 + i * 10
                d.ellipse((x, T - 16, x + 7, T - 9), fill=(255, 215, 0, 255),
                          outline=(120, 90, 0, 255))
            canvas.save(f"{out_dir}/level_{level}.png")
        print(f"✅ towers_kenney/{tower_id}")


if __name__ == "__main__":
    gen_biome_tiles()
    gen_decorations()
    gen_zombies()
    gen_towers()
    print("🎨 Все ассеты сгенерированы")
