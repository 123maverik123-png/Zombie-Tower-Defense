# core/audio/channels.py
import pygame
from typing import Dict, Optional


class ChannelManager:
    """Управление аудиоканалами"""
    
    def __init__(self):
        # Резервируем каналы для loop-звуков (0 и 1)
        self._reserved_channels = [0, 1]
        self._loop_channels: Dict[str, pygame.mixer.Channel] = {}
        self._next_channel = 2
        
        # Специальный канал для огнемёта (канал 0)
        self._flame_channel = None
    
    def get_free_channel(self) -> Optional[pygame.mixer.Channel]:
        """Получает свободный канал, исключая зарезервированные"""
        for i in range(self._next_channel, pygame.mixer.get_num_channels()):
            channel = pygame.mixer.Channel(i)
            if not channel.get_busy():
                return channel
        
        # Если все заняты — останавливаем первый доступный
        for i in range(self._next_channel, pygame.mixer.get_num_channels()):
            channel = pygame.mixer.Channel(i)
            channel.stop()
            return channel
        
        return None
    
    def get_reserved_channel(self, sound_id: str) -> Optional[pygame.mixer.Channel]:
        """Получает или создает зарезервированный канал для loop-звука"""
        if sound_id in self._loop_channels:
            channel = self._loop_channels[sound_id]
            if channel.get_busy():
                return channel
        
        # Ищем свободный зарезервированный канал
        for i in self._reserved_channels:
            channel = pygame.mixer.Channel(i)
            if not channel.get_busy():
                self._loop_channels[sound_id] = channel
                return channel
        
        # Если все заняты — используем первый
        i = self._reserved_channels[0]
        channel = pygame.mixer.Channel(i)
        channel.stop()
        self._loop_channels[sound_id] = channel
        return channel
    
    def get_flame_channel(self) -> Optional[pygame.mixer.Channel]:
        """Возвращает канал для огнемёта (канал 0)"""
        if self._flame_channel is None:
            self._flame_channel = pygame.mixer.Channel(0)
        return self._flame_channel
    
    def stop_looped_sound(self, sound_id: str) -> bool:
        """Останавливает зацикленный звук"""
        if sound_id in self._loop_channels:
            try:
                channel = self._loop_channels[sound_id]
                channel.stop()
                del self._loop_channels[sound_id]
                return True
            except Exception as e:
                print(f"⚠️ Error stopping looped sound {sound_id}: {e}")
        return False
    
    def stop_all_loop_sounds(self):
        """Останавливает все зацикленные звуки"""
        for sound_id in list(self._loop_channels.keys()):
            self.stop_looped_sound(sound_id)
    
    def stop_all_channels(self):
        """Останавливает все каналы (кроме музыки)"""
        for i in range(pygame.mixer.get_num_channels()):
            try:
                channel = pygame.mixer.Channel(i)
                if channel.get_busy():
                    channel.stop()
            except:
                pass
        
        self._loop_channels.clear()
        self._flame_channel = None
    
    def reset_states(self):
        """Сбрасывает все состояния каналов"""
        self._loop_channels.clear()
        self._flame_channel = None
    
    def get_num_channels(self) -> int:
        return pygame.mixer.get_num_channels()