# entities/projectile.py
import math
import pygame
import random
from typing import Optional, Tuple, List
from entities.base import Entity

class Projectile(Entity):
    """Снаряд с поддержкой разных типов и цепного урона"""
    
    def __init__(self, start_pos: Tuple[float, float], target: Entity, 
                 speed: float, damage: int, damage_type: str = 'physical',
                 config: dict = None):
        config = config or {}
        
        # Если это снайпер или турель — не создаём снаряд
        if config.get('id') in ['sniper', 'turret']:
            self.alive = False
            return
        
        super().__init__(
            entity_id=config.get('id', 'projectile'),
            x=start_pos[0],
            y=start_pos[1],
            config=config
        )
        
        self.target = target
        self.speed = speed
        self.damage = damage
        self.damage_type = damage_type
        
        self.projectile_type = config.get('projectile_type', 'bullet')
        
        self.width = config.get('width', 12)
        self.height = config.get('height', 12)
        self.rect = pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)
        
        self.piercing = config.get('piercing', False)
        self.aoe_radius = config.get('aoe_radius', 0)
        self.hit_effect = config.get('hit_effect', None)
        self.effect_value = config.get('effect_value', 0)
        self.effect_duration = config.get('effect_duration', 0)
        self.slow_duration = config.get('slow_duration', 0)
        self.slow_multiplier = config.get('slow_multiplier', 0.5)
        
        # Цепной урон
        self.chain_count = config.get('chain_count', 0)
        self.all_enemies: List[Entity] = config.get('all_enemies', [])
        self.hit_enemies: List[Entity] = []
        
        # След для огнемёта
        self.trail = []
        self.max_trail = 8
        
        # Угол поворота
        self.angle = 0
        
        # Эффекты электричества
        self.lightning_particles = []
        self.lightning_timer = 0
        
        self._load_image()
    
    def get_texture_name(self) -> str:
        """
        Возвращает имя текстуры для OpenGL.
        Использует только тип снаряда для кэширования.
        """
        return f"projectile_{self.projectile_type}"
    
    def _load_image(self):
        try:
            from services.resource_loader import ResourceLoader
            loader = ResourceLoader()
            image_name = f"projectiles/{self.projectile_type}.png"
            self.image = loader.load_image(image_name, scale=(self.width, self.height))
        except Exception:
            self.image = self._create_fallback_image()
    
    def _create_fallback_image(self) -> pygame.Surface:
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        if self.projectile_type == 'flamethrower':
            size = 20
            pygame.draw.circle(surf, (255, 50, 0), (size//2, size//2), size//2)
            pygame.draw.circle(surf, (255, 150, 50), (size//2, size//2), size//3)
            pygame.draw.circle(surf, (255, 255, 200), (size//2, size//2), size//5)
            self.width = size
            self.height = size
        
        elif self.projectile_type == 'electric':
            size = 24
            for r in range(3, 0, -1):
                alpha = 30 * r
                pygame.draw.circle(surf, (100, 200, 255, alpha), (size//2, size//2), size//2 * r // 3)
            self._draw_lightning(surf, size)
            self.width = size
            self.height = size
        
        else:
            pygame.draw.circle(surf, (255, 200, 50), (self.width//2, self.height//2), self.width//2)
        
        return surf
    
    def _draw_lightning(self, surf: pygame.Surface, size: int):
        points = []
        x, y = size//2, size//2
        for i in range(8):
            x += random.randint(-4, 4)
            y += random.randint(-6, 6)
            points.append((x, y))
        
        for i in range(len(points) - 1):
            pygame.draw.line(surf, (200, 255, 255), points[i], points[i+1], 3)
            pygame.draw.line(surf, (100, 200, 255), points[i], points[i+1], 1)
        
        pygame.draw.circle(surf, (255, 255, 255), (size//2, size//2), 4)
    
    def update(self, dt: float):
        if not self.alive:
            return
        
        if self.projectile_type == 'electric':
            self.lightning_timer += dt
            if self.lightning_timer > 0.05:
                self.lightning_timer = 0
                self._generate_lightning_particles()
            
            for p in self.lightning_particles[:]:
                p['life'] -= dt
                p['x'] += p['dx'] * dt * 50
                p['y'] += p['dy'] * dt * 50
                if p['life'] <= 0:
                    self.lightning_particles.remove(p)
        
        if not self.target or not self.target.alive:
            self.alive = False
            return
        
        target_center = self.target.get_center()
        dx = target_center[0] - self.x
        dy = target_center[1] - self.y
        distance = math.hypot(dx, dy)
        
        if self.projectile_type == 'flamethrower':
            self._update_trail()
        
        if distance < 5:
            self._hit_target()
            return
        
        move_distance = self.speed * dt
        
        if move_distance >= distance:
            self.x = target_center[0]
            self.y = target_center[1]
            self._hit_target()
        else:
            if distance > 0:
                self.x += (dx / distance) * move_distance
                self.y += (dy / distance) * move_distance
        
        if distance > 0:
            self.angle = math.degrees(math.atan2(dy, dx))
        
        self.rect.x = self.x - self.width // 2
        self.rect.y = self.y - self.height // 2
    
    def _generate_lightning_particles(self):
        for _ in range(3):
            self.lightning_particles.append({
                'x': self.x + random.randint(-10, 10),
                'y': self.y + random.randint(-10, 10),
                'dx': random.uniform(-1, 1),
                'dy': random.uniform(-1, 1),
                'life': random.uniform(0.1, 0.3)
            })
    
    def _update_trail(self):
        self.trail.append((self.x, self.y))
        if len(self.trail) > self.max_trail:
            self.trail.pop(0)
    
    def _hit_target(self):
        if not self.target or not self.target.alive:
            self.alive = False
            return
        
        # Цепной урон
        if self.chain_count > 0:
            self._chain_lightning()
            self.alive = False
            return
        
        # Электрическая (мгновенный урон)
        if self.projectile_type == 'electric':
            self.target.take_damage(self.damage, self.damage_type)
            if self.slow_duration > 0 and hasattr(self.target, 'apply_slow'):
                self.target.apply_slow(self.slow_multiplier, self.slow_duration)
            if hasattr(self.target, 'apply_electric_effect'):
                self.target.apply_electric_effect(self.slow_duration or 1.0)
            self.alive = False
            return
        
        # Обычный урон
        actual_damage = self.target.take_damage(self.damage, self.damage_type)
        
        if self.hit_effect == 'slow' and hasattr(self.target, 'apply_slow'):
            self.target.apply_slow(self.effect_value, self.effect_duration)
        
        if self.aoe_radius > 0:
            self._apply_aoe_damage()
        
        if not self.piercing:
            self.alive = False
    
    def _apply_aoe_damage(self):
        from core.event_bus import EventBus
        EventBus.emit('aoe_damage_request', {
            'projectile': self,
            'center': self.get_center(),
            'radius': self.aoe_radius,
            'damage': self.damage * 0.5,
            'damage_type': self.damage_type
        })
    
    def _chain_lightning(self):
        if not self.all_enemies:
            return
        
        hit_enemies = [self.target]
        damage = self.damage
        chain_count = self.chain_count
        
        self.target.take_damage(damage, self.damage_type)
        if hasattr(self.target, 'apply_electric_effect'):
            self.target.apply_electric_effect(0.5)
        self._add_lightning_effect(self.target, self.target)
        
        for _ in range(chain_count - 1):
            last_enemy = hit_enemies[-1]
            
            nearest = None
            min_dist = float('inf')
            
            for enemy in self.all_enemies:
                if not enemy.alive:
                    continue
                if enemy in hit_enemies:
                    continue
                
                dist = math.hypot(enemy.x - last_enemy.x, enemy.y - last_enemy.y)
                if dist < 250 and dist < min_dist:
                    nearest = enemy
                    min_dist = dist
            
            if nearest:
                hit_enemies.append(nearest)
                nearest.take_damage(damage, self.damage_type)
                if hasattr(nearest, 'apply_electric_effect'):
                    nearest.apply_electric_effect(0.5)
                self._add_lightning_effect(last_enemy, nearest)
            else:
                break
        
        self.alive = False
    
    def _add_lightning_effect(self, from_enemy: Entity, to_enemy: Entity):
        from core.event_bus import EventBus
        EventBus.emit('chain_lightning_effect', {
            'from': from_enemy,
            'to': to_enemy,
            'damage': self.damage
        })
    
    def draw(self, screen: pygame.Surface, offset_x: int = 0, offset_y: int = 0):
        if not self.alive:
            return
        
        if self.projectile_type == 'flamethrower' and len(self.trail) > 1:
            for i in range(len(self.trail) - 1):
                alpha = int(255 * (i / len(self.trail)))
                x1, y1 = self.trail[i]
                x2, y2 = self.trail[i+1]
                pygame.draw.line(screen, (255, 150, 50, alpha), 
                               (x1 + offset_x, y1 + offset_y),
                               (x2 + offset_x, y2 + offset_y), 3)
        
        if self.projectile_type == 'electric':
            for p in self.lightning_particles:
                alpha = int(255 * (p['life'] / 0.3))
                pygame.draw.circle(screen, (200, 255, 255, alpha), 
                                 (int(p['x'] + offset_x), int(p['y'] + offset_y)), 2)
                pygame.draw.circle(screen, (100, 200, 255, alpha // 2), 
                                 (int(p['x'] + offset_x), int(p['y'] + offset_y)), 4)
        
        if self.image:
            rotated_image = pygame.transform.rotate(self.image, self.angle)
            rect = rotated_image.get_rect(center=(self.x + offset_x, self.y + offset_y))
            screen.blit(rotated_image, rect)
        else:
            pygame.draw.circle(screen, (255, 200, 50),
                             (int(self.x + offset_x), int(self.y + offset_y)),
                             self.width//2)

    def draw_batch(self, renderer, offset_x: int = 0, offset_y: int = 0):
        """Рисует снаряд через GPU-батч"""
        if not self.alive:
            return
        from core.opengl.batch import BLEND_ADDITIVE
        batch = renderer.batch
        cx = self.x + offset_x
        cy = self.y + offset_y

        if self.projectile_type == 'flamethrower' and len(self.trail) > 1:
            for i in range(len(self.trail) - 1):
                alpha = int(255 * (i / len(self.trail)))
                x1, y1 = self.trail[i]
                x2, y2 = self.trail[i + 1]
                batch.draw_line(x1 + offset_x, y1 + offset_y,
                                x2 + offset_x, y2 + offset_y,
                                3, (255, 150, 50, alpha), blend=BLEND_ADDITIVE)

        if self.projectile_type == 'electric':
            dot = renderer.get_region('__dot__')
            soft = renderer.get_region('__soft__')
            for p in self.lightning_particles:
                alpha = int(255 * (p['life'] / 0.3))
                px, py = p['x'] + offset_x, p['y'] + offset_y
                batch.draw(dot, px, py, 4, 4, color=(200, 255, 255, alpha), blend=BLEND_ADDITIVE)
                batch.draw(soft, px, py, 8, 8, color=(100, 200, 255, alpha // 2), blend=BLEND_ADDITIVE)

        name = self.get_texture_name()
        if not renderer.has_texture(name):
            if self.image is None:
                self._load_image()
            renderer.load_texture(name, self.image or self._create_fallback_image())
        region = renderer.get_region(name)
        batch.draw(region, cx, cy, self.width, self.height, rotation=-self.angle)