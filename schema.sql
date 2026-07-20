-- schema.sql
-- Таблица игроков (профили)
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица прогресса (основные данные)
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
);

-- Инвентарь (связь многие-ко-многим)
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    tower_id TEXT NOT NULL,
    count INTEGER DEFAULT 0,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    UNIQUE(player_id, tower_id)
);

-- Разблокированные башни
CREATE TABLE IF NOT EXISTS unlocked_towers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    tower_id TEXT NOT NULL,
    unlock_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    UNIQUE(player_id, tower_id)
);

-- Статистика по уровням
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
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_progress_player ON game_progress(player_id);
CREATE INDEX IF NOT EXISTS idx_inventory_player ON inventory(player_id);
CREATE INDEX IF NOT EXISTS idx_stats_player_level ON level_stats(player_id, level_number);