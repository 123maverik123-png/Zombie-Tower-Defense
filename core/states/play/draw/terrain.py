# core/states/play/draw/terrain.py
from core.iso import world_to_screen


class TerrainDraw:
    """Отрисовка карты, тайлов и декалей на земле через GPU-батч"""

    def __init__(self, state):
        self.state = state

    def draw_scene(self, renderer, ox, oy, screen_w, screen_h):
        """Отрисовывает карту и декали в батч"""
        state = self.state

        # 1. Карта
        state.tile_manager.draw_opengl(renderer)

        # 1.5 Декорации (поверх тайлов, под сущностями)
        if getattr(state, 'decoration_layer', None):
            state.decoration_layer.draw_scene(renderer, ox, oy)

        # 2. Декали на земле (только видимые)
        for decal in state.decals:
            dsx, dsy = world_to_screen(decal.x, decal.y)
            if -100 < dsx + ox < screen_w + 100 and -100 < dsy + oy < screen_h + 100:
                decal.draw_batch(renderer, ox, oy)

        # 2.5 Кислотные лужи на земле (под сущностями)
        for pool in getattr(state, 'acid_pools', []):
            psx, psy = world_to_screen(pool.x, pool.y)
            if -100 < psx + ox < screen_w + 100 and -100 < psy + oy < screen_h + 100:
                pool.draw_batch(renderer, ox, oy)

        # Ворота и стены рисуются в EntitiesDraw (y-сортировка с врагами)
