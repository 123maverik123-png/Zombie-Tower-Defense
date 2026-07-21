# core/level_generator/level_data.py

class LevelData:
    def __init__(self):
        self.completed_levels = set()
        self.unlocked_level = 1
        self.total_levels = 50
    
    def is_completed(self, level: int) -> bool:
        return level in self.completed_levels
    
    def is_unlocked(self, level: int) -> bool:
        return level <= self.unlocked_level
    
    def complete_level(self, level: int):
        self.completed_levels.add(level)
        if level >= self.unlocked_level:
            self.unlocked_level = min(level + 1, self.total_levels)
    
    def to_dict(self) -> dict:
        return {
            'completed_levels': list(self.completed_levels),
            'unlocked_level': self.unlocked_level,
            'total_levels': self.total_levels
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LevelData':
        level_data = cls()
        level_data.completed_levels = set(data.get('completed_levels', []))
        level_data.unlocked_level = data.get('unlocked_level', 1)
        level_data.total_levels = data.get('total_levels', 50)
        return level_data
