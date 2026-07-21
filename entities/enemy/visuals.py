# entities/enemy/visuals.py
import pygame
import math
import random
import os


class EnemyVisuals:
    """Управление отрисовкой и анимациями врага"""

    # Кадры огня общие на весь класс - грузятся с диска ОДИН раз
    # за всю игру, а не на каждого заспавненного врага
    _fire_frames_cache = None

    def __init__(self, enemy):
        self.enemy = enemy
        self.float_offset = 0
        self.float_speed = 2.0

        self._fire_frame_index = 0
        self._fire_anim_speed = 0.08
        self._ensure_fire_sprites_loaded()

    @classmethod
    def _ensure_fire_sprites_loaded(cls):
        """Грузит кадры огня один раз и кэширует на классе"""
        if cls._fire_frames_cache is not None:
            return

        cls._fire_frames_cache = []
        try:
            folder_path = "assets/sprites/fire_sheet/"
            if not os.path.exists(folder_path):
                return

            files = sorted([f for f in os.listdir(folder_path) if f.endswith('.png')])
            if not files:
                return

            for filename in files:
                path = os.path.join(folder_path, filename)
                frame = pygame.image.load(path).convert_alpha()
                cls._fire_frames_cache.append(frame)

            if cls._fire_frames_cache:
                print(f"🔥 Loaded {len(cls._fire_frames_cache)} fire frames for enemies (cached)")
        except Exception as e:
            print(f"⚠️ Could not load fire sprites: {e}")

    @property
    def _fire_frames(self):
        return EnemyVisuals._fire_frames_cache or []

    def get_texture_name(self) -> str:
        enemy = self.enemy
        enemy_type = enemy.config.get('id', 'unknown')
        direction = enemy.direction

        anim_frames = enemy.animations.get(direction, [])
        frame_idx = int(enemy.animation_frame) % len(anim_frames) if anim_frames else 0

        return f"enemy_{enemy_type}_{direction}_{frame_idx}"

    def get_current_frame(self):
        enemy = self.enemy
        if not enemy.animations:
            return self._create_fallback_image()

        direction = enemy.direction
        anim_frames = enemy.animations.get(direction, [])

        if not anim_frames:
            return self._create_fallback_image()

        frame_index = int(enemy.animation_frame) % len(anim_frames)
        return anim_frames[frame_index]

    def _create_fallback_image(self):
        enemy = self.enemy
        surf = pygame.Surface((enemy.width, enemy.height), pygame.SRCALPHA)
        color = enemy.config.get('color', (150, 50, 50))
        pygame.draw.circle(surf, color, (enemy.width // 2, enemy.height // 2), enemy.width // 2)
        return surf

    def get_scaled_image(self) -> pygame.Surface:
        enemy = self.enemy
        if not enemy.image:
            return self._create_fallback_image()

        if enemy.is_flying:
            target_width = enemy.width
            target_height = enemy.height
            if enemy.image.get_width() != target_width or enemy.image.get_height() != target_height:
                return pygame.transform.scale(enemy.image, (target_width, target_height))

        return enemy.image

    # ===== GPU-ПУТЬ =====

    def _frame_region(self, renderer):
        """Кадр текущей анимации в атласе (лениво загружает)."""
        name = self.get_texture_name()
        if not renderer.has_texture(name):
            renderer.load_texture(name, self.get_current_frame())
        return renderer.get_region(name)

    def draw_batch(self, renderer, offset_x: int = 0, offset_y: int = 0):
        """Рисует врага через GPU-батч. Порядок слоёв как в pygame-версии."""
        from core.opengl.batch import BLEND_ADDITIVE
        enemy = self.enemy
        batch = renderer.batch

        if enemy.states.is_dead():
            return

        if enemy.states.is_corpse() or enemy.states.is_fading():
            self._batch_dead(renderer, offset_x, offset_y)
            return

        if enemy.states.is_dying():
            self._batch_dying(renderer, offset_x, offset_y)
            return

        if not enemy.alive:
            return

        if enemy.is_flying:
            self.float_offset = math.sin(pygame.time.get_ticks() / 500) * 8

        cx = enemy.x + offset_x
        cy = enemy.y + offset_y

        # Эффекты ПОД врагом
        self._batch_effects_below(renderer, cx, cy)

        # Тень (у всех врагов; у летающих — на земле, далеко под мышью)
        spawn_alpha = enemy.states.get_spawn_alpha()
        shadow = renderer.get_region('__shadow__')
        if shadow:
            sa = spawn_alpha / 255.0
            if enemy.is_flying:
                batch.draw(shadow, cx, cy + enemy.height // 2, 44, 14,
                           color=(255, 255, 255, int(45 * sa)))
            else:
                sw = enemy.width * 0.72
                batch.draw(shadow, cx, cy + enemy.height * 0.06, sw, sw * 0.36,
                           color=(255, 255, 255, int(85 * sa)))

        float_y = int(self.float_offset) if enemy.is_flying else 0

        region = self._frame_region(renderer)
        w, h = enemy.width, enemy.height
        draw_x = cx - w // 2
        draw_y = cy - h // 1.2 + float_y
        if enemy.is_flying:
            # Летит высоко над головами наземных
            draw_y -= h * 0.55

        if spawn_alpha < 255:
            batch.draw(region, draw_x, draw_y, w, h, centered=False,
                       color=(255, 255, 255, spawn_alpha))
        else:
            batch.draw(region, draw_x, draw_y, w, h, centered=False)

        # Раны на теле — поверх спрайта (с учётом альфы появления)
        self._batch_wounds(renderer, offset_x, offset_y, spawn_alpha / 255.0)

        # Огонь ПОВЕРХ врага
        if enemy.effects.fire_effect_active and self._fire_frames:
            self._fire_frame_index += 0.08
            if self._fire_frame_index >= len(self._fire_frames):
                self._fire_frame_index = 0
            idx = int(self._fire_frame_index)
            fire_name = f"__fire_{idx}"
            if not renderer.has_texture(fire_name):
                renderer.load_texture(fire_name, self._fire_frames[idx])
            fire_region = renderer.get_region(fire_name)
            scale = min(enemy.width / 32, 1.5)
            fw = fire_region.w * scale
            fh = fire_region.h * scale
            batch.draw(fire_region, cx, cy - enemy.height // 2 - 10, fw, fh)

            # Разлетающиеся угольки (бывший _draw_effects_above)
            dot = renderer.get_region('__dot__')
            time = pygame.time.get_ticks() / 200
            fy = cy - enemy.height // 2
            for i in range(3):
                angle = time + i * 2.094
                dist = 20 + math.sin(time * 1.5 + i) * 8
                px = cx + math.cos(angle) * dist * 0.5
                py = fy + math.sin(angle) * dist * 0.3 - 10
                size = random.randint(2, 6)
                alpha = random.randint(100, 200)
                batch.draw(dot, px, py, size, size,
                           color=(255, 200, 100, alpha), blend=BLEND_ADDITIVE)

        self._batch_health_bar(renderer, cx, cy, float_y)

    def _batch_wounds(self, renderer, offset_x, offset_y, alpha_scale=1.0):
        """Рисует раны (декали попаданий) на теле врага поверх спрайта."""
        enemy = self.enemy
        wounds = getattr(enemy, 'wounds', None)
        if not wounds:
            return
        for w in wounds:
            decal = w['decal']
            a = int(decal.current_alpha * alpha_scale)
            if a <= 0:
                continue
            image = decal.image
            if image is None or image.get_width() == 0:
                continue
            name = f"decal_{decal.type}_s{decal.size}_v{decal._atlas_variant}"
            if not renderer.has_texture(name):
                renderer.load_texture(name, image)
            region = renderer.get_region(name)
            renderer.batch.draw(region, decal.x + offset_x, decal.y + offset_y,
                                region.w, region.h,
                                color=(255, 255, 255, a))

    def _batch_dying(self, renderer, offset_x, offset_y):
        enemy = self.enemy
        region = self._frame_region(renderer)
        cx = enemy.states.death_x + offset_x
        cy = enemy.states.death_y + offset_y - enemy.height // 1.2 + enemy.height // 2 + enemy.states.fall_y_offset
        renderer.batch.draw(region, cx, cy, enemy.width, enemy.height,
                            rotation=-enemy.states.fall_angle)
        self._batch_wounds(renderer, offset_x, offset_y)

    def _batch_dead(self, renderer, offset_x, offset_y):
        """Труп: лежит повёрнутым на 45°, при fading растворяется (альфа 255→0)."""
        enemy = self.enemy
        alpha = enemy.states.get_death_alpha()
        if alpha <= 0:
            return
        region = self._frame_region(renderer)
        cx = enemy.states.death_x + offset_x
        cy = enemy.states.death_y + offset_y - enemy.height + enemy.height // 2 + enemy.states.fall_y_offset
        renderer.batch.draw(region, cx, cy, enemy.width, enemy.height,
                            rotation=-enemy.states.FALL_ANGLE,
                            color=(255, 255, 255, alpha))
        # Раны гаснут вместе с трупом
        self._batch_wounds(renderer, offset_x, offset_y, alpha / 255.0)

    def _batch_effects_below(self, renderer, cx, cy):
        from core.opengl.batch import BLEND_ADDITIVE
        enemy = self.enemy
        batch = renderer.batch
        soft = renderer.get_region('__soft__')
        dot = renderer.get_region('__dot__')

        if enemy.effects.water_effect_active:
            batch.draw(soft, cx, cy, 60, 60, color=(50, 150, 255, 100), blend=BLEND_ADDITIVE)
            batch.draw(dot, cx, cy, 28, 28, color=(100, 200, 255, 120))
            batch.draw(dot, cx, cy, 14, 14, color=(200, 230, 255, 70))
            time = pygame.time.get_ticks() / 400
            for i in range(5):
                angle = time + i * 1.256
                dist = 14 + math.sin(time * 1.5 + i * 0.8) * 4
                px = cx + math.cos(angle) * dist
                py = cy + math.sin(angle) * dist - 5
                size = random.randint(6, 14)
                alpha = random.randint(100, 200)
                batch.draw(dot, px, py, size, size,
                           color=(random.randint(80, 200), random.randint(180, 255),
                                  random.randint(200, 255), alpha))

        if enemy.effects.freeze_effect_active:
            batch.draw(soft, cx, cy, 44, 44, color=(150, 220, 255, 90), blend=BLEND_ADDITIVE)
            for i in range(4):
                angle = math.radians(i * 90 + enemy.effects.freeze_effect_timer * 50)
                px = cx + math.cos(angle) * 12
                py = cy + math.sin(angle) * 12
                batch.draw(dot, px, py, 6, 6, color=(200, 240, 255, 80))

        if enemy.effects.acid_effect_active:
            batch.draw(soft, cx, cy, 44, 44, color=(50, 255, 50, 90), blend=BLEND_ADDITIVE)

        if enemy.effects.acid_ground_active:
            # Кислота на полу — едкое зелёное свечение у ног + капли
            batch.draw(soft, cx, cy, 36, 36, color=(120, 255, 60, 70), blend=BLEND_ADDITIVE)
            for i in range(3):
                a = pygame.time.get_ticks() / 300 + i * 2.094
                px = cx + math.cos(a) * 10
                py = cy + math.sin(a) * 5
                batch.draw(dot, px, py, 4, 4, color=(150, 255, 90, 120))

        if enemy.effects.electric_effect_active and not enemy.is_flying:
            batch.draw(soft, cx, cy, 30, 30, color=(100, 200, 255, 90), blend=BLEND_ADDITIVE)
            for spark in enemy.effects.electric_sparks:
                alpha = int(255 * (spark['life'] / 0.5))
                sx = cx + spark['x']
                sy = cy + spark['y']
                batch.draw(dot, sx, sy, 4, 4, color=(200, 255, 255, alpha), blend=BLEND_ADDITIVE)
                batch.draw(soft, sx, sy, 8, 8, color=(100, 200, 255, alpha // 2), blend=BLEND_ADDITIVE)

    def _batch_health_bar(self, renderer, cx, cy, float_y):
        enemy = self.enemy
        if enemy.health >= enemy.max_health:
            return
        batch = renderer.batch

        bar_width = min(enemy.width, 60)
        bar_height = 6 if enemy.is_boss else 4
        health_percent = enemy.health / enemy.max_health

        x = cx - bar_width // 2
        y = cy - enemy.height // 2 - 45 + float_y
        if enemy.is_flying:
            # Полоска над мышью с учётом высоты полёта
            y -= enemy.height * 0.55

        if enemy.is_boss:
            batch.draw_rect(x, y, bar_width, bar_height, (100, 50, 0, 255))
            batch.draw_rect(x, y, bar_width * health_percent, bar_height, (255, 215, 0, 255))
            # Рамка
            batch.draw_rect(x, y - 2, bar_width, 2, (255, 255, 200, 255))
            batch.draw_rect(x, y + bar_height, bar_width, 2, (255, 255, 200, 255))
        else:
            batch.draw_rect(x, y, bar_width, bar_height, (255, 0, 0, 255))
            batch.draw_rect(x, y, bar_width * health_percent, bar_height, (0, 255, 0, 255))

