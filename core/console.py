# core/console.py
import pygame
import sys
from typing import List, Dict, Any

class DevConsole:
    """Консоль разработчика для отладки и читов"""
    
    def __init__(self, game):
        self.game = game
        self.active = False
        self.input_text = ""
        self.history: List[str] = []
        self.output: List[str] = []
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.max_history = 100
        self.history_index = 0
        
        # Команды
        self.commands = {
            'help': self._cmd_help,
            'god': self._cmd_god,
            'freeze': self._cmd_freeze,
            'money': self._cmd_money,
            'kill_all': self._cmd_kill_all,
            'spawn': self._cmd_spawn,
            'speed': self._cmd_speed,
            'toggle_build': self._cmd_toggle_build,
            'lives': self._cmd_lives,
            'level': self._cmd_level,
            'clear': self._cmd_clear,
            'exit': self._cmd_exit,
            'unlock_all': self._cmd_unlock_all,
            'unlock_levels': self._cmd_unlock_levels,  # ✅ НОВАЯ КОМАНДА
            'set_level': self._cmd_set_level,          # ✅ НОВАЯ КОМАНДА
        }
        
        self._cmd_help()
    
    def toggle(self):
        """Открыть/закрыть консоль"""
        self.active = not self.active
        if self.active:
            self.input_text = ""
            self.history_index = len(self.history)
    
    def handle_event(self, event):
        """Обработка событий клавиатуры"""
        if not self.active:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self._execute_command()
                self.input_text = ""
                return True
            elif event.key == pygame.K_ESCAPE:
                self.active = False
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
                return True
            elif event.key == pygame.K_UP:
                if self.history_index > 0:
                    self.history_index -= 1
                    if self.history_index < len(self.history):
                        self.input_text = self.history[self.history_index]
                return True
            elif event.key == pygame.K_DOWN:
                if self.history_index < len(self.history) - 1:
                    self.history_index += 1
                    self.input_text = self.history[self.history_index]
                else:
                    self.history_index = len(self.history)
                    self.input_text = ""
                return True
            else:
                if event.unicode and event.unicode.isprintable():
                    self.input_text += event.unicode
                    return True
        
        return False
    
    def _execute_command(self):
        """Выполняет введённую команду"""
        if not self.input_text.strip():
            return
        
        self.history.append(self.input_text)
        if len(self.history) > self.max_history:
            self.history.pop(0)
        
        self.history_index = len(self.history)
        
        parts = self.input_text.strip().split()
        cmd = parts[0].lower() if parts else ""
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd in self.commands:
            self.commands[cmd](args)
        else:
            self._add_output(f"Unknown command: {cmd}. Type 'help' for list.")
    
    def _add_output(self, text: str):
        """Добавляет строку в вывод консоли"""
        self.output.append(text)
        if len(self.output) > 50:
            self.output.pop(0)
    
    def _get_play_state(self):
        """Получает текущее состояние игры"""
        state = self.game.state_manager.get_current_state()
        if state.__class__.__name__ == 'PlayState':
            return state
        return None
    
    # === КОМАНДЫ ===
    
    def _cmd_help(self, args=None):
        """Показывает список команд"""
        self._add_output("=== Available Commands ===")
        self._add_output("  help          - Show this help")
        self._add_output("  god           - Toggle god mode (enemies don't move)")
        self._add_output("  freeze        - Freeze all enemies")
        self._add_output("  money [amount]- Add gold (default: 9999)")
        self._add_output("  kill_all      - Kill all enemies on screen")
        self._add_output("  spawn <type>  - Spawn enemy (normal/fast/tank/night/flying)")
        self._add_output("  speed <num>   - Set game speed (0.5, 1.0, 2.0, 5.0)")
        self._add_output("  toggle_build  - Toggle build mode")
        self._add_output("  lives <num>   - Set lives")
        self._add_output("  level <num>   - Jump to level")
        self._add_output("  clear         - Clear console")
        self._add_output("  exit          - Close console")
        self._add_output("  unlock_all    - Unlock all towers and walls")
        self._add_output("  unlock_levels - Unlock all 50 levels")
        self._add_output("  set_level <n> - Set current level number (unlock previous)")
    
    def _cmd_unlock_all(self, args=None):
        """Открывает все башни для текущего уровня"""
        play = self._get_play_state()
        if not play:
            self._add_output("Not in game!")
            return
        
        play.level_number = 50
        
        if hasattr(play, 'ui_logic'):
            play.ui_logic.tower_buttons = []
        
        self._add_output("✅ All towers unlocked! (Level set to 50)")
        self._add_output("   Available towers: Sniper, Turret, Flamethrower,")
        self._add_output("   Electric, Water, PVO, Freeze, Gate, Wall")
    
    def _cmd_unlock_levels(self, args=None):
        """Открывает все 50 уровней в меню выбора уровней"""
        from services.save_system import SaveSystem
        save = SaveSystem()
        level_data = save.load_level_data()
        
        # Открываем все уровни
        for i in range(1, 51):
            level_data.complete_level(i)
        
        level_data.unlocked_level = 50
        save.save_level_data(level_data)
        
        self._add_output("✅ All 50 levels unlocked!")
        self._add_output("   Go to LEVEL SELECT to see them.")
    
    def _cmd_set_level(self, args=None):
        """Устанавливает текущий уровень (открывает предыдущие)"""
        if not args or not args[0].isdigit():
            self._add_output("Usage: set_level <number>")
            self._add_output("   Example: set_level 25")
            return
        
        level = int(args[0])
        if level < 1 or level > 50:
            self._add_output("Level must be between 1 and 50")
            return
        
        from services.save_system import SaveSystem
        save = SaveSystem()
        level_data = save.load_level_data()
        
        # Открываем все уровни до указанного
        for i in range(1, level + 1):
            level_data.complete_level(i)
        
        level_data.unlocked_level = level + 1
        if level_data.unlocked_level > 50:
            level_data.unlocked_level = 50
        
        save.save_level_data(level_data)
        
        # Если мы в игре — обновляем текущий уровень
        play = self._get_play_state()
        if play:
            play.level_number = level
        
        self._add_output(f"✅ Level {level} unlocked!")
        self._add_output(f"   Next level: {level_data.unlocked_level}")
        self._add_output("   Go to LEVEL SELECT to see changes.")
    
    def _cmd_god(self, args=None):
        """Включает/выключает режим бога"""
        play = self._get_play_state()
        if not play:
            self._add_output("Not in game!")
            return
        
        if not hasattr(play, 'god_mode'):
            play.god_mode = False
        
        play.god_mode = not play.god_mode
        state = "ON" if play.god_mode else "OFF"
        self._add_output(f"God mode: {state}")
    
    def _cmd_freeze(self, args=None):
        """Замораживает всех врагов"""
        play = self._get_play_state()
        if not play:
            self._add_output("Not in game!")
            return
        
        if not hasattr(play, 'frozen'):
            play.frozen = False
        
        play.frozen = not play.frozen
        state = "ON" if play.frozen else "OFF"
        self._add_output(f"❄️ Freeze: {state}")
        
        if play.frozen:
            for enemy in play.enemies:
                enemy.speed = 0
            self._add_output(f"🧊 Frozen {len(play.enemies)} enemies!")
        else:
            for enemy in play.enemies:
                enemy.speed = enemy.config.get('speed', 90)
            self._add_output(f"🔥 Unfrozen all enemies!")
    
    def _cmd_money(self, args=None):
        """Добавляет золото"""
        play = self._get_play_state()
        if not play:
            self._add_output("Not in game!")
            return
        
        amount = 9999
        if args and args[0].isdigit():
            amount = int(args[0])
        
        play.player.gold += amount
        self._add_output(f"Added {amount} gold. Total: {play.player.gold}")
    
    def _cmd_kill_all(self, args=None):
        """Убивает всех врагов"""
        play = self._get_play_state()
        if not play:
            self._add_output("Not in game!")
            return
        
        count = len(play.enemies)
        for enemy in play.enemies[:]:
            enemy.health = 0
            enemy.alive = False
            enemy.on_death()
        self._add_output(f"Killed {count} enemies!")
    
    def _cmd_spawn(self, args=None):
        """Спавнит врага"""
        play = self._get_play_state()
        if not play:
            self._add_output("Not in game!")
            return
        
        enemy_type = args[0] if args and args[0] in ['normal', 'fast', 'tank', 'night', 'flying'] else 'normal'
        enemy_id = f"zombie_{enemy_type}"
        
        config = play.enemy_configs.get(enemy_id)
        if not config:
            self._add_output(f"Enemy type '{enemy_type}' not found!")
            return
        
        if play.path and len(play.path) > 0:
            from entities.enemy import Enemy
            from entities.enemy_factory import EnemyFactory
            
            config_copy = config.copy()
            config_copy['id'] = enemy_id
            
            enemy = EnemyFactory.create(config_copy, play.path)
            play.enemies.append(enemy)
            self._add_output(f"Spawned {enemy_type} enemy!")
        else:
            self._add_output("No path found!")
    
    def _cmd_speed(self, args=None):
        """Меняет скорость игры"""
        play = self._get_play_state()
        if not play:
            self._add_output("Not in game!")
            return
        
        if not args or not args[0].replace('.', '').isdigit():
            self._add_output("Usage: speed <0.5|1.0|2.0|5.0>")
            return
        
        speed = float(args[0])
        if speed < 0.1 or speed > 10:
            self._add_output("Speed must be between 0.1 and 10.0")
            return
        
        play.game_speed = speed
        self._add_output(f"Game speed set to: {speed}x")
    
    def _cmd_toggle_build(self, args=None):
        """Переключает режим строительства"""
        play = self._get_play_state()
        if not play:
            self._add_output("Not in game!")
            return
        
        play.building_mode = not play.building_mode
        state = "ON" if play.building_mode else "OFF"
        self._add_output(f"Build mode: {state}")
    
    def _cmd_lives(self, args=None):
        """Устанавливает количество жизней"""
        play = self._get_play_state()
        if not play:
            self._add_output("Not in game!")
            return
        
        if not args or not args[0].isdigit():
            self._add_output("Usage: lives <number>")
            return
        
        lives = int(args[0])
        play.player.lives = lives
        self._add_output(f"Lives set to: {lives}")
    
    def _cmd_level(self, args=None):
        """Переход на уровень"""
        play = self._get_play_state()
        if not play:
            self._add_output("Not in game!")
            return
        
        if not args or not args[0].isdigit():
            self._add_output("Usage: level <number>")
            return
        
        level = int(args[0])
        if level < 1 or level > 50:
            self._add_output("Level must be between 1 and 50")
            return
        
        from core.level_loader import build_level
        from core.states.play.state import PlayState
        
        level_data = build_level(level)
        new_state = PlayState(self.game, level, level_data)
        self.game.state_manager.add_state('PLAYING', new_state)
        self.game.state_manager.change_state('PLAYING')
        self._add_output(f"Jumped to level: {level}")
    
    def _cmd_clear(self, args=None):
        """Очищает консоль"""
        self.output.clear()
    
    def _cmd_exit(self, args=None):
        """Закрывает консоль"""
        self.active = False
    
    def draw(self, screen):
        """Отрисовывает консоль"""
        if not self.active:
            return
        
        screen_width, screen_height = screen.get_size()
        
        console_height = min(400, screen_height // 2)
        bg_rect = pygame.Rect(0, screen_height - console_height, screen_width, console_height)
        pygame.draw.rect(screen, (0, 0, 0, 220), bg_rect)
        pygame.draw.rect(screen, (100, 100, 150), bg_rect, 2)
        
        y_offset = screen_height - console_height + 10
        for line in self.output[-15:]:
            text = self.small_font.render(line, True, (200, 255, 200))
            screen.blit(text, (10, y_offset))
            y_offset += 20
        
        input_y = screen_height - 30
        prompt = self.font.render("> ", True, (255, 255, 255))
        screen.blit(prompt, (10, input_y))
        
        input_text = self.font.render(self.input_text, True, (255, 255, 100))
        screen.blit(input_text, (35, input_y))
        
        cursor_x = 35 + input_text.get_width()
        if pygame.time.get_ticks() % 1000 < 500:
            pygame.draw.line(screen, (255, 255, 255), 
                           (cursor_x, input_y + 2), 
                           (cursor_x, input_y + 22), 2)