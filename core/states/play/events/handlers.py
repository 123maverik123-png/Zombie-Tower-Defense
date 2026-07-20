# core/states/play/events/handlers.py
from core.event_bus import EventBus

class EventHandlers:
    """Вспомогательные обработчики событий"""
    
    def __init__(self, state):
        self.state = state
    
    def setup(self):
        """Настройка подписок (если нужно разделить)"""
        # Можно оставить пустым, если всё в BusEvents
        pass