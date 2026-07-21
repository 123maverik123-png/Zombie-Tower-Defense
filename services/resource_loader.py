# services/resource_loader.py
import pygame
import os
from typing import Dict, Optional

class ResourceLoader:
    """Кэширует загруженные ресурсы"""
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

        self.images: Dict[str, pygame.Surface] = {}
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.fonts: Dict[str, pygame.font.Font] = {}

        self.assets_path = "assets/"
        self.images_path = os.path.join(self.assets_path, "images")
        self.sounds_path = os.path.join(self.assets_path, "sounds")
        self.fonts_path = os.path.join(self.assets_path, "fonts")

        for path in [self.images_path, self.sounds_path, self.fonts_path]:
            os.makedirs(path, exist_ok=True)

    def load_image(self, name: str, scale: Optional[tuple] = None,
                   colorkey: Optional[tuple] = None) -> pygame.Surface:
        """Загружает изображение с кэшированием"""
        if name in self.images:
            image = self.images[name]
        else:
            path = os.path.join(self.images_path, name)
            try:
                image = pygame.image.load(path).convert_alpha()
            except pygame.error:
                print(f"Warning: Image {name} not found, creating placeholder")
                image = self._create_placeholder(50, 50, (100, 100, 100))

            if colorkey:
                image.set_colorkey(colorkey)

            self.images[name] = image

        if scale:
            return pygame.transform.scale(image, scale)
        return image.copy()

    def load_sound(self, name: str) -> Optional[pygame.mixer.Sound]:
        """Загружает звук с кэшированием"""
        if name in self.sounds:
            return self.sounds[name]

        path = os.path.join(self.sounds_path, name)
        try:
            sound = pygame.mixer.Sound(path)
            self.sounds[name] = sound
            return sound
        except pygame.error:
            print(f"Warning: Sound {name} not found")
            return None

    def load_font(self, name: str, size: int) -> pygame.font.Font:
        """Загружает шрифт"""
        cache_key = f"{name}_{size}"
        if cache_key in self.fonts:
            return self.fonts[cache_key]

        path = os.path.join(self.fonts_path, name)
        try:
            font = pygame.font.Font(path, size)
            self.fonts[cache_key] = font
            return font
        except Exception:
            font = pygame.font.Font(None, size)
            self.fonts[cache_key] = font
            return font

    def _create_placeholder(self, width, height, color) -> pygame.Surface:
        """Создаёт квадрат-заглушку"""
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        surf.fill(color)
        pygame.draw.rect(surf, (255, 255, 255), (0, 0, width, height), 2)
        return surf