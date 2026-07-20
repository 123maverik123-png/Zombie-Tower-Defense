# tests/test_enemy.py
import pytest
import pygame
from entities.enemy import Enemy
from entities.tower import Tower
from systems.wave_manager import WaveManager

def test_enemy_creation():
    """Тест создания врага"""
    config = {
        'id': 'zombie',
        'health': 100,
        'speed': 50,
        'reward_gold': 10
    }
    path = [(0, 0), (100, 0), (100, 100)]
    enemy = Enemy(config, path)

    assert enemy.health == 100
    assert enemy.speed == 50
    assert enemy.alive is True
    assert enemy.x == 0
    assert enemy.y == 0

def test_enemy_movement():
    """Тест движения врага"""
    config = {'speed': 100}
    path = [(0, 0), (100, 0)]
    enemy = Enemy(config, path)

    enemy.update(0.5)
    assert enemy.x == 50
    assert enemy.y == 0

    enemy.update(0.5)
    assert enemy.x == 100
    assert enemy.y == 0
    assert enemy.current_target_index == 2

def test_enemy_takes_damage():
    """Тест получения урона"""
    config = {'health': 100}
    enemy = Enemy(config, [(0, 0)])

    damage = enemy.take_damage(30)
    assert damage == 30
    assert enemy.health == 70
    assert enemy.alive is True

    damage = enemy.take_damage(80)
    assert enemy.health == 0
    assert enemy.alive is False

def test_tower_finds_target():
    """Тест поиска цели башней"""
    pygame.init()
    tower = Tower(0, 0, {'range': 100, 'damage': 10, 'fire_rate': 1})

    enemies = []
    for i in range(3):
        config = {'health': 100}
        enemy = Enemy(config, [(i * 50, 0)])
        enemies.append(enemy)

    target = tower._find_target(enemies)
    assert target is not None
    assert target.x == 0

def test_wave_manager_spawning():
    """Тест спавна волн"""
    wave_data = [{
        'enemies': [{'id': 'zombie', 'weight': 1}],
        'count': 3,
        'spawn_delay': 0.5
    }]
    path = [(0, 0), (100, 0)]

    manager = WaveManager(wave_data, path)
    manager.start_next_wave()

    enemies = []
    enemy = manager.update(0.6)
    if enemy:
        enemies.append(enemy)

    assert len(enemies) == 1

    enemy = manager.update(0.6)
    if enemy:
        enemies.append(enemy)

    assert len(enemies) == 2
