# core/states/play/enemies.py
from entities.enemy import Enemy
from entities.enemy_factory import EnemyFactory


class PlayEnemies:
    def __init__(self, state):
        self.state = state

    def spawn(self, enemy_type):
        state = self.state
        enemy_id = f"zombie_{enemy_type}"
        config = state.enemy_configs.get(enemy_id)
        if not config:
            return False

        if state.path and len(state.path) > 0:
            config_copy = config.copy()
            config_copy['id'] = enemy_id
            enemy = EnemyFactory.create(config_copy, state.path)
            state.enemies.append(enemy)
            return True
        return False

    def kill_all(self):
        state = self.state
        count = len(state.enemies)
        for enemy in state.enemies[:]:
            enemy.health = 0
            enemy.alive = False
            enemy.on_death()
        return count

    def update(self, dt):
        state = self.state
        if state.frozen:
            return

        for enemy in state.enemies:
            enemy.update(dt)

    def clear_dead_bodies(self):
        state = self.state
        removed = 0
        for enemy in state.enemies[:]:
            if enemy.states.is_dead():
                state.enemies.remove(enemy)
                removed += 1
        return removed