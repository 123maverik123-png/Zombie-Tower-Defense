# entities/decals/types.py

DECAL_TYPES = {
    'blood': {
        'color': (180, 30, 30),
        'size': 30,
        'lifetime': 8.0,
        'alpha': 200,
        'fade': True,
        'animated': False
    },
    'blood_small': {
        'color': (160, 20, 20),
        'size': 18,
        'lifetime': 6.0,
        'alpha': 180,
        'fade': True,
        'animated': False
    },
    'blood_large': {
        'color': (200, 40, 40),
        'size': 45,
        'lifetime': 10.0,
        'alpha': 220,
        'fade': True,
        'animated': False
    },
    'smoke': {
        'color': (100, 100, 100),
        'size': 35,
        'lifetime': 4.0,
        'alpha': 120,
        'fade': True,
        'animated': False
    },
    'smoke_light': {
        'color': (150, 150, 150),
        'size': 25,
        'lifetime': 3.0,
        'alpha': 80,
        'fade': True,
        'animated': False
    },
    'crack': {
        'color': (80, 80, 80),
        'size': 30,
        'lifetime': 12.0,
        'alpha': 150,
        'fade': False,
        'animated': False
    },
    'spark': {
        'color': (255, 255, 200),
        'size': 12,
        'lifetime': 1.0,
        'alpha': 255,
        'fade': True,
        'animated': False
    },
    'fire': {
        'color': (255, 100, 20),
        'size': 10,
        'lifetime': 2.0,
        'alpha': 180,
        'fade': True,
        'animated': True,
        'anim_frames': 16,          # ✅ 16 кадров
        'anim_speed': 0.04          # ✅ скорость для 16 кадров
    },
    'fire_small': {
        'color': (255, 100, 20),
        'size': 6,
        'lifetime': 1.5,
        'alpha': 200,
        'fade': True,
        'animated': True,
        'anim_frames': 16,
        'anim_speed': 0.03
    },
    'fire_big': {
        'color': (255, 100, 20),
        'size': 20,
        'lifetime': 3.0,
        'alpha': 200,
        'fade': True,
        'animated': True,
        'anim_frames': 16,
        'anim_speed': 0.05
    },
    'acid': {
        'color': (50, 200, 50),
        'size': 22,
        'lifetime': 5.0,
        'alpha': 150,
        'fade': True,
        'animated': False
    },
    'water_splash': {
        'color': (50, 150, 255),
        'size': 25,
        'lifetime': 3.0,
        'alpha': 150,
        'fade': True,
        'animated': False
    },
    'ice_crystal': {
        'color': (200, 240, 255),
        'size': 20,
        'lifetime': 4.0,
        'alpha': 180,
        'fade': True,
        'animated': False
    }
}


def get_decal_config(decal_type: str) -> dict:
    """Возвращает конфигурацию для типа декали"""
    return DECAL_TYPES.get(decal_type, DECAL_TYPES['blood'])