# entities/enemy/states.py

class EnemyStates:
    """Состояния врага: spawning → alive → dying → corpse → fading → dead.

    spawning — проявляется из пустоты (альфа 0 → 255), стоит на месте
    dying  — падает на спину (поворот до 45°)
    corpse — лежит corpse_duration секунд
    fading — растворяется fade_duration секунд (альфа 255 → 0)
    dead   — удаляется из state.enemies
    """

    FALL_ANGLE = 45

    def __init__(self, enemy):
        self.enemy = enemy
        self.state = 'spawning'
        self.spawn_timer = 0.6
        self.spawn_duration = 0.6
        self.death_timer = 0.0
        self.death_duration = 0.8
        self.corpse_timer = 0.0
        self.corpse_duration = 4.0
        self.fade_timer = 0.0
        self.fade_duration = 1.0
        self.fall_angle = 0
        self.fall_speed = 0
        self.fall_y_offset = 0
        self.death_x = 0
        self.death_y = 0

    def update(self, dt: float) -> bool:
        enemy = self.enemy

        if self.state == 'dead':
            return False

        if self.state == 'spawning':
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                self.state = 'alive'
            return False  # во время появления враг не двигается

        if self.state == 'fading':
            self.fade_timer -= dt
            if self.fade_timer <= 0:
                self.state = 'dead'
            return False

        if self.state == 'corpse':
            self.corpse_timer -= dt
            if self.corpse_timer <= 0:
                self.state = 'fading'
                self.fade_timer = self.fade_duration
            return False

        if self.state == 'dying':
            self.death_timer -= dt
            # Плавный поворот до FALL_ANGLE за время падения
            progress = 1.0 - max(0.0, self.death_timer / self.death_duration)
            self.fall_angle = self.FALL_ANGLE * progress
            self.fall_speed += dt * 100
            self.fall_y_offset += self.fall_speed * dt

            if self.death_timer <= 0:
                self.state = 'corpse'
                self.corpse_timer = self.corpse_duration
                self.fall_angle = self.FALL_ANGLE
            return False

        if not enemy.alive or enemy.reached_end:
            return False

        return True

    def start_dying(self):
        """Запускает анимацию смерти."""
        enemy = self.enemy
        self.state = 'dying'
        self.death_timer = self.death_duration
        self.fall_angle = 0
        self.fall_speed = 0
        self.fall_y_offset = 0
        self.death_x = enemy.x   # <-- фиксируем позицию в момент смерти
        self.death_y = enemy.y   # <-- чтобы тело не "прыгало"

    def get_death_alpha(self) -> int:
        """Альфа тела: 255 пока лежит, 255→0 во время растворения."""
        if self.state == 'fading':
            return max(0, int(255 * (self.fade_timer / self.fade_duration)))
        return 255

    def get_spawn_alpha(self) -> int:
        """Альфа при появлении: 0 → 255 за spawn_duration."""
        if self.state == 'spawning':
            return max(0, min(255, int(255 * (1.0 - self.spawn_timer / self.spawn_duration))))
        return 255

    def is_spawning(self) -> bool:
        return self.state == 'spawning'

    def is_alive(self) -> bool:
        return self.state == 'alive'

    def is_dying(self) -> bool:
        return self.state == 'dying'

    def is_corpse(self) -> bool:
        return self.state == 'corpse'

    def is_fading(self) -> bool:
        return self.state == 'fading'

    def is_dead(self) -> bool:
        return self.state == 'dead'
