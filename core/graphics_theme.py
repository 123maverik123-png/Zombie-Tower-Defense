# core/graphics_theme.py
"""Выбор графической темы и биома уровня.

THEME:
  'kenney'  — новая графика (Kenney CC0, плоский вектор)
  'classic' — старые ассеты
"""

THEME = 'kenney'

# Диапазоны уровней по биомам
def biome_for_level(level_number: int) -> str:
    if level_number <= 0:        # кастомные карты из редактора
        return 'forest'
    if level_number <= 20:
        return 'forest'
    if level_number <= 35:
        return 'desert'
    return 'city'


# Соответствие папок спрайтов врагов (pzombie_* — процедурный пиксель-арт,
# генератор: tools/gen_zombie_pixel.py)
ENEMY_SPRITES = {
    'zombie_normal_sheet': 'pzombie_normal',
    'zombie_fast_sheet': 'pzombie_fast',
    'zombie_tank_sheet': 'pzombie_tank',
    'zombie_night_sheet': 'pzombie_night',
    'zombie_flying_sheet': 'pzombie_flying',
    'zombie_boss_sheet': 'pzombie_boss',
    'zombie_light_sheet': 'pzombie_normal',
}


def enemy_sprite_folder(folder: str) -> str:
    if THEME == 'kenney':
        return ENEMY_SPRITES.get(folder, folder)
    return folder


def towers_dir() -> str:
    # towers_pixel — процедурный пиксель-арт (tools/gen_tower_pixel.py)
    return 'towers_pixel' if THEME == 'kenney' else 'towers'


# ===== Атмосфера биомов (тёмное фэнтези) =====
# ambient: цвет+альфа мультипликативного затемнения поверх сцены
# vignette_alpha: сила виньетки по краям кадра
BIOME_AMBIENT = {
    'forest': {'ambient': (14, 20, 44, 88), 'vignette_alpha': 185},   # холодная ночь
    'desert': {'ambient': (58, 28, 8, 60), 'vignette_alpha': 150},    # пыльный закат
    'city':   {'ambient': (20, 15, 38, 95), 'vignette_alpha': 200},   # мёртвый город
}


def biome_ambient(biome: str) -> dict:
    return BIOME_AMBIENT.get(biome, BIOME_AMBIENT['forest'])
