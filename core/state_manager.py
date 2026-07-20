# core/state_manager.py
from abc import ABC, abstractmethod

class State(ABC):
    """Базовый класс для всех состояний"""
    def __init__(self, game):
        self.game = game
        self.next_state = None
    
    @abstractmethod
    def handle_events(self, events):
        pass
    
    @abstractmethod
    def update(self, dt):
        pass
    
    @abstractmethod
    def draw(self, screen):
        if self._current_state:
            self._current_state.draw(screen)

class StateManager:
    """Управляет переключением между состояниями"""
    def __init__(self):
        self._states = {}
        self._current_state = None
    
    def add_state(self, name, state_instance):
        self._states[name] = state_instance
    
    def change_state(self, name):
        if name in self._states:
            self._current_state = self._states[name]
    
    def get_current_state(self):
        return self._current_state