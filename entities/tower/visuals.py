# entities/tower/visuals.py
import pygame
import random
import math
from services.resource_loader import ResourceLoader
from core.iso import world_to_screen


class TowerVisuals:
    """Управление отрисовкой башни"""

    # Башни с поворотной головой: base = level_N.png, head = head_N.png
    ROTATING_IDS = ('turret', 'flamethrower', 'sniper', 'water')

    def __init__(self, tower):
        self.tower = tower
        self.image = None
        self.head_image = None
        self._spark_timer = 0.0

    @property
    def has_head(self) -> bool:
        return self.tower.id in self.ROTATING_IDS

    def load_image(self):
        tower = self.tower
        try:
            from core.graphics_theme import towers_dir
            loader = ResourceLoader()
            image_name = f"{towers_dir()}/{tower.id}/level_{tower.upgrades.level}.png"
            self.image = loader.load_image(image_name, scale=(tower.width, tower.height))
        except Exception:
            self.image = self._create_fallback_image()
        if self.has_head:
            try:
                from core.graphics_theme import towers_dir
                loader = ResourceLoader()
                head_name = f"{towers_dir()}/{tower.id}/head_{tower.upgrades.level}.png"
                self.head_image = loader.load_image(head_name, scale=(tower.width, tower.height))
            except Exception:
                self.head_image = None
    
    def _create_fallback_image(self) -> pygame.Surface:
        tower = self.tower
        surf = pygame.Surface((tower.width, tower.height), pygame.SRCALPHA)
        
        level_colors = {
            1: (50, 150, 200),
            2: (100, 200, 100),
            3: (200, 150, 50),
            4: (200, 50, 200)
        }
        color = level_colors.get(tower.upgrades.level, (150, 150, 150))
        pygame.draw.rect(surf, color, (0, 0, tower.width, tower.height))
        font = pygame.font.Font(None, 30)
        text = font.render(str(tower.upgrades.level), True, (255, 255, 255))
        surf.blit(text, (tower.width//2 - text.get_width()//2, tower.height//2 - text.get_height()//2))
        return surf
    
    def get_texture_name(self) -> str:
        return f"tower_{self.tower.id}_{self.tower.upgrades.level}"

    # ===== GPU-ПУТЬ =====

    _level_text_cache = {}

    def draw_batch(self, renderer, offset_x: int = 0, offset_y: int = 0):
        """Рисует башню через GPU-батч. Струя огнемёта — отдельно, через частицы."""
        tower = self.tower
        if not tower.alive:
            return

        sx, sy = world_to_screen(tower.x, tower.y)
        cx = sx + offset_x
        cy = sy + offset_y  # проекция основания башни на землю

        # Тень под башней — у земли
        shadow = renderer.get_region('__shadow__')
        if shadow:
            renderer.batch.draw(shadow, cx + 3, cy + tower.height * 0.08,
                                tower.width * 0.9, tower.height * 0.3,
                                color=(255, 255, 255, 80))

        # Спрайт башни стоит НИЗОМ на земле, а не центром (иначе тонет в тайле)
        base_cy = cy - tower.height * 0.5

        name = self.get_texture_name()
        if not renderer.has_texture(name):
            if self.image is None:
                self.load_image()
            renderer.load_texture(name, self.image or self._create_fallback_image())
        region = renderer.get_region(name)
        renderer.batch.draw(region, cx, base_cy, tower.width, tower.height)

        # Поворотная голова (пулемёт/огнемёт) — вращается к цели
        if self.has_head:
            head_name = f"{name}_head"
            if not renderer.has_texture(head_name):
                if self.head_image is None:
                    self.load_image()
                if self.head_image is not None:
                    renderer.load_texture(head_name, self.head_image)
            if renderer.has_texture(head_name):
                head_region = renderer.get_region(head_name)
                # Ось вращения совпадает с тумбой на базе (чуть ниже центра)
                renderer.batch.draw(head_region, cx, base_cy + tower.height * 0.05,
                                    tower.width, tower.height,
                                    rotation=tower.aim_angle)

        # Текст уровня — кэш отрендеренных надписей в атласе
        level = tower.upgrades.level
        text_name = f"__lvl_text_{level}"
        if not renderer.has_texture(text_name):
            font = TowerVisuals._level_text_cache.get('font')
            if font is None:
                font = pygame.font.Font(None, 16)
                TowerVisuals._level_text_cache['font'] = font
            renderer.load_texture(text_name, font.render(f"Lv.{level}", True, (255, 215, 0)))
        text_region = renderer.get_region(text_name)
        renderer.batch.draw(text_region, cx, base_cy - tower.height // 2 - 20 + text_region.h // 2,
                            text_region.w, text_region.h)
    
    def draw_flame_batch(self, renderer, offset_x: int = 0, offset_y: int = 0):
        """GPU-струя огнемёта/водомёта: аддитивные мягкие круги вдоль луча.

        Огнемёт — тёплая струя (жёлтый→красный), водомёт — инвертированный
        холодный цвет (голубой→белый). Струя выраженная: широкое тело,
        яркое ядро у сопла, брызги/искры.
        """
        tower = self.tower
        if not tower.alive or tower.id not in ('flamethrower', 'water') or not tower.flame_target:
            return

        target = tower.flame_target
        if not target or not target.alive:
            return

        is_water = tower.id == 'water'

        from core.opengl.batch import BLEND_ADDITIVE
        batch = renderer.batch
        soft = renderer.get_region('__soft__')
        dot = renderer.get_region('__dot__')

        sx1, sy1 = world_to_screen(tower.x, tower.y)
        sx2, sy2 = world_to_screen(target.x, target.y)
        start_x = sx1 + offset_x
        start_y = sy1 + offset_y - tower.height * 0.45
        end_x = sx2 + offset_x
        end_y = sy2 + offset_y

        dx = end_x - start_x
        dy = end_y - start_y
        distance = math.hypot(dx, dy)
        if distance < 10:
            return

        dx /= distance
        dy /= distance
        end_x -= dx * 20
        end_y -= dy * 20

        steps = max(8, int(distance / 8))
        time = pygame.time.get_ticks() / 100
        spark_count = min(7, 4 + tower.flame_level)

        # Тело струи — шире и плотнее, чем раньше
        for i in range(steps):
            t = i / steps
            x = start_x + (end_x - start_x) * t
            y = start_y + (end_y - start_y) * t

            noise_x = random.uniform(-6, 6) * (1 - t * 0.3)
            noise_y = random.uniform(-6, 6) * (1 - t * 0.3)

            width = max(4, int((9 + tower.flame_level * 1.5) * (1 - t * 0.25)))

            if is_water:
                # Инверсия огня: голубой у сопла → белесый на конце
                r = max(0, min(255, int(60 + 160 * t)))
                g = max(0, min(255, int(150 + 90 * t)))
                b = 255
            else:
                r = 255
                g = max(0, min(255, int(200 - 180 * t)))
                b = max(0, min(255, int(40 - 40 * t)))
            alpha = max(70, min(255, int(220 * (1 - t * 0.2))))

            batch.draw(soft, x + noise_x, y + noise_y, width * 2, width * 2,
                       color=(r, g, b, alpha), blend=BLEND_ADDITIVE)

        # Яркое ядро у сопла
        core_color = (200, 240, 255) if is_water else (255, 255, 200)
        for i in range(6):
            t = i / 12
            x = start_x + (end_x - start_x) * t * 0.5
            y = start_y + (end_y - start_y) * t * 0.5
            noise_x = random.uniform(-3, 3) * (1 - t)
            noise_y = random.uniform(-3, 3) * (1 - t)
            size = max(3, int(7 * (1 - t * 0.4)) + random.randint(0, 2))
            alpha = int(200 * (1 - t * 0.3))
            batch.draw(soft, x + noise_x, y + noise_y, size * 2, size * 2,
                       color=(*core_color, alpha), blend=BLEND_ADDITIVE)

        # Брызги / искры
        spark_color = (150, 210, 255) if is_water else (255, 200, 100)
        if self._spark_timer <= 0:
            self._spark_timer = 0.1
            for i in range(spark_count):
                t = random.uniform(0.1, 0.95)
                x = start_x + (end_x - start_x) * t
                y = start_y + (end_y - start_y) * t
                spread = 12 * (1 - t * 0.3)
                x += math.sin(time + i * 1.5) * spread
                y += math.cos(time * 1.2 + i * 2.1) * spread
                size = random.randint(2, 5)
                batch.draw(dot, x, y, size, size,
                           color=(*spark_color, 255), blend=BLEND_ADDITIVE)
        else:
            self._spark_timer -= 0.016

    
