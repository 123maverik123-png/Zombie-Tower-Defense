# entities/decals/decal.py
import pygame
import random
import math
import os
from typing import Optional

from .types import get_decal_config


class Decal:
    """Декаль — след на земле от попаданий, взрывов и т.д."""
    
    def __init__(self, x: float, y: float, decal_type: str, 
                 rotation: float = None, scale: float = 1.0):
        self.x = x
        self.y = y
        self.type = decal_type
        
        config = get_decal_config(decal_type)
        
        self.lifetime = config['lifetime'] * random.uniform(0.8, 1.2)
        self.max_lifetime = self.lifetime
        self.alpha = config['alpha']
        self.fade = config['fade']
        self.color = config['color']
        self.size = int(config['size'] * scale)
        
        self.animated = config.get('animated', False)
        self.anim_frames = config.get('anim_frames', 1)
        self.anim_speed = config.get('anim_speed', 0.1)
        self.anim_frame = 0
        self.rotation = rotation if rotation is not None else random.uniform(0, 360)
        self.scale = scale * random.uniform(0.7, 1.3)
        
        self.frames = []
        self.image = None
        
        if self.animated:
            self._load_sprites()
        else:
            self._create_static_image()
        
        self.alive = True
        self.current_alpha = self.alpha
        # Вариант для GPU-атласа: до 4 случайных обликов на тип декали,
        # чтобы не забивать атлас уникальной текстурой на каждый экземпляр
        self._atlas_variant = random.randint(0, 3)
    
    def _load_sprites(self):
        """Загружает спрайты для анимированной декали"""
        from utils.sprite_loader import SpriteLoader
        
        loader = SpriteLoader()
        folder_name = f"{self.type}_sheet"
        folder_path = os.path.join(loader.sprites_path, folder_name)
        
        if not os.path.exists(folder_path):
            print(f"❌ Folder not found: {folder_path}")
            self.image = self._empty_surface()
            return
        
        animations = loader.load_animations_from_folder(folder_name, self.anim_frames)
        
        if animations and 'down' in animations and len(animations['down']) > 0:
            self.frames = animations['down']
            self.image = self.frames[0] if self.frames else self._empty_surface()
            print(f"✅ Loaded {len(self.frames)} frames for {self.type}")
        else:
            print(f"⚠️ No frames loaded for {self.type}")
            self.image = self._empty_surface()
    
    def _empty_surface(self) -> pygame.Surface:
        """Создаёт пустую прозрачную поверхность"""
        surf = pygame.Surface((4, 4), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        return surf
    
    def _create_static_image(self):
        """Создаёт изображение для статичных декалей"""
        # ✅ Для огня — всегда пустая поверхность (используем только анимацию)
        if self.type == 'fire' or self.type.startswith('fire'):
            self.image = self._empty_surface()
            return
        
        # Для остальных типов — создаём изображение
        size = max(4, self.size)
        surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        center = size
        
        if self.type.startswith('blood'):
            self._draw_blood(surf, center, center, size)
        elif self.type == 'smoke' or self.type == 'smoke_light':
            self._draw_smoke(surf, center, center, size)
        elif self.type == 'crack':
            self._draw_crack(surf, center, center, size)
        elif self.type == 'spark':
            self._draw_spark(surf, center, center, size)
        elif self.type == 'acid':
            self._draw_acid(surf, center, center, size)
        elif self.type == 'water_splash':
            self._draw_water_splash(surf, center, center, size)
        elif self.type == 'ice_crystal':
            self._draw_ice_crystal(surf, center, center, size)
        else:
            pygame.draw.circle(surf, (*self.color, self.alpha), (center, center), size)
        
        self.image = surf
    
    # ===== МЕТОДЫ РИСОВАНИЯ СТАТИКИ =====
    
    def _draw_blood(self, surf, cx, cy, size):
        for radius in range(size, 2, -2):
            alpha = int(self.alpha * (radius / size) * random.uniform(0.6, 1.0))
            r = int(self.color[0] * random.uniform(0.7, 1.1))
            g = int(self.color[1] * random.uniform(0.5, 1.0))
            b = int(self.color[2] * random.uniform(0.5, 1.0))
            r = max(0, min(255, r)); g = max(0, min(255, g)); b = max(0, min(255, b))
            offset_x = random.uniform(-3, 3) * (1 - radius / size)
            offset_y = random.uniform(-3, 3) * (1 - radius / size)
            pygame.draw.circle(surf, (r, g, b, alpha), (int(cx + offset_x), int(cy + offset_y)), radius)
    
    def _draw_smoke(self, surf, cx, cy, size):
        for radius in range(size, 2, -3):
            alpha = int(self.alpha * (radius / size) * random.uniform(0.4, 0.8))
            gray = random.randint(80, 180)
            offset_x = random.uniform(-5, 5) * (1 - radius / size)
            offset_y = random.uniform(-5, 5) * (1 - radius / size)
            pygame.draw.circle(surf, (gray, gray, gray, alpha), (int(cx + offset_x), int(cy + offset_y)), radius)
    
    def _draw_crack(self, surf, cx, cy, size):
        points = [(cx, cy)]
        for _ in range(3 + random.randint(0, 3)):
            angle = random.uniform(0, 2 * math.pi)
            length = random.uniform(size * 0.2, size * 0.8)
            x = points[-1][0] + math.cos(angle) * length
            y = points[-1][1] + math.sin(angle) * length
            points.append((x, y))
            if random.random() < 0.3:
                branch_angle = angle + random.uniform(-0.8, 0.8)
                branch_length = random.uniform(size * 0.1, size * 0.3)
                bx = points[-1][0] + math.cos(branch_angle) * branch_length
                by = points[-1][1] + math.sin(branch_angle) * branch_length
                points.append((bx, by))
        for i in range(len(points) - 1):
            width = random.randint(1, 3)
            pygame.draw.line(surf, (*self.color, self.alpha), points[i], points[i+1], width)
    
    def _draw_spark(self, surf, cx, cy, size):
        pygame.draw.circle(surf, (255, 255, 255, 255), (cx, cy), size // 2)
        pygame.draw.circle(surf, (255, 255, 200, 200), (cx, cy), size)
        for angle in range(0, 360, 20):
            rad = math.radians(angle)
            length = random.uniform(size * 0.3, size * 0.9)
            end_x = cx + math.cos(rad) * length
            end_y = cy + math.sin(rad) * length
            alpha = random.randint(50, 150)
            pygame.draw.line(surf, (255, 255, 200, alpha), (cx, cy), (end_x, end_y), 2)
    
    def _draw_acid(self, surf, cx, cy, size):
        for radius in range(size, 2, -2):
            alpha = int(self.alpha * (radius / size) * random.uniform(0.5, 0.9))
            r = random.randint(30, 80); g = random.randint(150, 255); b = random.randint(30, 80)
            offset_x = random.uniform(-3, 3) * (1 - radius / size)
            offset_y = random.uniform(-3, 3) * (1 - radius / size)
            pygame.draw.circle(surf, (r, g, b, alpha), (int(cx + offset_x), int(cy + offset_y)), radius)
        for _ in range(3 + random.randint(0, 3)):
            radius = random.randint(2, 5)
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(0, size * 0.6)
            x = cx + math.cos(angle) * dist; y = cy + math.sin(angle) * dist
            alpha = random.randint(50, 150)
            pygame.draw.circle(surf, (100, 255, 100, alpha), (int(x), int(y)), radius)
            pygame.draw.circle(surf, (50, 200, 50, alpha // 2), (int(x), int(y)), radius * 2, 1)
    
    def _draw_water_splash(self, surf, cx, cy, size):
        for radius in range(size, 2, -2):
            alpha = int(self.alpha * (radius / size) * random.uniform(0.5, 0.9))
            r = random.randint(30, 100); g = random.randint(130, 200); b = random.randint(200, 255)
            offset_x = random.uniform(-3, 3) * (1 - radius / size)
            offset_y = random.uniform(-3, 3) * (1 - radius / size)
            pygame.draw.circle(surf, (r, g, b, alpha), (int(cx + offset_x), int(cy + offset_y)), radius)
        for _ in range(4 + random.randint(0, 4)):
            radius = random.randint(2, 5)
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(size * 0.4, size * 1.1)
            x = cx + math.cos(angle) * dist; y = cy + math.sin(angle) * dist
            alpha = random.randint(80, 180)
            pygame.draw.circle(surf, (100, 200, 255, alpha), (int(x), int(y)), radius)
            pygame.draw.circle(surf, (150, 220, 255, alpha // 2), (int(x), int(y)), radius * 2, 1)
    
    def _draw_ice_crystal(self, surf, cx, cy, size):
        for radius in range(size, 2, -2):
            alpha = int(self.alpha * (radius / size) * random.uniform(0.5, 0.9))
            r = random.randint(180, 230); g = random.randint(220, 255); b = random.randint(230, 255)
            offset_x = random.uniform(-3, 3) * (1 - radius / size)
            offset_y = random.uniform(-3, 3) * (1 - radius / size)
            pygame.draw.circle(surf, (r, g, b, alpha), (int(cx + offset_x), int(cy + offset_y)), radius)
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            length = random.uniform(size * 0.3, size * 0.8)
            end_x = cx + math.cos(rad) * length; end_y = cy + math.sin(rad) * length
            alpha = random.randint(100, 200)
            pygame.draw.line(surf, (200, 240, 255, alpha), (cx, cy), (end_x, end_y), random.randint(1, 3))
        for _ in range(3 + random.randint(0, 3)):
            radius = random.randint(2, 4)
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(size * 0.2, size * 0.7)
            x = cx + math.cos(angle) * dist; y = cy + math.sin(angle) * dist
            alpha = random.randint(100, 200)
            for i in range(3):
                a = angle + math.radians(i * 120)
                end_x = x + math.cos(a) * radius * 2
                end_y = y + math.sin(a) * radius * 2
                pygame.draw.line(surf, (200, 240, 255, alpha), (x, y), (end_x, end_y), 1)
    
    # ===== ОСНОВНЫЕ МЕТОДЫ =====
    
    def update(self, dt: float):
        self.lifetime -= dt
        
        if self.animated and self.frames:
            self.anim_frame += dt * (1.0 / self.anim_speed)
            if self.anim_frame >= len(self.frames):
                self.anim_frame = 0
            frame_index = int(self.anim_frame)
            if frame_index < len(self.frames):
                self.image = self.frames[frame_index]
        
        if self.lifetime > 0:
            progress = 1 - (self.lifetime / self.max_lifetime)
            if self.fade and progress > 0.6:
                fade_alpha = 1 - (progress - 0.6) / 0.4
                self.current_alpha = int(self.alpha * fade_alpha)
            else:
                self.current_alpha = self.alpha
        else:
            self.current_alpha = 0
        
        if self.lifetime <= 0:
            self.alive = False
    
    def draw(self, screen: pygame.Surface, offset_x: int = 0, offset_y: int = 0):
        if not self.alive or self.current_alpha <= 0:
            return
        
        if self.animated and self.frames:
            frame_index = int(self.anim_frame) % len(self.frames)
            image = self.frames[frame_index]
        else:
            image = self.image
        
        if image is None:
            return
        
        if image.get_width() == 0 or image.get_height() == 0:
            return
        
        image = image.copy()
        image.set_alpha(self.current_alpha)

        draw_x = self.x + offset_x - image.get_width() // 2
        draw_y = self.y + offset_y - image.get_height() // 2
        screen.blit(image, (draw_x, draw_y))

    def draw_batch(self, renderer, offset_x: int = 0, offset_y: int = 0):
        """Рисует декаль через GPU-батч. Изображение кладётся в атлас один раз."""
        if not self.alive or self.current_alpha <= 0:
            return

        if self.animated and self.frames:
            frame_index = int(self.anim_frame) % len(self.frames)
            image = self.frames[frame_index]
            name = f"decal_{self.type}_f{frame_index}"
        else:
            image = self.image
            # Статичные декали одного типа делят до 4 обликов
            name = f"decal_{self.type}_s{self.size}_v{self._atlas_variant}"

        if image is None or image.get_width() == 0 or image.get_height() == 0:
            return

        if not renderer.has_texture(name):
            renderer.load_texture(name, image)
        region = renderer.get_region(name)

        renderer.batch.draw(region, self.x + offset_x, self.y + offset_y,
                            region.w, region.h,
                            color=(255, 255, 255, self.current_alpha))