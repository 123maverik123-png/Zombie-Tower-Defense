# tools/balance_gen.py
# Генератор баланса по формулам. dry-run по умолчанию; --apply пишет JSON.
# Формула экономики (см. заметку): Доступный_DPS >= Требуемый_DPS × ЗАПАС.
#   reward_gold = HP × income_rate × k_special
#   tower_damage масштабируется до целевого EFFECTIVE DPS/100g (с учётом охвата)
# Латиница в выводе (консоль cp1251).
import json, os, sys, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# ======================= КОЭФФИЦИЕНТЫ (крути здесь) =======================
DIFFICULTY   = 'medium'          # закладка сложности
ZAPAS        = 1.4               # запас доступного DPS над требуемым
INCOME_RATE  = 0.06              # доля HP, возвращаемая золотом за убийство

# Надбавка награды за "неудобство" врага (умножает базовый reward)
K_SPECIAL = {
    'zombie_normal': 1.0,
    'zombie_fast':   2.2,   # мало времени стрелять + фарм-ценность
    'zombie_tank':   0.9,   # толстый, но лёгкая мишень
    'zombie_night':  2.2,   # уклонение 30% + фарм-ценность
    'zombie_flying': 1.3,   # только ПВО достаёт
    'zombie_boss':   1.0,   # награда босса задаётся отдельно
}

# Целевой EFFECTIVE DPS на 100 золота (номинал × охват должен попасть сюда).
# Эталон дамагеров = 50. Контроль/AoE тоже 50, но их номинал ниже —
# добирают охватом (coverage), поэтому реальный номинал масштабируем вверх.
TARGET_EFF_PER100 = 50.0
# coverage — во сколько раз башня эффективнее номинала (AoE/цепь/пробитие)
COVERAGE = {
    'sniper': 1.0, 'turret': 1.0, 'pvo': 1.0,   # одиночные — эталон
    'rocket': 2.2,        # большой AoE по пачке
    'flamethrower': 2.2,  # конус + горящая земля по толпе
    'electric': 3.0,      # цепь по chain_count целям
    'freeze': 1.3,        # single, но slow помогает всем башням
    'acid': 1.6,          # AoE-всплеск + лужа на полу
    'water': None,        # баффер, урона нет — не трогаем
}
# Босс
BOSS_BASE_HP = 500
BOSS_HP_PER_LEVEL = 220
BOSS_REWARD = 60
# Волны (управляемые значения вместо разогнанных)
WAVE = dict(
    min_waves=3, max_waves=12,
    min_enemies_per_wave=5, max_enemies_per_wave=70,
    base_spawn_delay=0.5, min_spawn_delay=0.3,
    boss_wave_interval=5, boss_spawn_delay=1.5,
    hp_growth_per_level=0.05,
    enemies_level_coef=1.5,   # int(level*coef) в calculate_wave_count
)
# =========================================================================


def eff_dps(t):
    dmg, rate = t['damage'], t.get('fire_rate', 1.0)
    direct = dmg / rate if rate > 0 else 0
    dot = 0.0
    if 'fire_dot_damage' in t:
        dot += t['fire_dot_damage'] / t.get('fire_dot_interval', 0.5)
    if 'acid_damage' in t:
        dot += t['acid_damage'] / t.get('acid_interval', 0.5)
    return direct + dot


def scale_tower(tid, t):
    cov = COVERAGE.get(tid)
    if cov is None:
        return t, 1.0  # water — не трогаем
    dps = eff_dps(t)
    if dps <= 0:
        return t, 1.0
    per100 = dps / t['cost'] * 100
    eff = per100 * cov
    scale = TARGET_EFF_PER100 / eff
    scale = max(0.5, min(2.5, scale))  # предохранитель
    nt = json.loads(json.dumps(t))
    nt['damage'] = round(t['damage'] * scale, 1)
    for k in ('fire_dot_damage', 'acid_damage'):
        if k in nt:
            nt[k] = round(t[k] * scale, 1)
    # апгрейды абсолютных DoT тоже масштабируем
    for lvl, st in nt.get('upgrade_stats', {}).items():
        for k in ('fire_dot_damage', 'acid_damage'):
            if k in st:
                st[k] = round(st[k] * scale, 1)
    return nt, scale


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    towers = json.load(open(f'{ROOT}/data/configs/towers.json', encoding='utf-8'))
    enemies = json.load(open(f'{ROOT}/data/configs/enemies.json', encoding='utf-8'))

    print(f"DIFFICULTY={DIFFICULTY} ZAPAS={ZAPAS} INCOME_RATE={INCOME_RATE}")
    print("=" * 70)
    print("TOWERS  (damage: old -> new, effective DPS/100g -> target 50)")
    print("=" * 70)
    print(f"{'tower':<14}{'dmg_old':>8}{'dmg_new':>8}{'scale':>7}{'eff_old':>9}{'eff_new':>9}")
    for tid, t in towers.items():
        nt, scale = scale_tower(tid, t)
        cov = COVERAGE.get(tid) or 0
        eo = eff_dps(t) / t['cost'] * 100 * cov
        en = eff_dps(nt) / nt['cost'] * 100 * cov
        print(f"{tid:<14}{t['damage']:>8.1f}{nt['damage']:>8.1f}{scale:>7.2f}{eo:>9.1f}{en:>9.1f}")
        towers[tid] = nt

    print()
    print("=" * 70)
    print("ENEMIES  (reward_gold: old -> new = HP x income x k_special)")
    print("=" * 70)
    print(f"{'enemy':<16}{'HP':>5}{'gold_old':>9}{'gold_new':>9}{'k':>5}")
    for eid, e in enemies.items():
        if e.get('is_boss'):
            new = BOSS_REWARD
            k = 1.0
        else:
            k = K_SPECIAL.get(eid, 1.0)
            new = max(1, round(e['health'] * INCOME_RATE * k))
        print(f"{eid:<16}{e['health']:>5}{e['reward_gold']:>9}{new:>9}{k:>5.1f}")
        e['reward_gold'] = new

    print()
    print("=" * 70)
    print("WAVE_CONFIG (recommended) — apply вручную в systems/wave/config.py:")
    print("=" * 70)
    for k, v in WAVE.items():
        print(f"  {k:<24} = {v}")
    print(f"  boss_base_hp             = {BOSS_BASE_HP}")
    print(f"  boss_hp_per_level        = {BOSS_HP_PER_LEVEL}")

    if args.apply:
        json.dump(towers, open(f'{ROOT}/data/configs/towers.json', 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=2)
        json.dump(enemies, open(f'{ROOT}/data/configs/enemies.json', 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=2)
        print("\n[APPLIED] towers.json + enemies.json written.")
    else:
        print("\n[DRY-RUN] nothing written. Re-run with --apply to write JSON.")


if __name__ == '__main__':
    main()
