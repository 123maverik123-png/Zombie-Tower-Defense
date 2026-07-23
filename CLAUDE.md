# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the game (requires OpenGL 3.3+ GPU)
python main.py

# Install deps
pip install -r requirements.txt

# Tests (pytest). test_gl_core.py exercises the GPU/ModernGL path headlessly.
python -m pytest tests/ -q
python -m pytest tests/test_enemy.py -q          # single file
python -m pytest tests/test_iso.py -q             # isometric projection math

# Smoke test: boots the game, drops straight into a level, spawns a wave,
# checks the GPU render path doesn't crash. Optional arg = level number (default 1).
python -u smoke_test.py <level_num>

# Compile-check without running (fast syntax/import sanity check after edits)
python -m compileall -q main.py core entities systems ui utils services

# Build portable Windows .exe (PyInstaller) into portable/ + zip
BUILD_PORTABLE.bat
```

No lint/format config is enforced in CI; `black`/`mypy` are in requirements.txt but unconfigured.

## Architecture

Isometric (2:1 dimetric) pixel-art tower defense. All game logic (paths, positions,
collision, targeting) is stored in **world pixel coordinates** on a top-down plane;
isometric projection is purely a draw-time transform via `core/iso.py::world_to_screen`
(and `screen_to_world` for mouse clicks). Never store screen/projected coordinates in
game state — see the module docstring in `core/iso.py` for the axis convention
(+X world → screen right-down, +Y world → screen left-down).

### State machine

`core/state_manager.py` is a deliberately thin `StateManager`: a flat dict of
`{name: State instance}` with `change_state(name)` swapping the active one — no
transition graph, no guards. States are registered lazily; several states
(`GameOverState`, `IntroState`) tear down and re-`add_state('PLAYING', PlayState(...))`
right before switching, to force a fresh session. `main.py::Game.__init__` wires up
the initial states and calls `change_state('MENU')` once; everything else is created
on demand inside the relevant transition handler.

Typical flow: `MENU → PROFILE_SELECT/CREATE → (DIFFICULTY_SELECT) → LEVEL_SELECT →
INTRO (long once per profile, short "card" every level) → PLAYING → PAUSED/GAME_OVER/
victory → LEVEL_SELECT`. `core/states/play/` is the actual TD session — it's a
package, not a single file: `state.py` is the `PlayState` shell; `init.py`,
`update.py`, `towers.py`, `enemies.py`, `decals.py`, `effects.py`, `tutorial.py`,
`events/`, `draw/`, `ui/` split out setup, per-frame update, and per-layer draw logic.

### Rendering (GPU, `core/opengl/`)

Everything draws through one atlas + one sprite batcher, not pygame's blit:
- All sprites get packed into 2048×2048 texture atlases (`atlas.py`).
- One `SpriteBatcher` per frame (`batch.py`) — draw-call order == layer order, so
  layer ordering bugs show up as "wrong thing on top", not crashes.
- Additive-blended particles on GPU for fire/lightning/glow-type effects.
- UI is still drawn with pygame, then composited on top as a single texture each
  frame (`ui_overlay.py`) — recreating/renaming this texture per-frame instead of
  reusing a fixed set of buffers caused a real VRAM leak at 2K resolution; keep
  texture lifetime bounded (fixed triple-buffer, not alloc-per-frame) if touching
  this path.

### Tile map & camera (`core/tile_manager/`)

`TileManager` owns `tile_size` as a property whose setter propagates to `drawer`
and `map_loader` — always set it through the manager, not the sub-objects directly.
`_calculate_tile_size()` auto-fits tile size to the viewport using the iso scale
constants from `core/iso.py` (map diagonal in world-pixel terms), clamped to
`max_tile_size=128`. The map editor (`core/states/map_editor/`) keeps its own
independent `tile_size`, not wired to `TileManager`.

### Entities & enemy direction

`entities/enemy/` splits `enemy.py` (state/stats), `movement.py` (pathing/collision),
`visuals.py` (sprite/frame selection) — the same split pattern repeats for
`entities/tower/`. Enemy sprite direction (`EnemyMovement._face`, `movement.py`) is
chosen from **raw world-space** `vx`/`vy` (dominant axis → left/right/up/down), not
from `world_to_screen`-projected vectors — projecting first was tried and reverted:
`ISO_SCALE_X` (0.5) is twice `ISO_SCALE_Y` (0.25), so for any single-axis world
movement the projected `sx` always dominates `sy`, collapsing every direction to
just left/right. Only 4 sprite directions exist per enemy class; there is no
8-direction (NE/SE/SW/NW) sprite set.

### Procedural sprite generation (`tools/gen_*.py`)

Enemy/tower/tile pixel art is generated offline by standalone scripts, not at
runtime. `tools/gen_zombie_pixel.py` is the active enemy generator: draws on a
26×34 logical grid, upscales ×4 NEAREST, one palette + `SIZE_MOD` per variant
(`normal/fast/tank/night/flying/boss`), output to `assets/sprites/pzombie_<variant>/
{down,up,left,right}_{0..3}.png` (static PNGs, read at runtime via
`core/graphics_theme.py`'s `sprite_folder` remap — never imported/called from game
code). Only 2 diagonal poses are drawn — `draw_diag_toward` (camera-facing SE
lean) and `draw_diag_away` (away-facing NE lean) — each mirrored via PIL to cover
the opposite lean; saved as `right`=toward, `down`=mirror(toward), `up`=away,
`left`=mirror(away) (see the file's module docstring for the world-axis↔screen-
diagonal↔file-slot mapping). These pose functions are **shared** across all
non-flying variants (only palette/`SIZE_MOD` differ) — editing them changes every
variant at once; regenerate one variant at a time with `generate('normal')` via
`python -c` rather than running the module's `__main__` loop (which regenerates
all 6). `flying` still uses separate, non-diagonal `draw_bat_front/back/side`.
`tools/gen_kenney_assets.py` (`kzombie_*` output) is legacy/unused —
`graphics_theme.py` maps everything to `pzombie_*`.

### Balance & content data

- `data/configs/towers.json` / `enemies.json` — all tower/enemy stats, no code
  changes needed to retune.
- `systems/wave/` — wave composition/difficulty curve (`config.py`), spawn
  scheduling (`manager.py`, `factory.py`).
- `data/levels/levels_*.py` (5 files × 10 levels) merged into `LEVELS` by
  `data/levels_data.py` — pure geometry (waypoints, decorations), no story data.
- Lore lives in `core/states/intro_state.py` (`LORE_SLIDES`/`SLIDE_SCENES`): the
  world is held by a Crystal Heart, a Rift released an undead horde from a portal,
  the player is the last Guardian. `LEVEL_SUBTITLES` gives the short per-level
  intro card text.

### Persistence

`services/save_system.py` + `services/profile_manager.py` read/write SQLite at
`saves/game.db` (schema in `schema.sql`) plus per-profile files under
`saves/profiles/`.
