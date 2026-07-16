# 🧟 Zombie Tower Defense

> **Version 1.2.0** — Build towers, defend your castle, survive the zombie apocalypse!

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.6.0-green.svg)](https://www.pygame.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://github.com/)

---

## 🎮 About the Game

**Zombie Tower Defense** is a classic tower defense game where you build defensive towers to stop waves of zombies from reaching your castle. Strategically place different tower types, upgrade them, and survive as long as possible!

### 🧟 Story
The zombie apocalypse has begun! Zombies are emerging from portals and marching toward your castle. Build towers along their path, upgrade your defenses, and protect your kingdom from the undead horde!

---

## ✨ Features

### 🏰 Gameplay
- **4 Unique Tower Types**: Sniper, Turret, Flamethrower, Electric — each with 4 upgrade levels
- **5 Enemy Types**: Normal, Fast, Tank, Night (dodge chance), and Boss
- **50 Levels**: Progressive difficulty with new enemies unlocking as you advance
- **Wave System**: Each level has multiple waves with increasing difficulty
- **Boss Waves**: Challenge yourself with powerful boss enemies every 5 levels

### 🎨 Visuals
- **Animated Sprites**: 4-directional animations for all enemy types
- **Tower Sprites**: Unique visuals for each tower and upgrade level
- **Projectile Effects**: Bullets, fireballs, lightning, and chain lightning
- **Adaptive UI**: Scales perfectly to any screen resolution

### 🎮 Controls
- **LMB on Tower**: Open upgrade/sell UI
- **LMB on Tower Panel**: Select tower type
- **RMB**: Toggle build mode
- **Middle Mouse**: Drag to pan camera
- **1-4**: Quick tower select
- **ESC**: Pause game

### 🗺️ Custom Maps
- **Map Editor**: Create your own levels with custom paths
- **Waypoint System**: Place waypoints to define zombie path
- **Auto-Road Generation**: Convert waypoints to road tiles
- **Custom Level Selector**: Play your own maps alongside standard levels

### 💾 Save System
- **Automatic Progress Saving**: Level completion is saved automatically
- **SQLite Database**: All game data stored in `saves/game.db`
- **Settings Persistence**: Volume and display settings saved to `settings.json`

---

## 📥 Installation

### Option 1: Portable EXE (Recommended)
1. Download `ZombieTowerDefense.exe` from [Releases](https://github.com/yourusername/zombie-tower-defense/releases)
2. Extract the portable folder
3. Double-click `ZombieTowerDefense.exe` to play!

### Option 2: From Source
```bash
# Clone the repository
git clone https://github.com/yourusername/zombie-tower-defense.git
cd zombie-tower-defense

# Install dependencies
pip install -r requirements.txt

# Generate sounds
python generate_sounds.py

# Run the game
python main.py
