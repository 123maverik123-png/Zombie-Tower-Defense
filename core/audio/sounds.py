# core/audio/sounds.py
import pygame
import os
from typing import Dict, Optional
from .channels import ChannelManager


class SoundManager:
    """Управление звуковыми эффектами (SFX)"""
    
    def __init__(self, channel_manager: ChannelManager):
        self.channel_manager = channel_manager
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.sounds_path = "assets/sounds/"
        self._settings = None
        self._master_volume = 1.0
        self._sfx_volume = 1.0
        self._sound_enabled = True
        
        os.makedirs(self.sounds_path, exist_ok=True)
        self._load_sounds()
    
    def _load_settings(self):
        """Ленивая загрузка настроек"""
        if self._settings is None:
            from core.settings import GameSettings
            self._settings = GameSettings()
            self._update_volumes()
    
    def _update_volumes(self):
        """Обновляет громкость всех звуков"""
        if self._settings:
            self._master_volume = self._settings.master_volume if self._settings.sound_enabled else 0.0
            self._sfx_volume = self._settings.sfx_volume if self._settings.sound_enabled else 0.0
            self._sound_enabled = self._settings.sound_enabled
        
        for sound in self.sounds.values():
            if sound:
                sound.set_volume(self._master_volume * self._sfx_volume)
    
    def _load_sounds(self):
        """Загружает все звуки из папки"""
        sound_files = {
            'shoot': 'shoot.wav',
            'death': 'death.wav',
            'tower_build': 'tower_build.wav',
            'game_over': 'game_over.wav',
            'wave_complete': 'wave_complete.wav',
            'button_click': 'button_click.wav',
            'enemy_spawn': 'enemy_spawn.wav',
            'water_shoot': 'water_shoot.wav',
            'freeze_shoot': 'freeze_shoot.wav',
            'acid_shoot': 'acid_shoot.wav',
            'rocket_shoot': 'rocket_shoot.wav',
            'pvo_shoot': 'pvo_shoot.wav',
            'water_hit': 'water_hit.wav',
            'freeze_hit': 'freeze_hit.wav',
            'acid_hit': 'acid_hit.wav',
            'rocket_hit': 'rocket_hit.wav',
            'flame_loop': 'flame_loop.wav',
            'flame_start': 'flame_start.wav',
            'flame_stop': 'flame_stop.wav',
        }
        
        for sound_id, filename in sound_files.items():
            path = os.path.join(self.sounds_path, filename)
            try:
                if os.path.exists(path):
                    self.sounds[sound_id] = pygame.mixer.Sound(path)
                else:
                    self.sounds[sound_id] = None
            except Exception as e:
                print(f"⚠️ Error loading sound {sound_id}: {e}")
                self.sounds[sound_id] = None
    
    def get_sound(self, sound_id: str) -> Optional[pygame.mixer.Sound]:
        """Возвращает звук по ID"""
        return self.sounds.get(sound_id)
    
    def play(self, sound_id: str, volume_override: Optional[float] = None, loops: int = 0) -> bool:
        """Воспроизводит звук"""
        self._load_settings()
        if not self._sound_enabled:
            return False
        
        sound = self.sounds.get(sound_id)
        if not sound:
            return False
        
        try:
            if volume_override is not None:
                sound.set_volume(self._master_volume * self._sfx_volume * volume_override)
            else:
                sound.set_volume(self._master_volume * self._sfx_volume)
            
            channel = self.channel_manager.get_free_channel()
            if channel:
                channel.play(sound, loops=loops)
                return True
            else:
                sound.play(loops=loops)
                return True
        except Exception as e:
            print(f"⚠️ Error playing sound {sound_id}: {e}")
            return False
    
    def play_looped(self, sound_id: str, volume_override: Optional[float] = None) -> bool:
        """Воспроизводит зацикленный звук"""
        self._load_settings()
        if not self._sound_enabled:
            return False
        
        if self.is_playing(sound_id):
            return True
        
        sound = self.sounds.get(sound_id)
        if not sound:
            return False
        
        try:
            if volume_override is not None:
                sound.set_volume(self._master_volume * self._sfx_volume * volume_override)
            else:
                sound.set_volume(self._master_volume * self._sfx_volume)
            
            channel = self.channel_manager.get_reserved_channel(sound_id)
            if channel:
                channel.play(sound, loops=-1)
                return True
        except Exception as e:
            print(f"⚠️ Error playing looped sound {sound_id}: {e}")
        return False
    
    def stop_looped(self, sound_id: str) -> bool:
        """Останавливает зацикленный звук"""
        return self.channel_manager.stop_looped_sound(sound_id)
    
    def is_playing(self, sound_id: str) -> bool:
        """Проверяет, играет ли звук в данный момент"""
        sound = self.sounds.get(sound_id)
        if sound:
            for i in range(self.channel_manager.get_num_channels()):
                channel = pygame.mixer.Channel(i)
                if channel.get_sound() == sound and channel.get_busy():
                    return True
        return False
    
    def stop_all(self):
        """Останавливает все звуки"""
        self.channel_manager.stop_all_channels()
        self.channel_manager.reset_states()
    
    def update_volumes(self):
        """Обновляет громкость всех звуков"""
        self._update_volumes()
    
    def toggle_sound(self):
        """Включает/выключает звук"""
        self._load_settings()
        if self._settings:
            self._settings.set("sound_enabled", not self._sound_enabled)
            self._update_volumes()
    
    # === Глобальный звук огнемёта ===
    
    def flame_start(self):
        """Увеличивает счётчик активных огнемётов. Включает звук если нужно."""
        # Этот метод теперь в AudioManager, здесь заглушка
        pass
    
    def flame_stop(self):
        """Уменьшает счётчик активных огнемётов. Выключает звук если нужно."""
        pass
    
    def flame_reset(self):
        """Сбрасывает счётчик и выключает звук."""
        pass
    
    def flame_force_stop(self):
        """Принудительно выключает звук."""
        pass