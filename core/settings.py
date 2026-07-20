# core/settings.py
import json
import os
import sys

class GameSettings:
    """Глобальные настройки игры с сохранением в JSON"""
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
        
        # Определяем базовую папку
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.settings_file = os.path.join(base_path, "settings.json")
        
        # Проверяем права на запись
        try:
            test_file = os.path.join(base_path, "test_write.tmp")
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except (PermissionError, OSError):
            docs_path = os.path.join(os.path.expanduser("~"), "Documents", "ZombieTowerDefense")
            os.makedirs(docs_path, exist_ok=True)
            self.settings_file = os.path.join(docs_path, "settings.json")
        
        self.default_settings = {
            "master_volume": 0.7,
            "music_volume": 0.6,
            "sfx_volume": 0.8,
            "sound_enabled": True,
            "music_enabled": True,
            "fullscreen": False,
            "borderless": False,
            "display_mode": "window",  # ✅ ОКНО ПО УМОЛЧАНИЮ
            "fps_limit": 60,
            "resolution": "1920x1080",  # ✅ FULL HD ПО УМОЛЧАНИЮ
            "tile_scale": 0.6,
            "ui_scale": 1.0,
            "show_fps": False
        }
        
        self.settings = self.default_settings.copy()
        self.load()
    
    def load(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    for key in self.default_settings:
                        if key in loaded:
                            self.settings[key] = loaded[key]
            except (json.JSONDecodeError, IOError):
                pass
    
    def save(self):
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            return True
        except (PermissionError, IOError):
            try:
                docs_path = os.path.join(os.path.expanduser("~"), "Documents", "ZombieTowerDefense")
                os.makedirs(docs_path, exist_ok=True)
                self.settings_file = os.path.join(docs_path, "settings.json")
                with open(self.settings_file, 'w', encoding='utf-8') as f:
                    json.dump(self.settings, f, indent=4, ensure_ascii=False)
                return True
            except:
                return False
    
    def get(self, key, default=None):
        return self.settings.get(key, default)
    
    def set(self, key, value):
        if key in self.settings:
            self.settings[key] = value
            self.save()
            return True
        return False
    
    @property
    def master_volume(self):
        return self.settings.get("master_volume", 0.7)
    
    @property
    def music_volume(self):
        return self.settings.get("music_volume", 0.6)
    
    @property
    def sfx_volume(self):
        return self.settings.get("sfx_volume", 0.8)
    
    @property
    def sound_enabled(self):
        return self.settings.get("sound_enabled", True)
    
    @property
    def music_enabled(self):
        return self.settings.get("music_enabled", True)
    
    @property
    def fullscreen(self):
        return self.settings.get("fullscreen", False)
    
    @property
    def borderless(self):
        return self.settings.get("borderless", False)
    
    @property
    def display_mode(self):
        return self.settings.get("display_mode", "window")
    
    @property
    def resolution(self):
        return self.settings.get("resolution", "1920x1080")
    
    @property
    def tile_scale(self):
        return self.settings.get("tile_scale", 0.6)
    
    @property
    def ui_scale(self):
        return self.settings.get("ui_scale", 1.0)
    
    @property
    def show_fps(self):
        return self.settings.get("show_fps", False)

    def get_resolution_tuple(self) -> tuple:
        res_map = {
            "1280x720": (1280, 720),
            "1920x1080": (1920, 1080),
            "2560x1440": (2560, 1440)
        }
        return res_map.get(self.resolution, (1920, 1080))