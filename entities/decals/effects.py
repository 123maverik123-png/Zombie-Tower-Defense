# entities/decals/effects.py
import pygame
import random
import math
from typing import Tuple


class DecalEffects:
    """Методы рисования различных эффектов декалей"""
    
    @staticmethod
    def draw_blood(surf: pygame.Surface, cx: int, cy: int, size: int, alpha: int, color: Tuple[int, int, int]):
        """Рисует кровавое пятно"""
        for radius in range(size, 2, -2):
            a = int(alpha * (radius / size) * random.uniform(0.6, 1.0))
            r = int(color[0] * random.uniform(0.7, 1.1))
            g = int(color[1] * random.uniform(0.5, 1.0))
            b = int(color[2] * random.uniform(0.5, 1.0))
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            
            offset_x = random.uniform(-3, 3) * (1 - radius / size)
            offset_y = random.uniform(-3, 3) * (1 - radius / size)
            
            pygame.draw.circle(surf, (r, g, b, a), 
                             (int(cx + offset_x), int(cy + offset_y)), radius)
        
        for _ in range(5 + random.randint(0, 5)):
            radius = random.randint(2, 6)
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(size * 0.3, size * 1.2)
            x = cx + math.cos(angle) * dist
            y = cy + math.sin(angle) * dist
            a = random.randint(50, 150)
            pygame.draw.circle(surf, (color[0], color[1], color[2], a), 
                             (int(x), int(y)), radius)
    
    @staticmethod
    def draw_smoke(surf: pygame.Surface, cx: int, cy: int, size: int, alpha: int):
        """Рисует дым"""
        for radius in range(size, 2, -3):
            a = int(alpha * (radius / size) * random.uniform(0.4, 0.8))
            gray = random.randint(80, 180)
            offset_x = random.uniform(-5, 5) * (1 - radius / size)
            offset_y = random.uniform(-5, 5) * (1 - radius / size)
            pygame.draw.circle(surf, (gray, gray, gray, a), 
                             (int(cx + offset_x), int(cy + offset_y)), radius)
    
    @staticmethod
    def draw_crack(surf: pygame.Surface, cx: int, cy: int, size: int, alpha: int, color: Tuple[int, int, int]):
        """Рисует трещину"""
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
            pygame.draw.line(surf, (*color, alpha), 
                           points[i], points[i+1], width)
    
    @staticmethod
    def draw_spark(surf: pygame.Surface, cx: int, cy: int, size: int):
        """Рисует искру"""
        pygame.draw.circle(surf, (255, 255, 255, 255), (cx, cy), size // 2)
        pygame.draw.circle(surf, (255, 255, 200, 200), (cx, cy), size)
        
        for angle in range(0, 360, 20):
            rad = math.radians(angle)
            length = random.uniform(size * 0.3, size * 0.9)
            end_x = cx + math.cos(rad) * length
            end_y = cy + math.sin(rad) * length
            a = random.randint(50, 150)
            pygame.draw.line(surf, (255, 255, 200, a), 
                           (cx, cy), (end_x, end_y), 2)
    
    @staticmethod
    def draw_fire(surf: pygame.Surface, cx: int, cy: int, size: int, alpha: int):
        """Рисует огонь (заглушка для анимированных декалей)"""
        for radius in range(size, 2, -2):
            a = int(alpha * (radius / size) * random.uniform(0.5, 0.9))
            r = random.randint(200, 255)
            g = random.randint(50, 150)
            b = random.randint(0, 30)
            offset_x = random.uniform(-4, 4) * (1 - radius / size)
            offset_y = random.uniform(-4, 4) * (1 - radius / size)
            pygame.draw.circle(surf, (r, g, b, a), 
                             (int(cx + offset_x), int(cy + offset_y)), radius)
    
    @staticmethod
    def draw_acid(surf: pygame.Surface, cx: int, cy: int, size: int, alpha: int):
        """Рисует кислотное пятно"""
        for radius in range(size, 2, -2):
            a = int(alpha * (radius / size) * random.uniform(0.5, 0.9))
            r = random.randint(30, 80)
            g = random.randint(150, 255)
            b = random.randint(30, 80)
            offset_x = random.uniform(-3, 3) * (1 - radius / size)
            offset_y = random.uniform(-3, 3) * (1 - radius / size)
            pygame.draw.circle(surf, (r, g, b, a), 
                             (int(cx + offset_x), int(cy + offset_y)), radius)
        
        for _ in range(3 + random.randint(0, 3)):
            radius = random.randint(2, 5)
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(0, size * 0.6)
            x = cx + math.cos(angle) * dist
            y = cy + math.sin(angle) * dist
            a = random.randint(50, 150)
            pygame.draw.circle(surf, (100, 255, 100, a), (int(x), int(y)), radius)
            pygame.draw.circle(surf, (50, 200, 50, a // 2), (int(x), int(y)), radius * 2, 1)
    
    @staticmethod
    def draw_water_splash(surf: pygame.Surface, cx: int, cy: int, size: int, alpha: int):
        """Рисует водяной всплеск"""
        for radius in range(size, 2, -2):
            a = int(alpha * (radius / size) * random.uniform(0.5, 0.9))
            r = random.randint(30, 100)
            g = random.randint(130, 200)
            b = random.randint(200, 255)
            offset_x = random.uniform(-3, 3) * (1 - radius / size)
            offset_y = random.uniform(-3, 3) * (1 - radius / size)
            pygame.draw.circle(surf, (r, g, b, a), 
                             (int(cx + offset_x), int(cy + offset_y)), radius)
        
        for _ in range(4 + random.randint(0, 4)):
            radius = random.randint(2, 5)
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(size * 0.4, size * 1.1)
            x = cx + math.cos(angle) * dist
            y = cy + math.sin(angle) * dist
            a = random.randint(80, 180)
            pygame.draw.circle(surf, (100, 200, 255, a), (int(x), int(y)), radius)
            pygame.draw.circle(surf, (150, 220, 255, a // 2), (int(x), int(y)), radius * 2, 1)
    
    @staticmethod
    def draw_ice_crystal(surf: pygame.Surface, cx: int, cy: int, size: int, alpha: int):
        """Рисует ледяной кристалл"""
        for radius in range(size, 2, -2):
            a = int(alpha * (radius / size) * random.uniform(0.5, 0.9))
            r = random.randint(180, 230)
            g = random.randint(220, 255)
            b = random.randint(230, 255)
            offset_x = random.uniform(-3, 3) * (1 - radius / size)
            offset_y = random.uniform(-3, 3) * (1 - radius / size)
            pygame.draw.circle(surf, (r, g, b, a), 
                             (int(cx + offset_x), int(cy + offset_y)), radius)
        
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            length = random.uniform(size * 0.3, size * 0.8)
            end_x = cx + math.cos(rad) * length
            end_y = cy + math.sin(rad) * length
            a = random.randint(100, 200)
            pygame.draw.line(surf, (200, 240, 255, a), 
                           (cx, cy), (end_x, end_y), random.randint(1, 3))
        
        for _ in range(3 + random.randint(0, 3)):
            radius = random.randint(2, 4)
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(size * 0.2, size * 0.7)
            x = cx + math.cos(angle) * dist
            y = cy + math.sin(angle) * dist
            a = random.randint(100, 200)
            for i in range(3):
                a_angle = angle + math.radians(i * 120)
                end_x = x + math.cos(a_angle) * radius * 2
                end_y = y + math.sin(a_angle) * radius * 2
                pygame.draw.line(surf, (200, 240, 255, a), 
                               (x, y), (end_x, end_y), 1)
    
    @staticmethod
    def draw_fallback(surf: pygame.Surface, cx: int, cy: int, size: int, alpha: int, color: Tuple[int, int, int]):
        """Запасной вариант"""
        pygame.draw.circle(surf, (*color, alpha), (cx, cy), size)