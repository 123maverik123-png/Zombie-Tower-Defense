# services/profile_manager.py
import os
import json
from typing import Optional, List
from datetime import datetime
from utils.debug import dprint

class Profile:
    """Профиль игрока"""
    
    def __init__(self, name: str, mode: str = 'normal'):
        self.name = name
        self.mode = mode
        self.created_at = datetime.now().isoformat()
        self.last_played = datetime.now().isoformat()
        
        self.unlocked_level = 1
        self.completed_levels = set()
        self.current_level = 1
        self.gold = 300
        self.lives = 5
        self.stats = {
            'total_kills': 0,
            'waves_survived': 0,
            'total_gold_earned': 0
        }
    
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'mode': self.mode,
            'created_at': self.created_at,
            'last_played': self.last_played,
            'progress': {
                'unlocked_level': self.unlocked_level,
                'completed_levels': list(self.completed_levels),
                'current_level': self.current_level,
                'gold': self.gold,
                'lives': self.lives,
                'stats': self.stats
            }
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Profile':
        profile = cls(data['name'], data.get('mode', 'normal'))
        profile.created_at = data.get('created_at', datetime.now().isoformat())
        profile.last_played = data.get('last_played', datetime.now().isoformat())
        
        progress = data.get('progress', {})
        profile.unlocked_level = progress.get('unlocked_level', 1)
        profile.completed_levels = set(progress.get('completed_levels', []))
        profile.current_level = progress.get('current_level', 1)
        profile.gold = progress.get('gold', 300)
        profile.lives = progress.get('lives', 5)
        profile.stats = progress.get('stats', {
            'total_kills': 0,
            'waves_survived': 0,
            'total_gold_earned': 0
        })
        
        return profile
    
    def update_last_played(self):
        self.last_played = datetime.now().isoformat()
    
    def complete_level(self, level: int):
        self.completed_levels.add(level)
        if level >= self.unlocked_level:
            self.unlocked_level = min(level + 1, 50)
    
    def is_completed(self, level: int) -> bool:
        return level in self.completed_levels
    
    def is_unlocked(self, level: int) -> bool:
        return level <= self.unlocked_level
    
    def reset_progress(self):
        self.unlocked_level = 1
        self.completed_levels = set()
        self.current_level = 1
        self.gold = 300
        self.lives = 5
        self.stats = {
            'total_kills': 0,
            'waves_survived': 0,
            'total_gold_earned': 0
        }


class ProfileManager:
    """Управление профилями игроков (синглтон)"""
    
    MAX_PROFILES = 3
    PROFILES_DIR = "saves/profiles"
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
        
        self.profiles: List[Profile] = []
        self.current_profile: Optional[Profile] = None
        self._ensure_dir()
        self._load_all_profiles()
        dprint(f"📂 ProfileManager initialized. Found {len(self.profiles)} profiles.")
    
    def _ensure_dir(self):
        os.makedirs(self.PROFILES_DIR, exist_ok=True)
    
    def _get_profile_path(self, name: str) -> str:
        return os.path.join(self.PROFILES_DIR, f"{name}.json")
    
    def _load_all_profiles(self):
        """Загружает все профили из папки"""
        self.profiles = []
        if not os.path.exists(self.PROFILES_DIR):
            return
        
        for filename in os.listdir(self.PROFILES_DIR):
            if filename.endswith('.json'):
                try:
                    path = os.path.join(self.PROFILES_DIR, filename)
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        profile = Profile.from_dict(data)
                        self.profiles.append(profile)
                except Exception as e:
                    print(f"   ⚠️ Error loading profile {filename}: {e}")
        
        self.profiles.sort(key=lambda p: p.last_played, reverse=True)
    
    def _reload_profiles(self):
        """Перезагружает список профилей (без создания нового экземпляра)"""
        self._load_all_profiles()
    
    def save_profile(self, profile: Profile):
        """Сохраняет профиль в файл"""
        path = self._get_profile_path(profile.name)
        profile.update_last_played()
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(profile.to_dict(), f, indent=4, ensure_ascii=False)
        
        # ✅ Обновляем список, но НЕ создаём новый экземпляр
        self._reload_profiles()
        
        # ✅ Если это текущий профиль — обновляем его в памяти
        if self.current_profile and self.current_profile.name == profile.name:
            self.current_profile = profile
    
    def delete_profile(self, name: str) -> bool:
        """Удаляет профиль"""
        path = self._get_profile_path(name)
        if os.path.exists(path):
            os.remove(path)
            self._reload_profiles()
            if self.current_profile and self.current_profile.name == name:
                self.current_profile = None
            return True
        return False
    
    def create_profile(self, name: str, mode: str = 'normal') -> Optional[Profile]:
        """Создаёт новый профиль"""
        if len(self.profiles) >= self.MAX_PROFILES:
            print(f"⚠️ Max profiles reached ({self.MAX_PROFILES})")
            return None
        
        if self.profile_exists(name):
            print(f"⚠️ Profile '{name}' already exists")
            return None
        
        profile = Profile(name, mode)
        profile.lives = 5
        profile.gold = 300
        self.save_profile(profile)
        self.current_profile = profile
        dprint(f"✅ Profile created: {name} ({mode})")
        return profile
    
    def profile_exists(self, name: str) -> bool:
        return any(p.name == name for p in self.profiles)
    
    def get_profile(self, name: str) -> Optional[Profile]:
        for p in self.profiles:
            if p.name == name:
                return p
        return None
    
    def get_all_profiles(self) -> List[Profile]:
        return self.profiles.copy()
    
    def get_profiles_count(self) -> int:
        return len(self.profiles)
    
    def load_profile(self, name: str) -> Optional[Profile]:
        """Загружает профиль и делает его текущим"""
        profile = self.get_profile(name)
        if profile:
            self.current_profile = profile
            profile.update_last_played()
            self.save_profile(profile)
            print(f"👤 Profile loaded: {name}")
            return profile
        return None
    
    def set_current_profile(self, profile: Profile):
        self.current_profile = profile
    
    def get_current_profile(self) -> Optional[Profile]:
        return self.current_profile
    
    def has_profile(self) -> bool:
        return len(self.profiles) > 0
    
    def is_hardcore(self) -> bool:
        return self.current_profile and self.current_profile.mode == 'hardcore'
    
    def reset_hardcore_progress(self):
        if self.current_profile and self.is_hardcore():
            self.current_profile.reset_progress()
            self.save_profile(self.current_profile)
            dprint(f"💀 HARDCORE: Progress reset for {self.current_profile.name}!")
            return True
        return False