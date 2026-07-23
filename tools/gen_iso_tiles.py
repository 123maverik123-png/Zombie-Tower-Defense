# tools/gen_iso_tiles.py
"""Конвертирует квадратные тайлы биомов в изометрические ромбы 2:1.

Источник: assets/images/tiles/{forest,desert,city}/*.png
Результат: assets/images/tiles_iso/{биом}/*.png

tile_castle и tile_portal — плоские базовые ромбы (трава/дорога без 3D-объектов).
Кристалл и портал генерируются как отдельные изо-декорации:
  assets/images/decorations_iso/{биом}/crystal.png
  assets/images/decorations_iso/{биом}/portal.png

Запуск: python tools/gen_iso_tiles.py  (из корня проекта)
"""
import os
import math
from PIL import Image, ImageDraw

SRC_ROOT = "assets/images/tiles"
OUT_ROOT = "assets/images/tiles_iso"
DECO_OUT = "assets/images/decorations_iso"
BIOMES = ("forest", "desert", "city")

# Базовые тайлы для castle/portal (без 3D-объектов)
FLAT_OVERRIDE = {
    "tile_castle.png": "tile_grass.png",
    "tile_portal.png": "tile_road_straight_h.png",
}


def to_iso_diamond(img: Image.Image) -> Image.Image:
    """Квадратный top-down тайл -> ромб 2:1 (точное соотношение сторон)."""
    T = img.width  # квадратный источник
    rotated = img.rotate(-45, expand=True, resample=Image.BICUBIC, fillcolor=(0, 0, 0, 0))
    # Финальный ресайз до точного 2:1 — избегаем накопленной ошибки от нечётных размеров
    return rotated.resize((T, T // 2), Image.LANCZOS)


def _crystal_iso(size: int) -> Image.Image:
    """Кристалл-октаэдр в изометрическом ракурсе (стоит на тайле)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = size // 2
    # Тень-эллипс на земле
    d.ellipse((cx - size//5, size*3//4 - size//12,
               cx + size//5, size*3//4 + size//12), fill=(0, 0, 0, 60))
    # Грани кристалла (изо-ракурс: чуть сдвинут вверх)
    top   = int(size * 0.08)
    bot   = int(size * 0.78)
    midy  = int(size * 0.44)
    half  = int(size * 0.28)
    outl  = (18, 40, 70, 255)
    d.polygon([(cx, top), (cx - half, midy), (cx, midy)],       fill=(52, 120, 190))
    d.polygon([(cx, top), (cx + half, midy), (cx, midy)],       fill=(170, 225, 250))
    d.polygon([(cx - half, midy), (cx, bot), (cx, midy)],       fill=(70, 145, 210))
    d.polygon([(cx + half, midy), (cx, bot), (cx, midy)],       fill=(90, 175, 235))
    d.line([(cx, top), (cx - half, midy), (cx, bot),
            (cx + half, midy), (cx, top)], fill=outl, width=2)
    d.line([(cx, top), (cx, bot)], fill=(120, 190, 235, 180), width=1)
    # Блик
    d.polygon([(cx+3, top+4), (cx+half-6, midy-3), (cx+3, midy-3)],
              fill=(235, 250, 255))
    return img


def _portal_iso(size: int) -> Image.Image:
    """Портал в изометрическом ракурсе: вертикальное кольцо, сплюснутое под изо."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = size // 2
    # Тень
    d.ellipse((cx - size//5, size*4//5 - size//14,
               cx + size//5, size*4//5 + size//14), fill=(0, 0, 0, 55))
    # Кольцо портала (вертикальное, сплюснутое по горизонтали под изо)
    rw = int(size * 0.30)   # полуширина
    rh = int(size * 0.38)   # полувысота
    cy = int(size * 0.46)
    rings = [
        (rw+8, rh+10, (70, 20, 90, 60)),
        (rw+4, rh+5,  (120, 30, 140, 130)),
        (rw,   rh,    (180, 40, 130, 210)),
        (rw-5, rh-6,  (230, 60, 90, 255)),
        (rw-9, rh-11, (255, 110, 140, 255)),
        (rw-13,rh-16, (90, 20, 70, 255)),
        (rw-17,rh-21, (20, 5, 30, 255)),
    ]
    for hw, hh, col in rings:
        d.ellipse((cx-hw, cy-hh, cx+hw, cy+hh), fill=col)
    # Искры по кольцу
    for i in range(8):
        a = i * (2 * math.pi / 8)
        x = cx + int((rw-6) * math.cos(a))
        y = cy + int((rh-7) * math.sin(a))
        d.ellipse((x-2, y-2, x+2, y+2), fill=(255, 180, 210, 255))
    return img


def gen_iso_tiles():
    for biome in BIOMES:
        src_dir = f"{SRC_ROOT}/{biome}"
        out_dir = f"{OUT_ROOT}/{biome}"
        if not os.path.isdir(src_dir):
            print(f"⚠️ Пропуск {biome}: нет {src_dir}")
            continue
        os.makedirs(out_dir, exist_ok=True)
        count = 0
        for filename in sorted(os.listdir(src_dir)):
            if not filename.endswith(".png"):
                continue
            src_file = FLAT_OVERRIDE.get(filename, filename)
            img = Image.open(f"{src_dir}/{src_file}").convert("RGBA")
            to_iso_diamond(img).save(f"{out_dir}/{filename}")
            count += 1
        print(f"✅ tiles_iso/{biome}: {count}")


def gen_iso_decorations():
    for biome in BIOMES:
        out_dir = f"{DECO_OUT}/{biome}"
        os.makedirs(out_dir, exist_ok=True)
        _crystal_iso(128).save(f"{out_dir}/crystal.png")
        _portal_iso(128).save(f"{out_dir}/portal.png")
    print(f"✅ decorations_iso: crystal + portal x{len(BIOMES)}")


if __name__ == "__main__":
    gen_iso_tiles()
    gen_iso_decorations()
    print("🎨 Изо-тайлы и декорации сгенерированы")
