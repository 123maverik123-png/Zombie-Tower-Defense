# services/save_system.py
import sqlite3
import os
import json
from utils.path_utils import get_save_path
from typing import Optional
from entities.player import Player
from core.level_generator import LevelData

class SaveSystem:
    """Система сохранения в SQLite"""
    
    def __init__(self, db_path="saves/game.db"):
        self.db_path = get_save_path("game.db")
        self._init_db()
    
    def _init_db(self):
        """Создаёт таблицы при первом запуске"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Проверяем, есть ли уже таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='players'")
        if cursor.fetchone():
            # Проверяем, есть ли таблица level_progress
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='level_progress'")
            if not cursor.fetchone():
                # Создаём только таблицу level_progress
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS level_progress (
                        id INTEGER PRIMARY KEY,
                        data TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
            conn.close()
            return
        
        # Создаём все таблицы
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS game_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                gold INTEGER DEFAULT 100,
                lives INTEGER DEFAULT 20,
                current_level INTEGER DEFAULT 1,
                experience INTEGER DEFAULT 0,
                character_level INTEGER DEFAULT 1,
                total_kills INTEGER DEFAULT 0,
                total_gold_earned INTEGER DEFAULT 0,
                waves_survived INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                tower_id TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
                UNIQUE(player_id, tower_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS unlocked_towers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                tower_id TEXT NOT NULL,
                unlock_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
                UNIQUE(player_id, tower_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS level_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                level_number INTEGER NOT NULL,
                result TEXT CHECK(result IN ('win', 'loss')),
                waves_completed INTEGER,
                towers_built INTEGER,
                enemies_killed INTEGER,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS level_progress (
                id INTEGER PRIMARY KEY,
                data TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_progress_player ON game_progress(player_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_player ON inventory(player_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stats_player_level ON level_stats(player_id, level_number)")
        
        conn.commit()
        conn.close()
    
    def save_player(self, player: Player) -> int:
        """Сохраняет игрока и его прогресс"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT OR REPLACE INTO players (id, name, last_played) VALUES (COALESCE((SELECT id FROM players WHERE name=?), NULL), ?, CURRENT_TIMESTAMP)",
            (player.name, player.name)
        )
        player_id = cursor.lastrowid
        if not player_id:
            cursor.execute("SELECT id FROM players WHERE name=?", (player.name,))
            player_id = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT OR REPLACE INTO game_progress 
            (player_id, gold, lives, current_level, experience, character_level, 
             total_kills, total_gold_earned, waves_survived)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            player_id, player.gold, player.lives, player.current_level,
            player.experience, player.level,
            player.stats.get("total_kills", 0),
            player.stats.get("total_gold_earned", 0),
            player.stats.get("waves_survived", 0)
        ))
        
        cursor.execute("DELETE FROM inventory WHERE player_id=?", (player_id,))
        for tower_id, count in player.inventory.items():
            if count > 0:
                cursor.execute(
                    "INSERT INTO inventory (player_id, tower_id, count) VALUES (?, ?, ?)",
                    (player_id, tower_id, count)
                )
        
        cursor.execute("DELETE FROM unlocked_towers WHERE player_id=?", (player_id,))
        for tower_id in player.unlocked_towers:
            cursor.execute(
                "INSERT INTO unlocked_towers (player_id, tower_id) VALUES (?, ?)",
                (player_id, tower_id)
            )
        
        conn.commit()
        conn.close()
        return player_id
    
    def load_player(self, name: str) -> Optional[Player]:
        """Загружает игрока из БД"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT gold, lives, current_level, experience, character_level,
                   total_kills, total_gold_earned, waves_survived
            FROM game_progress
            JOIN players ON players.id = game_progress.player_id
            WHERE players.name = ?
        """, (name,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return None
        
        gold, lives, current_level, exp, char_level, kills, gold_earned, waves = result
        
        cursor.execute(
            "SELECT tower_id, count FROM inventory JOIN players ON players.id = inventory.player_id WHERE players.name = ?",
            (name,)
        )
        inventory = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.execute(
            "SELECT tower_id FROM unlocked_towers JOIN players ON players.id = unlocked_towers.player_id WHERE players.name = ?",
            (name,)
        )
        unlocked = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        player = Player(name)
        player.gold = gold
        player.lives = lives
        player.current_level = current_level
        player.experience = exp
        player.level = char_level
        player.inventory = inventory
        player.unlocked_towers = unlocked
        player.stats = {
            "total_kills": kills,
            "total_gold_earned": gold_earned,
            "waves_survived": waves
        }
        
        return player
    
    def save_level_data(self, level_data: LevelData):
        """Сохраняет прогресс уровней"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        data = level_data.to_dict()
        json_data = json.dumps(data)
        
        cursor.execute("""
            INSERT OR REPLACE INTO level_progress (id, data, updated_at)
            VALUES (1, ?, CURRENT_TIMESTAMP)
        """, (json_data,))
        
        conn.commit()
        conn.close()
    
    def load_level_data(self) -> LevelData:
        """Загружает прогресс уровней"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Проверяем, существует ли таблица
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='level_progress'")
        if not cursor.fetchone():
            # Создаём таблицу
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS level_progress (
                    id INTEGER PRIMARY KEY,
                    data TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
            return LevelData()
        
        cursor.execute("SELECT data FROM level_progress WHERE id = 1")
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            try:
                data = json.loads(result[0])
                return LevelData.from_dict(data)
            except Exception:
                pass
        
        return LevelData()