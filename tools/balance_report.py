# tools/balance_report.py
# Аналитика баланса: DPS/эффективность башен + поток HP волн vs доход золота.
# Чистая математика по configs, игру не трогает. Латиница в выводе (cp1251).
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
towers = json.load(open(os.path.join(ROOT, 'data/configs/towers.json'), encoding='utf-8'))
enemies = json.load(open(os.path.join(ROOT, 'data/configs/enemies.json'), encoding='utf-8'))

import sys
sys.path.insert(0, ROOT)
from systems.wave.config import WAVE_CONFIG, ENEMY_UNLOCK_LEVELS


def eff_dps(t):
    """Оценка эффективного DPS башни ур.1 (fire_rate = интервал в сек)."""
    dmg = t['damage']
    rate = t.get('fire_rate', 1.0)
    direct = dmg / rate if rate > 0 else 0
    # DoT-компоненты
    dot = 0.0
    if 'fire_dot_damage' in t:
        dot += t['fire_dot_damage'] / t.get('fire_dot_interval', 0.5)
    if 'acid_damage' in t:
        dot += t['acid_damage'] / t.get('acid_interval', 0.5)
    return direct, dot


print("=" * 78)
print("TOWERS: cost / DPS / DPS-per-100g  (fire_rate = interval sec)")
print("=" * 78)
print(f"{'tower':<14}{'cost':>6}{'dmg':>7}{'rate':>7}{'directDPS':>11}{'dotDPS':>9}{'DPS/100g':>10}")
for tid, t in towers.items():
    direct, dot = eff_dps(t)
    total = direct + dot
    per100 = total / t['cost'] * 100 if t['cost'] else 0
    print(f"{tid:<14}{t['cost']:>6}{t['damage']:>7.1f}{t.get('fire_rate',0):>7.2f}"
          f"{direct:>11.1f}{dot:>9.1f}{per100:>10.1f}")

print()
print("=" * 78)
print("WAVE HP FLOW vs GOLD INCOME per level")
print("=" * 78)


def wave_count(level, wi):
    base = WAVE_CONFIG['min_enemies_per_wave'] + wi * 2 + int(level * 3)
    return min(base, WAVE_CONFIG['max_enemies_per_wave'])


def n_waves(level):
    return min(WAVE_CONFIG['max_waves'], WAVE_CONFIG['min_waves'] + level // 3)


def hp_mult(level):
    return 1 + WAVE_CONFIG['hp_growth_per_level'] * (level - 1)


def avail(level):
    return [e for e, lv in ENEMY_UNLOCK_LEVELS.items()
            if level >= lv and e != 'zombie_boss']


print(f"{'lvl':>4}{'waves':>6}{'enem/last':>10}{'avgHP':>7}{'totalHP':>10}"
      f"{'gold_in':>9}{'boss?':>6}")
for level in [1, 3, 5, 7, 10, 15, 20, 25, 30, 40, 50]:
    nw = n_waves(level)
    types = avail(level) or ['zombie_normal']
    avg_hp_base = sum(enemies[e]['health'] for e in types) / len(types)
    avg_gold = sum(enemies[e]['reward_gold'] for e in types) / len(types)
    m = hp_mult(level)
    total_hp = 0
    total_gold = 0
    for wi in range(nw):
        c = wave_count(level, wi)
        total_hp += c * avg_hp_base * m
        total_gold += c * avg_gold
    is_boss = (level % WAVE_CONFIG['boss_wave_interval'] == 0)
    if is_boss:
        bhp = WAVE_CONFIG['boss_base_hp'] + WAVE_CONFIG['boss_hp_per_level'] * level
        total_hp += bhp
        total_gold += 50
    last = wave_count(level, nw - 1)
    print(f"{level:>4}{nw:>6}{last:>10}{avg_hp_base*m:>7.0f}{total_hp:>10.0f}"
          f"{total_gold:>9.0f}{'Y' if is_boss else '':>6}")

print()
print("Start gold=100, lives=20.  Reward/HP ratio per enemy type:")
for e, cfg in enemies.items():
    if cfg.get('is_boss'):
        continue
    print(f"  {e:<16} HP={cfg['health']:>4}  gold={cfg['reward_gold']:>3}  "
          f"gold/HP={cfg['reward_gold']/cfg['health']*100:>5.1f}%  "
          f"unlock=L{ENEMY_UNLOCK_LEVELS.get(e,'?')}")
