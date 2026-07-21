# core/console/console.py
import pygame
from typing import List, Dict, Any

from .commands import ConsoleCommands


class DevConsole(ConsoleCommands):
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
            'unlock_levels': self._cmd_unlock_levels,
            'set_level': self._cmd_set_level,
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
