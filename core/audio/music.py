# core/audio/music.py
import pygame
import os
from typing import Optional


class MusicManager:
    """Управление фоновой музыкой"""
    
    def __init__(self):
        self.current_music: Optional[str] = None
        self.sounds_path = "assets/sounds/"
        self._settings = None
        self._music_volume = 1.0
        self._music_enabled = True
        self._master_volume = 1.0
    
    def _load_settings(self):
        """Ленивая загрузка настроек"""
        if self._settings is None:
            from core.settings import GameSettings
            self._settings = GameSettings()
            self._update_volumes()
    
    def _update_volumes(self):
        """Обновляет громкость музыки"""
        if self._settings:
            self._master_volume = self._settings.master_volume
            self._music_volume = self._settings.music_volume if self._settings.music_enabled else 0.0
            self._music_enabled = self._settings.music_enabled
        
        pygame.mixer.music.set_volume(self._music_volume * self._master_volume)
    
    def play(self, filename: str, loop: bool = True) -> bool:
        """Воспроизводит фоновую музыку.

        Идемпотентно: если этот трек уже играет — ничего не делает,
        музыка продолжается без прерывания. Перезапуск происходит
        только при смене трека (например, игра → главное меню).
        """
        self._load_settings()
        if not self._music_enabled:
            return False

        # Тот же трек уже играет — не перезапускаем
        if self.current_music == filename and pygame.mixer.music.get_busy():
            return True

        path = os.path.join(self.sounds_path, filename)
        if not os.path.exists(path):
            print(f"⚠️ Music file not found: {path}")
            return False

        try:
            self.stop()
            pygame.mixer.music.load(path)
            self._update_volumes()
            pygame.mixer.music.play(-1 if loop else 0)
            self.current_music = filename
            return True
        except Exception as e:
            print(f"⚠️ Error playing music {filename}: {e}")
            return False
    
    def stop(self):
        """Останавливает музыку"""
        pygame.mixer.music.stop()
        self.current_music = None
    
    def pause(self):
        """Приостанавливает музыку"""
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
    
    def unpause(self):
        """Возобновляет музыку"""
        pygame.mixer.music.unpause()
    
    def is_playing(self) -> bool:
        """Проверяет, играет ли музыка"""
        return pygame.mixer.music.get_busy()
    
    def get_current_music(self) -> Optional[str]:
        return self.current_music
    
    def set_volume(self, volume: float):
        """Устанавливает громкость музыки"""
        self._music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self._music_volume * self._master_volume)
    
    def update_volumes(self):
        """Обновляет громкость"""
        self._update_volumes()
    
    def toggle_music(self):
        """Включает/выключает музыку"""
        self._load_settings()
        if self._settings:
            self._settings.set("music_enabled", not self._music_enabled)
            self._update_volumes()
            if not self._music_enabled:
                self.stop()
    
    def is_fading(self) -> bool:
        return False