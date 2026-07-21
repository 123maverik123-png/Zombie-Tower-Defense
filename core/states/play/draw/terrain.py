# core/states/play/draw/terrain.py


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
            if -100 < decal.x + ox < screen_w + 100 and -100 < decal.y + oy < screen_h + 100:
                decal.draw_batch(renderer, ox, oy)

        # 2.5 Кислотные лужи на земле (под сущностями)
        for pool in getattr(state, 'acid_pools', []):
            if -100 < pool.x + ox < screen_w + 100 and -100 < pool.y + oy < screen_h + 100:
                pool.draw_batch(renderer, ox, oy)

        # Ворота и стены рисуются в EntitiesDraw (y-сортировка с врагами)
