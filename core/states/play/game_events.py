# core/states/play/game_events.py
from services.profile_manager import ProfileManager
from services.save_system import SaveSystem


class PlayStateGameEvents:
    """Управление событиями Game Over и Victory"""
    
    def __init__(self, state):
        self.state = state
    
    def check_game_over(self):
        """Проверяет, не закончилась ли игра поражением"""
        state = self.state
        
        if state.player.lives <= 0:
            state.player.lives = 0
            state.game_over = True
            
            # Останавливаем звук огнемёта
            state.audio.flame_force_stop()
            state.audio.play_sound("game_over")
            self._save_game_over_data()
            
            # Hardcore режим
            pm = ProfileManager()
            if pm.is_hardcore():
                pm.reset_hardcore_progress()
                print("💀 HARDCORE: Progress reset to Level 1!")
            
            # Переход в Game Over
            from core.states.game_over_state import GameOverState
            state.game.state_manager.add_state('GAME_OVER', GameOverState(state.game))
            state.game.state_manager.change_state('GAME_OVER')
    
    def check_victory(self):
        """Проверяет, не завершён ли уровень победой"""
        state = self.state
        
        if state.wave_manager.is_all_waves_complete() and len(state.enemies) == 0:
            if state._is_saving:
                return
            state._is_saving = True
            state.level_complete = True
            
            # Останавливаем звук огнемёта
            state.audio.flame_force_stop()
            
            # Сохраняем прогресс
            pm = ProfileManager()
            profile = pm.get_current_profile()
            
            if profile:
                profile.complete_level(state.level_number)
                profile.current_level = state.level_number + 1
                if profile.current_level > 50:
                    profile.current_level = 50
                pm.save_profile(profile)
                print(f"✅ Level {state.level_number} completed! Unlocked: {profile.unlocked_level}")
            else:
                save = SaveSystem()
                level_data = save.load_level_data()
                level_data.complete_level(state.level_number)
                save.save_level_data(level_data)
                print(f"⚠️ Using fallback save system for level {state.level_number}")
            
            state._is_saving = False
    
    def _save_game_over_data(self):
        """Сохраняет данные для экрана Game Over"""
        state = self.state
        state.game._game_over_data = {
            'level': state.level_number,
            'waves': state.player.stats.get('waves_survived', 0),
            'kills': state.player.stats.get('total_kills', 0),
            'gold': state.player.gold
        }
        print(f"💾 Game Over data saved: Level {state.level_number}, Kills: {state.player.stats.get('total_kills', 0)}")
    
    def check_music(self):
        """Проверяет, играет ли музыка, и перезапускает если нужно"""
        state = self.state
        if not state.audio.is_music_playing() and state.audio.settings.music_enabled:
            if not state.audio.is_fading():
                state.audio.play_music("game_theme.wav")