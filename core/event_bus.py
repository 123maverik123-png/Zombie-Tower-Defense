# core/event_bus.py
from typing import Dict, List, Callable, Any
from collections import defaultdict

class EventBus:
    """Центральная шина событий для связи между компонентами"""
    _listeners: Dict[str, List[Callable]] = defaultdict(list)
    _once_listeners: Dict[str, List[Callable]] = defaultdict(list)
    _debug: bool = False  # ✅ ОТКЛЮЧЕНО
    
    @classmethod
    def set_debug(cls, enabled: bool):
        cls._debug = enabled
    
    @classmethod
    def subscribe(cls, event_type: str, callback: Callable):
        if callback not in cls._listeners[event_type]:
            cls._listeners[event_type].append(callback)
    
    @classmethod
    def subscribe_once(cls, event_type: str, callback: Callable):
        cls._once_listeners[event_type].append(callback)
    
    @classmethod
    def unsubscribe(cls, event_type: str, callback: Callable):
        if callback in cls._listeners[event_type]:
            cls._listeners[event_type].remove(callback)
    
    @classmethod
    def emit(cls, event_type: str, data: Any = None):
        listeners = cls._listeners.get(event_type, [])
        for callback in listeners:
            try:
                callback(data)
            except Exception as e:
                print(f"❌ EventBus: Error in callback for '{event_type}': {e}")
        
        once_callbacks = cls._once_listeners.get(event_type, [])
        for callback in once_callbacks:
            try:
                callback(data)
            except Exception as e:
                print(f"❌ EventBus: Error in once callback for '{event_type}': {e}")
        
        if once_callbacks:
            cls._once_listeners[event_type].clear()
    
    @classmethod
    def clear(cls):
        cls._listeners.clear()
        cls._once_listeners.clear()
    
    @classmethod
    def get_listeners(cls, event_type: str) -> List[Callable]:
        return cls._listeners.get(event_type, [])
    
    @classmethod
    def print_listeners(cls):
        print("\n📡 EventBus: Current listeners:")
        for event_type, listeners in cls._listeners.items():
            print(f"  '{event_type}': {len(listeners)} listeners")
        print()