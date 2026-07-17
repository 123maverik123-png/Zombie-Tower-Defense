# 🧟 Zombie Tower Defense

> **Version 1.3.0** — 9 Towers, 5 Enemies, 50 Levels

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.6.0-green.svg)](https://www.pygame.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://github.com/)

---

## 🎮 About

**Zombie Tower Defense** — Build towers, defend your castle, survive 50 levels!

---

## 🏰 Features

### 9 Tower Types
| Tower | Unlock | Special |
|-------|--------|---------|
| Sniper | Lv.1 | High damage |
| Turret | Lv.1 | Fast fire |
| Flamethrower | Lv.5 | Fire + burn |
| Electric | Lv.10 | Chain lightning |
| Water | Lv.12 | Amplifies |
| PVO | Lv.15 | Anti-air |
| Freeze | Lv.20 | Slows 50% |
| Acid | Lv.25 | DoT damage |
| Rocket | Lv.30 | AOE damage |

### 5 Enemy Types
- Normal, Fast, Tank, Night, Flying

### Tower Combos
- Water + Electric = **130% damage**
- Water + Freeze = **80% slow**

### 50 Levels
- Hand-crafted paths
- 15 waves each
- Progressive difficulty

### Wall System
- Gates (on road)
- Walls (on grass)
- Unlocked at Lv.5

---

## 🎮 Controls

| Action | Key |
|--------|-----|
| Select Tower | **1-9** |
| Build Mode | **RMB** |
| Build Tower | **LMB** on grass |
| Upgrade Tower | **LMB** on tower → ⬆ |
| Sell Tower | **LMB** on tower → $ |
| Wall Mode | **G** |
| Pan Camera | **Middle Mouse** |
| Pause | **ESC** |

---

## 📥 Installation

### Portable EXE (Recommended)
1. Download `ZombieTowerDefense.exe` from [Releases](https://github.com/yourusername/zombie-tower-defense/releases)
2. Extract and run!

### From Source
```bash
git clone https://github.com/yourusername/zombie-tower-defense.git
cd zombie-tower-defense
pip install -r requirements.txt
python generate_sounds.py
python main.py
