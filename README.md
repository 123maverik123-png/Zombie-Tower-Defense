# 🧟 Zombie Tower Defense

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/yourusername/zombie-tower-defense/releases)
[![Platform](https://img.shields.io/badge/platform-Windows-blue.svg)](https://github.com/yourusername/zombie-tower-defense/releases)
[![Downloads](https://img.shields.io/github/downloads/yourusername/zombie-tower-defense/total.svg)](https://github.com/yourusername/zombie-tower-defense/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![Pygame](https://img.shields.io/badge/pygame-2.5.2-green.svg)](https://pygame.org)

A feature-rich Tower Defense game built with Python and Pygame. Defend your base against waves of zombies across 50 procedurally generated levels!

## 🎮 Features

- **50 Procedurally Generated Levels** - Each level offers unique challenges with random enemy waves
- **3 Tower Types** - Basic, Sniper, and Cannon towers with upgrade system (up to level 5)
- **Progression System** - Unlock levels sequentially, track your progress
- **Wave System** - Dynamic waves with increasing difficulty
- **Tower Upgrade System** - Click on towers to upgrade their stats (damage, range, fire rate)
- **Audio System** - Background music and sound effects with volume controls
- **Save/Load System** - Progress saved automatically in SQLite database
- **Settings Menu** - Adjust master volume, music volume, and SFX volume
- **Level Selection** - Visual grid showing completed (green), available (yellow), and locked (red) levels
- **Responsive UI** - Clean interface with real-time HUD
- **Portable Version** - No installation required, just download and play!

## 🛠️ Technologies

- **Python 3.12+** - Core language
- **Pygame 2.5.2** - Game engine and rendering
- **SQLite** - Progress persistence
- **NumPy** - Sound generation

## 📦 Download

### Windows (Portable)
- **Version 1.0.0** - [Download ZIP](https://github.com/yourusername/zombie-tower-defense/releases/download/v1.0.0/ZombieTowerDefense_Portable.zip)
- No installation required!
- Just unzip and run `ZombieTowerDefense.exe`

### System Requirements
- Windows 7, 8, 10, 11
- 64-bit processor
- 100 MB free disk space
- 2 GB RAM recommended
- **No Python required!**

## 🎯 How to Play

### Controls

| Key | Action |
|-----|--------|
| `B` | Toggle build mode |
| `1` | Select Basic Tower (Cost: 50 gold) |
| `2` | Select Sniper Tower (Cost: 100 gold) |
| `3` | Select Cannon Tower (Cost: 150 gold) |
| `Left Click` | Build tower (in build mode) / Upgrade tower (click on existing tower) |
| `Right Click` | Deselect tower |
| `ESC` | Pause game |

### Gameplay

1. **Build Towers** - Press `B` to enter build mode, select a tower type (1-3), and click on the map
2. **Upgrade Towers** - Click on any existing tower to upgrade it (costs gold, max level 5)
3. **Survive Waves** - Each level has multiple waves of zombies
4. **Earn Gold** - Defeat zombies to earn gold for building and upgrading
5. **Progress** - Complete levels to unlock the next one

### Tower Stats

| Tower Type | Cost | Damage | Range | Fire Rate | Upgrade Cost |
|------------|------|--------|-------|-----------|--------------|
| Basic | 50 | 25 | 200 | 1.0/s | 75 |
| Sniper | 100 | 75 | 400 | 0.4/s | 150 |
| Cannon | 150 | 40 | 250 | 0.6/s | 200 |

### Level Colors

| Color | Meaning |
|-------|---------|
| 🟢 **Green** | Level completed |
| 🟡 **Yellow** | Level available, not completed |
| 🔴 **Red** | Level locked (complete previous to unlock) |

## 📁 Project Structure
