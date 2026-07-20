# core/states/play/sound_control.py


class PlayStateSoundControl:
    """Управление звуками для PlayState"""
    
    def __init__(self, state):
        self.state = state
    
    def reset_all_tower_sounds(self):
        """Сбрасывает состояние звуков всех башен (для паузы)"""
        state = self.state
        
        # Останавливаем звук огнемёта через AudioManager
        state.audio.flame_reset()
        
        # Сбрасываем состояние всех башен
        for tower in state.towers:
            if hasattr(tower, 'reset_flame_sound_state'):
                tower.reset_flame_sound_state()
        
        print("🔊 All tower sounds reset")
    
    def stop_all_sfx(self):
        """Останавливает все звуки"""
        state = self.state
        state.audio.flame_force_stop()
        state.audio.stop_all_sfx()
        self.reset_all_tower_sounds()
        print("🔇 PlayState SFX stopped")