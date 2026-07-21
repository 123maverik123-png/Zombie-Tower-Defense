# utils/sprite_loader.py
import pygame
import os
import re
from typing import Dict, List, Optional, Tuple


class SpriteLoader:
    """Загружает и нарезает спрайт-листы и отдельные кадры"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.cache = {}
        self.images_path = "assets/images/"
        self.sprites_path = "assets/sprites/"
        os.makedirs(self.images_path, exist_ok=True)
        os.makedirs(self.sprites_path, exist_ok=True)
        
        self.scale_factor = 0.4
        self.tile_size_reference = 65
        
        self._updating = False
    
    def set_scale_from_tile_size(self, tile_size: int):
        """Устанавливает масштаб на основе размера тайла"""
        if tile_size <= 0:
            return
        
        if self._updating:
            return
        
        self._updating = True
        try:
            new_scale = (tile_size / self.tile_size_reference) * 0.7
            if abs(new_scale - self.scale_factor) < 0.01:
                return
            
            self.scale_factor = new_scale
            self.cache.clear()
            print(f"🔧 Sprite scale set to: {self.scale_factor:.2f} (tile: {tile_size}px)")
        finally:
            self._updating = False
    
    def load_animations_from_folder(self, folder_name: str, frames_per_anim: int = 4, scale: float = None) -> Dict[str, List[pygame.Surface]]:
        """
        Загружает анимации из папки с отдельными спрайтами.
        
        Поддерживает два формата:
        1. Все кадры подряд: 0.png, 1.png, 2.png, ...
        2. По направлениям: down_0.png, up_0.png, left_0.png, right_0.png
        """
        if scale is None:
            scale = self.scale_factor
        
        folder_path = os.path.join(self.sprites_path, folder_name)
        
        if not os.path.exists(folder_path):
            print(f"❌ Folder not found: {folder_path}")
            return self._create_fallback_animations(int(64 * scale))
        
        print(f"🔄 Loading animations from folder: {folder_name}")
        
        # Находим все PNG и JPG файлы
        valid_extensions = ('.png', '.PNG', '.jpg', '.JPG', '.jpeg', '.JPEG')
        files = []
        for f in os.listdir(folder_path):
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                files.append(f)
        
        if not files:
            print(f"   ❌ No image files found in {folder_path}")
            return self._create_fallback_animations(int(64 * scale))
        
        # ✅ ПРОВЕРЯЕМ: есть ли в именах направления (down, up, left, right)
        has_directions = False
        for f in files:
            if re.search(r'(down|up|left|right)', f.lower()):
                has_directions = True
                break
        
        if has_directions:
            # Загружаем по направлениям
            return self._load_directional_animations(folder_path, files, frames_per_anim, scale)
        else:
            # Загружаем все кадры подряд (одинаковые для всех направлений)
            return self._load_simple_animations(folder_path, files, frames_per_anim, scale)
    
    def _load_directional_animations(self, folder_path: str, files: List[str], frames_per_anim: int, scale: float) -> Dict[str, List[pygame.Surface]]:
        """Загружает анимации с разделением по направлениям"""
        directions = ['down', 'up', 'left', 'right']
        animations = {d: [] for d in directions}
        
        for direction in directions:
            # Ищем файлы для этого направления
            dir_files = [f for f in files if direction in f.lower()]
            dir_files.sort()
            
            if not dir_files:
                print(f"   ⚠️ No files for direction: {direction}")
                # Создаём заглушку
                placeholder = self._create_placeholder(int(64 * scale))
                animations[direction] = [placeholder] * frames_per_anim
                continue
            
            # Загружаем кадры
            frames = []
            for filename in dir_files[:frames_per_anim]:
                try:
                    filepath = os.path.join(folder_path, filename)
                    frame = pygame.image.load(filepath).convert_alpha()
                    
                    if scale != 1.0 and scale > 0:
                        new_w = int(frame.get_width() * scale)
                        new_h = int(frame.get_height() * scale)
                        if new_w > 0 and new_h > 0:
                            frame = pygame.transform.scale(frame, (new_w, new_h))
                    
                    frames.append(frame)
                except Exception as e:
                    print(f"   ❌ Error loading {filename}: {e}")
            
            # Добавляем недостающие кадры
            while len(frames) < frames_per_anim:
                if frames:
                    frames.append(frames[-1].copy())
                else:
                    placeholder = self._create_placeholder(int(64 * scale))
                    frames.append(placeholder)
            
            animations[direction] = frames
            print(f"   ✅ {direction}: {len(frames)} frames loaded")
        
        return animations
    
    def _load_simple_animations(self, folder_path: str, files: List[str], frames_per_anim: int, scale: float) -> Dict[str, List[pygame.Surface]]:
        """Загружает все кадры подряд (без разделения по направлениям)"""
        # Сортируем файлы по числу в имени
        def extract_number(filename):
            numbers = re.findall(r'\d+', filename)
            return int(numbers[-1]) if numbers else 0
        
        files = sorted(files, key=extract_number)
        
        frames = []
        for filename in files[:frames_per_anim]:
            try:
                filepath = os.path.join(folder_path, filename)
                frame = pygame.image.load(filepath).convert_alpha()
                
                if scale != 1.0 and scale > 0:
                    new_w = int(frame.get_width() * scale)
                    new_h = int(frame.get_height() * scale)
                    if new_w > 0 and new_h > 0:
                        frame = pygame.transform.scale(frame, (new_w, new_h))
                
                frames.append(frame)
            except Exception as e:
                print(f"   ❌ Error loading {filename}: {e}")
        
        while len(frames) < frames_per_anim:
            if frames:
                frames.append(frames[-1].copy())
            else:
                placeholder = self._create_placeholder(int(64 * scale))
                frames.append(placeholder)
        
        # Копируем одинаковые кадры во все направления
        animations = {
            'down': frames.copy(),
            'up': frames.copy(),
            'left': frames.copy(),
            'right': frames.copy()
        }
        
        print(f"   ✅ {len(frames)} frames loaded (same for all directions)")
        return animations
    
    def load_zombie_animations(self, sheet_name: str, sprite_size: int = 256, 
                                cols: int = 4, rows: int = 4) -> Dict[str, List[pygame.Surface]]:
        """Загружает анимации зомби из спрайт-листа"""
        sheet_path = os.path.join(self.images_path, sheet_name)
        
        if not os.path.exists(sheet_path):
            print(f"❌ Sprite sheet not found: {sheet_path}")
            size = int(sprite_size * self.scale_factor)
            return self._create_fallback_animations(size)
        
        try:
            sheet = pygame.image.load(sheet_path).convert_alpha()
            print(f"🔄 Loading zombie animations from sheet: {sheet_name}")
            
            directions = ['down', 'up', 'left', 'right']
            animations = {}
            
            sheet_width = sheet.get_width()
            sheet_height = sheet.get_height()
            
            actual_sprite_size = sheet_width // cols
            
            for row, direction in enumerate(directions):
                if row >= rows:
                    break
                
                frames = []
                for col in range(cols):
                    x = col * actual_sprite_size
                    y = row * actual_sprite_size
                    
                    frame = sheet.subsurface((x, y, actual_sprite_size, actual_sprite_size)).copy()
                    
                    if self.scale_factor != 1.0:
                        new_w = int(actual_sprite_size * self.scale_factor)
                        new_h = int(actual_sprite_size * self.scale_factor)
                        if new_w > 0 and new_h > 0:
                            frame = pygame.transform.scale(frame, (new_w, new_h))
                    
                    frames.append(frame)
                
                animations[direction] = frames
                print(f"   ✅ {direction}: {len(frames)} frames loaded")
            
            return animations
            
        except Exception as e:
            print(f"❌ Error loading sprite sheet: {e}")
            size = int(sprite_size * self.scale_factor)
            return self._create_fallback_animations(size)
    
    def _create_placeholder(self, size: int) -> pygame.Surface:
        """Создаёт заглушку для отсутствующего спрайта"""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        surf.fill((255, 0, 255, 200))
        pygame.draw.circle(surf, (0, 255, 0), (size//2, size//2), size//3)
        pygame.draw.rect(surf, (255, 255, 0), (2, 2, size-4, size-4), 2)
        try:
            font = pygame.font.Font(None, size//2)
            text = font.render("?", True, (255, 255, 255))
            surf.blit(text, (size//2 - text.get_width()//2, size//2 - text.get_height()//2))
        except Exception:
            pass
        return surf
    
    def _create_fallback_animations(self, sprite_size: int) -> Dict[str, List[pygame.Surface]]:
        """Создаёт анимации-заглушки"""
        placeholder = self._create_placeholder(sprite_size)
        return {
            'down': [placeholder] * 4,
            'up': [placeholder] * 4,
            'left': [placeholder] * 4,
            'right': [placeholder] * 4,
        }
    
    def set_scale(self, scale: float):
        """Устанавливает масштаб для всех спрайтов"""
        self.scale_factor = scale
        self.cache.clear()
        print(f"🔧 Scale set to: {scale}")
    
    def load_image(self, path: str, scale: Optional[Tuple[int, int]] = None) -> Optional[pygame.Surface]:
        """Загружает отдельное изображение"""
        full_path = os.path.join(self.images_path, path)
        if not os.path.exists(full_path):
            return None
        
        try:
            image = pygame.image.load(full_path).convert_alpha()
            if scale:
                image = pygame.transform.scale(image, scale)
            return image
        except Exception as e:
            print(f"❌ Error loading image {path}: {e}")
            return None
    
    def get_cached_animation(self, key: str) -> Optional[Dict[str, List[pygame.Surface]]]:
        """Получает анимацию из кэша"""
        return self.cache.get(key)
    
    def cache_animation(self, key: str, animation: Dict[str, List[pygame.Surface]]):
        """Сохраняет анимацию в кэш"""
        self.cache[key] = animation
    
    def load_fire_animation(self, scale: float = None) -> Dict[str, List[pygame.Surface]]:
        """
        Загружает анимацию огня из папки fire_sheet/
        Специальный метод для анимации огня
        """
        if scale is None:
            scale = self.scale_factor
        
        # Пробуем загрузить из папки fire_sheet
        folder_path = os.path.join(self.sprites_path, "fire_sheet")
        
        if os.path.exists(folder_path):
            # Проверяем, есть ли файлы
            files = [f for f in os.listdir(folder_path) if f.endswith(('.png', '.PNG', '.jpg', '.JPG'))]
            if files:
                return self.load_animations_from_folder("fire_sheet", len(files), scale)
        
        # Если папки нет — создаём заглушки
        print(f"⚠️ fire_sheet folder not found, using fallback")
        size = int(32 * scale)
        placeholder = self._create_placeholder(size)
        return {
            'down': [placeholder] * 9,
            'up': [placeholder] * 9,
            'left': [placeholder] * 9,
            'right': [placeholder] * 9,
        }