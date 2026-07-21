# data/levels_data.py
# 50 закрученных карт со спиралями и петлями, без самопересечений
# минимум 2 клетки зазора между непересекающимися участками пути
#
# Данные разбиты по десяткам уровней в data/levels/ (levels_01_10.py и т.д.),
# чтобы не читать 750 строк ради правки одного уровня. Здесь они собираются
# в единый словарь LEVELS — импортёры (core/level_loader.py) не меняются.

from data.levels.levels_01_10 import LEVELS as _L01
from data.levels.levels_11_20 import LEVELS as _L11
from data.levels.levels_21_30 import LEVELS as _L21
from data.levels.levels_31_40 import LEVELS as _L31
from data.levels.levels_41_50 import LEVELS as _L41

LEVELS = {**_L01, **_L11, **_L21, **_L31, **_L41}
