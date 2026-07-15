# main.py
import pygame
import sys
import os
from utils.path_utils import resource_path
from core.state_manager import StateManager, MenuState, PlayState, PauseState, GameOverState, SettingsState, LevelSelectState
from core.event_bus import EventBus
from core.settings import GameSettings

class Game:
    """Главный класс игры"""
    
    def __init__(self):
        pygame.init()
        
        # Загружаем настройки
        self.settings = GameSettings()
        
        # Настройки экрана
        self.screen_width = 1280
        self.screen_height = 720
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Zombie Tower Defense")
        
        # Часы для FPS
        self.clock = pygame.time.Clock()
        self.running = True
        self.dt = 0
        
        # Создаём папки
        os.makedirs(resource_path("saves"), exist_ok=True)
        os.makedirs(resource_path("data/configs"), exist_ok=True)
        os.makedirs(resource_path("assets/sounds"), exist_ok=True)
        
        # Создаём состояния
        self.state_manager = StateManager()
        self.state_manager.add_state('MENU', MenuState(self))
        self.state_manager.add_state('PLAYING', PlayState(self))
        self.state_manager.add_state('PAUSED', PauseState(self))
        self.state_manager.add_state('GAME_OVER', GameOverState(self))
        self.state_manager.add_state('SETTINGS', SettingsState(self))
        self.state_manager.add_state('LEVEL_SELECT', LevelSelectState(self))
        self.state_manager.change_state('MENU')
    
    def run(self):
        """Главный игровой цикл"""
        while self.running:
            self.dt = min(self.clock.tick(60) / 1000.0, 0.05)
            
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                    self.quit()
                    return
            
            current_state = self.state_manager.get_current_state()
            if current_state:
                current_state.handle_events(events)
                current_state.update(self.dt)
                current_state.draw(self.screen)
            
            pygame.display.flip()
    
    def quit(self):
        """Очистка перед выходом"""
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()