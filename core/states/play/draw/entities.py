# core/states/play/draw/entities.py
from core.iso import world_to_screen


class EntitiesDraw:
    """Отрисовка игровых сущностей с y-сортировкой (псевдоглубина).

    Все "стоящие" объекты (башни, враги, стены, ворота) рисуются в порядке
    их нижней кромки: что ниже по экрану — то ближе к камере и рисуется поверх.
    Это даёт ощущение глубины без изометрии.
    """

    def __init__(self, state):
        self.state = state

    def draw_scene(self, renderer, ox, oy, screen_w, screen_h):
        """Отрисовывает все сущности в батч"""
        state = self.state

        # ===== Собираем "стоящие" объекты в единый список =====
        # (sort_y, draw_callable)
        drawables = []

        for tower in state.towers:
            if tower.alive:
                drawables.append((tower.y + tower.height * 0.5,
                                  lambda t=tower: t.visuals.draw_batch(renderer, ox, oy)))

        for enemy in state.enemies:
            if not enemy.states.is_dead():
                esx, esy = world_to_screen(enemy.x, enemy.y)
                sx, sy = esx + ox, esy + oy
                if -100 < sx < screen_w + 100 and -100 < sy < screen_h + 100:
                    # Трупы — на земле, под всеми стоящими;
                    # летающие — в воздухе, поверх всех стоящих
                    if not enemy.alive:
                        sort_y = -10000 + enemy.y
                    elif enemy.is_flying:
                        sort_y = 10000 + enemy.y
                    else:
                        sort_y = enemy.y + enemy.height * 0.5
                    drawables.append((sort_y,
                                      lambda e=enemy: e.visuals.draw_batch(renderer, ox, oy)))

        # Стены/ворота — препятствия, по которым зомби лезут: сортируем по
        # ВЕРХНЕЙ кромке визуала, чтобы живые зомби рядом рисовались поверх.
        for gate in state.gates:
            if gate.alive:
                gds = getattr(gate, 'draw_size', gate.height)
                drawables.append((gate.y - gds * 0.5,
                                  lambda g=gate: g.draw_batch(renderer, ox, oy)))

        for wall in state.walls:
            if wall.alive:
                wds = getattr(wall, 'draw_size', wall.height)
                drawables.append((wall.y - wds * 0.5,
                                  lambda w=wall: w.draw_batch(renderer, ox, oy)))

        # Высокие декорации (деревья, здания) участвуют в сортировке
        deco = getattr(state, 'decoration_layer', None)
        if deco:
            for sort_y, name, px, py, size in deco.standing_items():
                drawables.append((sort_y,
                                  lambda n=name, x=px, y=py, s=size:
                                  deco.draw_one_standing(renderer, n, x, y, s, ox, oy)))

        # Факелы
        torches = getattr(state, 'torch_layer', None)
        if torches:
            for sort_y, px, py in torches.standing_items():
                drawables.append((sort_y,
                                  lambda x=px, y=py:
                                  torches.draw_one(renderer, x, y, ox, oy)))

        # Сортировка по нижней кромке: дальние (выше) рисуются первыми
        drawables.sort(key=lambda item: item[0])
        for _, draw in drawables:
            draw()

        # ===== Поверх стоящих: снаряды, струи, вспышки =====

        for proj in state.projectiles:
            psx, psy = world_to_screen(proj.x, proj.y)
            if -100 < psx + ox < screen_w + 100 and -100 < psy + oy < screen_h + 100:
                proj.draw_batch(renderer, ox, oy)

        for tower in state.towers:
            tower.visuals.draw_flame_batch(renderer, ox, oy)
