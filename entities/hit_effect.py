# entities/hit_effect.py
import pygame
import math
import random
from core.iso import world_to_screen

class HitEffect:
    """Эффект попадания на враге"""
    
    TYPES = {
        'sniper': {
            'color': (255, 255, 255),
            'particle_count': 20,
            'particle_size': 4,
            'duration': 0.3,
            'glow_radius': 30
        },
        'turret': {
            'color': (255, 220, 50),
            'particle_count': 12,
            'particle_size': 3,
            'duration': 0.2,
            'glow_radius': 20
        },
        'flamethrower': {
            'color': (255, 150, 50),
            'particle_count': 15,
            'particle_size': 5,
            'duration': 0.25,
            'glow_radius': 25
        },
        'electric': {
            'color': (100, 200, 255),
            'particle_count': 25,
            'particle_size': 3,
            'duration': 0.3,
            'glow_radius': 35
        },
        'acid': {
            'color': (50, 255, 50),
            'particle_count': 12,
            'particle_size': 4,
            'duration': 0.4,
            'glow_radius': 20
        },
        'water': {
            'color': (50, 150, 255),
            'particle_count': 15,
            'particle_size': 4,
            'duration': 0.3,
            'glow_radius': 25
        },
        'freeze': {
            'color': (200, 240, 255),
            'particle_count': 20,
            'particle_size': 3,
            'duration': 0.4,
            'glow_radius': 30
        },
        'rocket': {
            'color': (255, 200, 50),
            'particle_count': 35,
            'particle_size': 6,
            'duration': 0.6,
            'glow_radius': 55
        },
        'explosive': {
            'color': (255, 150, 50),
            'particle_count': 40,
            'particle_size': 7,
            'duration': 0.5,
            'glow_radius': 60
        }
    }
    
    def __init__(self, x: float, y: float, effect_type: str = 'turret', scale: float = 1.0, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z  # подъём над землёй в экранных пикселях (напр. высота дула башни)
        self.type = effect_type
        self.config = self.TYPES.get(effect_type, self.TYPES['turret'])
        self.scale = scale
        
        self.duration = self.config['duration']
        self.max_duration = self.duration
        self.alive = True
        
        self.particles = []
        self._create_particles()
        
        self.glow_radius = int(self.config['glow_radius'] * scale)
        self.glow_alpha = 255
    
    def _create_particles(self):
        """Создаёт частицы для эффекта"""
        color = self.config['color']
        count = int(self.config['particle_count'] * self.scale)
        size = self.config['particle_size'] * self.scale
        
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 200)
            distance = random.uniform(5, 20)
            
            self.particles.append({
                'x': self.x + math.cos(angle) * distance,
                'y': self.y + math.sin(angle) * distance,
                'vx': math.cos(angle) * speed * random.uniform(0.5, 1.5),
                'vy': math.sin(angle) * speed * random.uniform(0.5, 1.5),
                'size': random.uniform(size * 0.5, size * 1.5),
                'life': random.uniform(0.3, 0.8),
                'max_life': random.uniform(0.3, 0.8),
                'color': (
                    int(color[0] * random.uniform(0.7, 1.3)),
                    int(color[1] * random.uniform(0.7, 1.3)),
                    int(color[2] * random.uniform(0.7, 1.3))
                ),
                'trail': []
            })
    
    def update(self, dt: float):
        """Обновляет эффект"""
        self.duration -= dt
        
        if self.duration <= 0:
            self.alive = False
            return
        
        progress = 1 - (self.duration / self.max_duration)
        self.glow_alpha = int(255 * (1 - progress))
        
        for particle in self.particles[:]:
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            particle['vy'] += 50 * dt
            particle['life'] -= dt
            
            if len(particle.get('trail', [])) < 5:
                particle.setdefault('trail', []).append((particle['x'], particle['y']))
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def draw(self, screen: pygame.Surface, offset_x: int = 0, offset_y: int = 0):
        """Рисует эффект"""
        if not self.alive:
            return
        
        sx, sy = world_to_screen(self.x, self.y)
        x = sx + offset_x
        y = sy + offset_y - self.z

        # Рисуем свечение
        if self.glow_alpha > 10:
            glow_size = self.glow_radius * 2
            glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            glow_surf.fill((0, 0, 0, 0))
            
            for r in range(int(self.glow_radius), 0, -2):
                alpha = int(self.glow_alpha * (r / self.glow_radius) * 0.3)
                temp_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                temp_surf.fill((0, 0, 0, 0))
                pygame.draw.circle(temp_surf, self.config['color'], 
                                 (self.glow_radius, self.glow_radius), r)
                temp_surf.set_alpha(alpha)
                glow_surf.blit(temp_surf, (0, 0))
            
            screen.blit(glow_surf, (x - self.glow_radius, y - self.glow_radius))
        
        # Рисуем частицы
        for particle in self.particles:
            life_ratio = particle['life'] / particle['max_life']
            alpha = int(255 * life_ratio)
            
            trail = particle.get('trail', [])
            if len(trail) > 1:
                for i in range(len(trail) - 1):
                    trail_alpha = int(alpha * (i / len(trail)) * 0.3)
                    trail_color = (
                        int(particle['color'][0] * trail_alpha / 255),
                        int(particle['color'][1] * trail_alpha / 255),
                        int(particle['color'][2] * trail_alpha / 255)
                    )
                    pygame.draw.line(screen, trail_color,
                                   (trail[i][0] + offset_x, trail[i][1] + offset_y - self.z),
                                   (trail[i+1][0] + offset_x, trail[i+1][1] + offset_y - self.z), 1)
            
            size = int(particle['size'] * life_ratio)
            if size > 1:
                particle_size = size * 2 + 4
                particle_surf = pygame.Surface((particle_size, particle_size), pygame.SRCALPHA)
                particle_surf.fill((0, 0, 0, 0))
                
                base_color = (
                    max(0, min(255, particle['color'][0])),
                    max(0, min(255, particle['color'][1])),
                    max(0, min(255, particle['color'][2]))
                )
                
                pygame.draw.circle(particle_surf, base_color, (size + 2, size + 2), size)
                particle_surf.set_alpha(alpha)
                
                if size > 2:
                    inner_surf = pygame.Surface((particle_size, particle_size), pygame.SRCALPHA)
                    inner_surf.fill((0, 0, 0, 0))
                    pygame.draw.circle(inner_surf, (255, 255, 255), (size + 2, size + 2), size // 2)
                    inner_surf.set_alpha(min(alpha, 100))
                    particle_surf.blit(inner_surf, (0, 0))
                
                screen.blit(particle_surf, (particle['x'] + offset_x - size - 2,
                                           particle['y'] + offset_y - self.z - size - 2))

    def draw_batch(self, renderer, offset_x: int = 0, offset_y: int = 0):
        """Рисует эффект через GPU-батч (свечение и частицы — аддитивно)"""
        if not self.alive:
            return
        from core.opengl.batch import BLEND_ADDITIVE
        batch = renderer.batch
        soft = renderer.get_region('__soft__')
        dot = renderer.get_region('__dot__')

        sx, sy = world_to_screen(self.x, self.y)
        x = sx + offset_x
        y = sy + offset_y
        color = self.config['color']

        if self.glow_alpha > 10:
            d = self.glow_radius * 2
            batch.draw(soft, x, y, d, d,
                       color=(*color, int(self.glow_alpha * 0.6)), blend=BLEND_ADDITIVE)

        for particle in self.particles:
            life_ratio = particle['life'] / particle['max_life']
            alpha = int(255 * life_ratio)

            trail = particle.get('trail', [])
            if len(trail) > 1:
                for i in range(len(trail) - 1):
                    trail_alpha = int(alpha * (i / len(trail)) * 0.3)
                    t0x, t0y = world_to_screen(trail[i][0], trail[i][1])
                    t1x, t1y = world_to_screen(trail[i + 1][0], trail[i + 1][1])
                    batch.draw_line(t0x + offset_x, t0y + offset_y - self.z,
                                    t1x + offset_x, t1y + offset_y - self.z,
                                    1, (*particle['color'], trail_alpha), blend=BLEND_ADDITIVE)

            size = int(particle['size'] * life_ratio)
            if size > 1:
                psx, psy = world_to_screen(particle['x'], particle['y'])
                px = psx + offset_x
                py = psy + offset_y - self.z
                c = particle['color']
                base_color = (max(0, min(255, c[0])), max(0, min(255, c[1])),
                              max(0, min(255, c[2])), alpha)
                batch.draw(dot, px, py, size * 2, size * 2,
                           color=base_color, blend=BLEND_ADDITIVE)
                if size > 2:
                    batch.draw(dot, px, py, size, size,
                               color=(255, 255, 255, min(alpha, 100)), blend=BLEND_ADDITIVE)