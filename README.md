# 🧟 Zombie Tower Defense

> **Version 1.2.0** — Build towers, defend your castle, survive the zombie apocalypse!

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.6.0-green.svg)](https://www.pygame.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://github.com/)

---

## 🎮 About the Game

**Zombie Tower Defense** is a classic tower defense game where you build defensive towers to stop waves of zombies from reaching your castle. Strategically place different tower types, upgrade them, and survive as long as possible!

---

## 🏰 Gameplay

- **4 Unique Tower Types**: Sniper, Turret, Flamethrower, Electric — each with 4 upgrade levels
- **5 Enemy Types**: Normal, Fast, Tank, Night (dodge chance), and Boss
- **50 Levels**: Progressive difficulty with new enemies unlocking as you advance
- **Wave System**: Each level has multiple waves with increasing difficulty
- **Boss Waves**: Challenge yourself with powerful boss enemies every 5 levels

---

## 🎨 Visuals

- **Animated Sprites**: 4-directional animations for all enemy types
- **Tower Sprites**: Unique visuals for each tower and upgrade level
- **Projectile Effects**: Bullets, fireballs, lightning, and chain lightning
- **Adaptive UI**: Scales perfectly to any screen resolution

---

## 🎮 Controls

| Action | Control |
|--------|---------|
| Select Tower | Click on tower panel or press **1-4** |
| Build Mode | **RMB** toggle |
| Build Tower | **LMB** on empty grass tile |
| Upgrade Tower | **LMB** on tower → click **⬆** |
| Sell Tower | **LMB** on tower → click **$** |
| Pan Camera | **Middle Mouse** drag |
| Quick Select | **1** Sniper, **2** Turret, **3** Flamethrower, **4** Electric |
| Pause | **ESC** |

---

## 🗺️ Map Editor

Create your own custom levels!

| Action | Control |
|--------|---------|
| Select Tile | **1-9, 0** |
| Waypoint Mode | **W** |
| Erase Mode | **E** |
| Convert Waypoints to Road | **R** |
| Save Map | **S** |
| Load Map | **L** |
| Delete Last Waypoint | **Backspace** |
| Clear Waypoints | **C** |
| Toggle Path Display | **H** |

**How to Create a Map:**
1. Place **portal** (start) and **castle** (end)
2. Place waypoints to define the zombie path
3. Press **R** to auto-generate road tiles
4. Save and play from Level Select!

---

## 💾 Save System

- **Automatic Progress Saving**: Level completion is saved automatically
- **SQLite Database**: All game data stored in `saves/game.db`
- **Settings Persistence**: Volume and display settings saved to `settings.json`

---

## 🐛 Known Issues (v1.2.0)

- Zoom disabled temporarily (causes sprite scaling issues)
- Enemy pathfinding can be inconsistent on custom maps
- Sound effects may not play on first launch

---

## 🚀 Next (v1.3.0)

- Tower attack animations
- Sound effects library
- Tooltip system
- Mini-map
- Achievements system
- More enemy types

---

## ⭐ Show Your Support

If you like this project, please give it a ⭐ on GitHub!

---

**Made with ❤️ by Zombie Tower Defense Team**

[GitHub](https://github.com/yourusername/zombie-tower-defense) • [Releases](https://github.com/yourusername/zombie-tower-defense/releases)
