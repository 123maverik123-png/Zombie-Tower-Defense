# core/__init__.py
# Пустой намеренно: подмодули импортируются напрямую (from core.states import ...,
# from core.event_bus import EventBus). Раньше здесь были агрегирующие импорты
# всех состояний игры — из-за них любой `from core.X import ...` протягивал
# core.states -> systems.wave -> entities.enemy и создавал циклический импорт.
# Никто не использует `from core import ...`, поэтому агрегирование убрано.
