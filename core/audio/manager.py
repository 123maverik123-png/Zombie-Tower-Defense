# core/audio/manager.py
import pygame
from typing import Optional

from .channels import ChannelManager
from .sounds import SoundManager
from .music import MusicManager
from utils.debug import dprint


class AudioManager:
    """Управление звуками и музыкой (главный класс)"""
    
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
        
        pygame.mixer.init()
        pygame.mixer.set_num_channels(32)
        
        # Создаём менеджеры
        self.channel_manager = ChannelManager()
        self.sound_manager = SoundManager(self.channel_manager)
        self.music_manager = MusicManager()
        
        # Для обратной совместимости
        self._settings = None
    
    def _load_settings(self):
        if self._settings is None:
            from core.settings import GameSettings
            self._settings = GameSettings()
    
    # ===== ОБЩИЕ МЕТОДЫ =====
    
    def update_volumes(self):
        """Обновляет громкость всех звуков и музыки"""
        self.sound_manager.update_volumes()
        self.music_manager.update_volumes()
    
    def stop_all_sfx(self):
        """Останавливает все звуковые эффекты (SFX), но НЕ трогает музыку"""
        self.flame_force_stop()
        self.sound_manager.stop_all()
        print("🔇 All SFX stopped (music untouched)")
    
    # ===== МЕТОДЫ ДЛЯ ЗВУКОВ =====
    
    @property
    def sounds(self):
        return self.sound_manager.sounds
    
    def play_sound(self, sound_id: str, volume_override: Optional[float] = None, loops: int = 0) -> bool:
        """Воспроизводит звук"""
        return self.sound_manager.play(sound_id, volume_override, loops)
    
    def play_looped_sound(self, sound_id: str, volume_override: Optional[float] = None) -> bool:
        """Воспроизводит зацикленный звук"""
        return self.sound_manager.play_looped(sound_id, volume_override)
    
    def stop_looped_sound(self, sound_id: str) -> bool:
        """Останавливает зацикленный звук"""
        return self.sound_manager.stop_looped(sound_id)
    
    def is_sound_playing(self, sound_id: str) -> bool:
        """Проверяет, играет ли звук"""
        return self.sound_manager.is_playing(sound_id)
    
    def toggle_sound(self):
        """Включает/выключает звук"""
        self._load_settings()
        if self._settings:
            self._settings.set("sound_enabled", not self.sound_manager._sound_enabled)
            self.sound_manager.update_volumes()
    
    # ===== МЕТОДЫ ДЛЯ МУЗЫКИ =====
    
    def play_music(self, filename: str, loop: bool = True) -> bool:
        """Воспроизводит фоновую музыку"""
        return self.music_manager.play(filename, loop)
    
    def stop_music(self):
        """Останавливает музыку"""
        self.music_manager.stop()
    
    def pause_music(self):
        """Приостанавливает музыку"""
        self.music_manager.pause()
    
    def unpause_music(self):
        """Возобновляет музыку"""
        self.music_manager.unpause()
    
    def is_music_playing(self) -> bool:
        """Проверяет, играет ли музыка"""
        return self.music_manager.is_playing()
    
    def get_current_music(self) -> Optional[str]:
        """Возвращает текущую музыку"""
        return self.music_manager.get_current_music()
    
    def set_music_volume(self, volume: float):
        """Устанавливает громкость музыки"""
        self.music_manager.set_volume(volume)
    
    def toggle_music(self):
        """Включает/выключает музыку"""
        self.music_manager.toggle_music()
    
    def is_fading(self) -> bool:
        return self.music_manager.is_fading()
    
    # ===== МЕТОДЫ ДЛЯ ОГНЕМЁТА (ГЛОБАЛЬНЫЙ ЗВУК) =====
    
    def _load_flame_sound(self):
        """Загружает звук огнемёта"""
        return self.sound_manager.get_sound('flame_loop')
    
    def _get_flame_channel(self):
        """Возвращает канал для огнемёта"""
        return self.channel_manager.get_flame_channel()
    
    def _set_flame_volume(self, sound):
        """Устанавливает громкость для огнемёта"""
        self._load_settings()
        if self._settings:
            master = self._settings.master_volume if self._settings.sound_enabled else 0.0
            sfx = self._settings.sfx_volume if self._settings.sound_enabled else 0.0
            if sound:
                sound.set_volume(master * sfx * 0.3)
    
    # Переменные для глобального звука огнемёта
    _flame_active_count = 0
    _flame_is_playing = False
    _flame_channel = None
    
    def flame_start(self):
        """Увеличивает счётчик активных огнемётов. Включает звук если нужно."""
        self._flame_active_count += 1
        self._update_flame_sound()
    
    def flame_stop(self):
        """Уменьшает счётчик активных огнемётов. Выключает звук если нужно."""
        self._flame_active_count = max(0, self._flame_active_count - 1)
        self._update_flame_sound()
    
    def flame_reset(self):
        """Сбрасывает счётчик и выключает звук (для паузы/перезагрузки)"""
        self._flame_active_count = 0
        self._stop_flame_sound()
    
    def flame_force_stop(self):
        """Принудительно выключает звук (для удаления всех башен)"""
        self._stop_flame_sound()
        self._flame_active_count = 0
    
    def _update_flame_sound(self):
        """Обновляет состояние звука огнемёта"""
        if self._flame_active_count > 0:
            self._start_flame_sound()
        else:
            self._stop_flame_sound()
    
    def _start_flame_sound(self):
        """Включает звук огнемёта"""
        if self._flame_is_playing:
            return
        
        self._load_settings()
        if not self._settings or not self._settings.sound_enabled:
            return
        
        sound = self._load_flame_sound()
        if not sound:
            return
        
        try:
            channel = self._get_flame_channel()
            channel.stop()
            
            self._set_flame_volume(sound)
            channel.play(sound, loops=-1)
            self._flame_is_playing = True
            dprint("🔥 Flame sound GLOBAL ON")
        except Exception as e:
            print(f"⚠️ Error starting flame sound: {e}")
    
    def _stop_flame_sound(self):
        """Выключает звук огнемёта"""
        if not self._flame_is_playing:
            return
        
        try:
            channel = self._get_flame_channel()
            if channel:
                channel.stop()
            self._flame_is_playing = False
            dprint("🔥 Flame sound GLOBAL OFF")
        except Exception as e:
            print(f"⚠️ Error stopping flame sound: {e}")
    
    def is_flame_playing(self) -> bool:
        """Проверяет, играет ли звук огнемёта"""
        return self._flame_is_playing
    
    def get_flame_count(self) -> int:
        """Возвращает количество активных огнемётов"""
        return self._flame_active_count
    
    # ===== МЕТОДЫ ДЛЯ СОВМЕСТИМОСТИ =====
    
    @property
    def settings(self):
        self._load_settings()
        return self._settings
    
    def reset_all_sound_states(self):
        """Сбрасывает все состояния звуков"""
        self.flame_reset()
        self.channel_manager.reset_states()
        dprint("🔄 All sound states reset")
    
    def stop_all_loop_sounds(self):
        """Останавливает все зацикленные звуки"""
        self.flame_force_stop()
        self.channel_manager.stop_all_loop_sounds()
        dprint("🔄 Stopped all loop sounds")