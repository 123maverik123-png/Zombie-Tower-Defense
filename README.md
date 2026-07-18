<p align="center">
  <img src="https://img.shields.io/badge/Version-1.3.3-brightgreen.svg?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/Python-3.12-blue.svg?style=for-the-badge" alt="Python">
  <img src="https://img.shields.io/badge/Pygame-2.6.0-orange.svg?style=for-the-badge" alt="Pygame">
  <img src="https://img.shields.io/badge/Platform-Windows-lightgrey.svg?style=for-the-badge" alt="Platform">
</p>

<p align="center">
  <h1 align="center">🧟 Zombie Tower Defense</h1>
  <p align="center">
    <strong>Version 1.3.3</strong> — 9 Towers, 5 Enemies, 50 Levels
  </p>
</p>

---

## 🎮 About the Game

**Zombie Tower Defense** is a classic tower defense game where you build defensive towers to stop waves of zombies from reaching your castle. Strategically place different tower types, upgrade them, combine effects, and survive 50 increasingly difficult levels!

The zombie apocalypse has begun! Zombies are emerging from portals and marching toward your castle. Build towers along their path, upgrade your defenses, and protect your kingdom from the undead horde!

---

## 🏰 Features

### 🗼 9 Unique Tower Types

| Tower | Unlock Level | Special Ability |
|-------|--------------|-----------------|
| **Sniper** | 1 | High damage, long range, slow fire rate |
| **Turret** | 1 | Medium damage, fast fire rate |
| **Flamethrower** | 5 | Fire damage, AOE, burning effect (🔥 -0.5% HP/0.5s) |
| **Electric** | 10 | Chain lightning, hits ground + flying enemies |
| **Water** | 12 | No damage, applies Water effect (amplifies Electric and Freeze) |
| **PVO** | 15 | Anti-air, only targets flying enemies |
| **Freeze** | 20 | Slows enemies (50%, 80% with Water) |
| **Acid** | 25 | Damage over time (DoT) |
| **Rocket** | 30 | Massive AOE explosive damage |

### 🧟 5 Enemy Types

| Enemy | Speed | Health | Special |
|-------|-------|--------|---------|
| **Normal** | Medium | Medium | Basic zombie |
| **Fast** | High | Low | Fast movement |
| **Tank** | Slow | High | High HP, slow |
| **Night** | Medium | Medium | Dodge chance (30%) |
| **Flying** | Fast | Medium | Ignores walls, only PVO/Electric can target |

### 🔗 Tower Combinations

- **Water + Electric** → 130% damage (50% bonus)
- **Water + Freeze** → 80% slow (instead of 50%)

### 🧱 Wall System

- **Gates** — Place on road, block path (500 HP)
- **Walls** — Place on grass, block path (200 HP)
- Unlocked at Level 5

### 🌊 Visual Effects

- **Fire** — Red tint on enemies, burn damage
- **Water** — Blue tint on enemies, amplifier
- **Freeze** — Light blue tint, slow effect
- **Acid** — Green tint, DoT damage
- **Electric** — Sparks, chain lightning

### 🎯 50 Hand-Crafted Levels

- Each level has a unique, carefully designed path
- 15 waves per level
- Up to 60 enemies per wave
- Progressive difficulty (easy → expert)
- Boss waves every 5 levels

### 🎨 Visuals & Audio

- Animated sprites for all enemies (4 directions × frames)
- Tower sprites for all 4 upgrade levels
- Projectile effects (bullets, fireballs, lightning)
- Muzzle flashes for all towers
- Hit decals (blood, water splash, ice crystal, acid, crack)
- Death animation with falling effect
- Unique sound effects for each tower type
- Adaptive UI that scales to any screen resolution

---

## 💾 Save System

- **Automatic Progress Saving** — Level completion is saved automatically
- **SQLite Database** — All game data stored in `saves/game.db`
- **Settings Persistence** — Volume and display settings saved to `settings.json`

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
