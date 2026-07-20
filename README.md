# 🧟 Zombie Tower Defense

A classic tower defense game about defending a castle from hordes of zombies — built in **Python + Pygame** with full GPU rendering via **ModernGL**.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Pygame](https://img.shields.io/badge/Pygame-2.5-green)
![ModernGL](https://img.shields.io/badge/ModernGL-5.12-orange)
![OpenGL](https://img.shields.io/badge/OpenGL-3.3-red)

## 🎮 About the Game

Zombies come in waves along the path to your castle. Build towers, combine elemental effects, place walls and gates — and don't let them break through.

- **50 levels** with unique twisted maps
- **9 tower types**: Sniper, Machine Gun, Flamethrower, Electric, Water, Anti-Air, Freeze, Acid, Rocket
- **Elemental combos**: wet enemies take ×1.5 from electricity, water extinguishes burning enemies, freeze lasts longer on wet targets
- **6 zombie types**: Normal, Runner, Tank, Night (evasion), Flying, Boss
- **Walls and gates** — block the path and force zombies to break through
- **Bosses every 5th level** with scaling power
- **Tutorial first level** with hints
- **Player profiles** with progression, Normal and Hardcore modes
- **Map editor** — create your own levels and play them
- **Full GPU rendering**: hundreds of enemies and thousands of particles without FPS drops

## 🕹️ Controls

| Action | Key |
|---|---|
| Select tower | Left-click on the bottom panel |
| Build | Right-click — build mode, Left-click — place |
| Upgrade / Sell | Left-click on tower |
| Walls and gates | `G` (toggle: gate/wall) |
| Pause | `ESC` |
| Developer console | `~` |

## 🚀 Running from Source

```bash
# Python 3.12+
pip install -r requirements.txt
python main.py
```

Requires a GPU with **OpenGL 3.3** support (any GPU from ~2010 onward).

## 📦 Building a Portable Version (Windows)

```bash
BUILD_PORTABLE.bat
```

The script will build `ZombieTowerDefense.exe` via PyInstaller, package the portable version into the `portable/` folder, and zip it.

## 🏗️ Architecture

```
main.py                  — Game loop, window, OpenGL context
core/
  opengl/                — GPU renderer: texture atlas, sprite batcher, shaders
  states/                — Game states (menu, gameplay, pause, map editor...)
  audio/                 — Music and sound effects
  tile_manager/          — Map, tiles, camera
systems/wave/            — Wave generation and management
entities/                — Towers, enemies, projectiles, decals, walls
data/configs/            — JSON configs for towers and enemies (balance tweaked here)
data/levels_data.py      — 50 maps (waypoints)
services/                — Profiles, saves
tests/                   — pytest (including GPU core tests in headless mode)
```

Key rendering features:
- All sprites packed into 2048×2048 texture atlases
- One sprite batcher per frame: minimal draw calls (draw order = layer order)
- Effects (fire, lightning, glows) — additive GPU particles
- UI is drawn with Pygame and rendered over the scene as a single texture

## ⚖️ Balance

All balance is in `data/configs/towers.json` and `data/configs/enemies.json`,
the difficulty curve is in `systems/wave/config.py`. Tweakable without touching a single line of code.

## 📄 License

This project was created for educational purposes. Feel free to use the code.




Классическая tower defense про оборону замка от орд зомби — написана на **Python + Pygame** с полноценным GPU-рендерингом через **ModernGL**.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Pygame](https://img.shields.io/badge/Pygame-2.5-green)
![ModernGL](https://img.shields.io/badge/ModernGL-5.12-orange)
![OpenGL](https://img.shields.io/badge/OpenGL-3.3-red)

## 🎮 Об игре

Зомби идут волнами по дороге к вашему замку. Стройте башни, комбинируйте стихии, ставьте стены и ворота — и не дайте им прорваться.

- **50 уровней** с уникальными закрученными картами
- **9 типов башен**: снайпер, пулемёт, огнемёт, электрическая, водяная, ПВО, заморозка, кислота, ракетная
- **Стихийные комбо**: мокрые враги получают ×1.5 от электричества, вода тушит горящих, заморозка держит мокрых дольше
- **6 типов зомби**: обычный, бегун, танк, ночной (уклонение), летучий, босс
- **Стены и ворота** — перегораживайте путь и заставляйте зомби прогрызать себе дорогу
- **Боссы каждый 5-й уровень** с растущей силой
- **Обучающий первый уровень** с подсказками
- **Профили игроков** с прогрессом, Normal и Hardcore режимы
- **Редактор карт** — создавайте свои уровни и играйте на них
- **Полный GPU-рендеринг**: сотни врагов и тысячи частиц без просадок FPS

## 🕹️ Управление

| Действие | Клавиша |
|---|---|
| Выбор башни | ЛКМ по панели внизу |
| Постройка | ПКМ — режим постройки, ЛКМ — поставить |
| Апгрейд / продажа | ЛКМ по башне |
| Стены и ворота | `G` (переключение: ворота/стена) |
| Пауза | `ESC` |
| Консоль разработчика | `~` |

## 🚀 Запуск из исходников

```bash
# Python 3.12+
pip install -r requirements.txt
python main.py
```

Требуется видеокарта с поддержкой **OpenGL 3.3** (любая GPU после ~2010 года).

## 📦 Сборка portable-версии (Windows)

```bash
BUILD_PORTABLE.bat
```

Скрипт соберёт `ZombieTowerDefense.exe` через PyInstaller, сложит portable-версию в папку `portable/` и запакует её в ZIP.

## 🏗️ Архитектура

```
main.py                  — игровой цикл, окно, OpenGL-контекст
core/
  opengl/                — GPU-рендер: атлас текстур, спрайт-батчер, шейдеры
  states/                — состояния игры (меню, игра, пауза, редактор карт...)
  audio/                 — музыка и звуки
  tile_manager/          — карта, тайлы, камера
systems/wave/            — генерация и менеджмент волн
entities/                — башни, враги, снаряды, декали, стены
data/configs/            — JSON-конфиги башен и врагов (баланс правится тут)
data/levels_data.py      — 50 карт (waypoints)
services/                — профили, сейвы
tests/                   — pytest (включая тесты GPU-ядра в headless-режиме)
```

Ключевые особенности рендера:
- Все спрайты упаковываются в текстурные атласы 2048×2048
- Один спрайт-батчер на кадр: минимум draw call'ов (порядок вызовов = порядок слоёв)
- Эффекты (огонь, молнии, свечения) — аддитивные частицы на GPU
- UI рисуется Pygame'ом и выводится поверх сцены одной текстурой

## ⚖️ Баланс

Весь баланс — в `data/configs/towers.json` и `data/configs/enemies.json`,
кривая сложности — в `systems/wave/config.py`. Правится без единой строчки кода.

## 📄 Лицензия

Проект создан в учебных целях. Используйте код свободно.
