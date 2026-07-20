# core/states/level_select_state.py
import pygame
import os
import json
from core.state_manager import State
from core.audio import AudioManager
from core.level_loader import build_level
from services.profile_manager import ProfileManager
from ui.level_select import LevelSelectUI
from .play.state import PlayState
from core.font_loader import load_font, load_title_font
from core.theme import (
    GOLD, GOLD_BRIGHT, GOLD_DIM, STONE_DARK, STONE_MID, STONE_LIGHT,
    PARCHMENT, PARCHMENT_DIM, TEAL_GLOW, DANGER_BRIGHT
)


def _draw_glow(screen, rect, color, pad=8, alpha=60, radius=10):
    glow = pygame.Surface((rect.width + pad * 2, rect.height + pad * 2), pygame.SRCALPHA)
    pygame.draw.rect(glow, (*color, alpha), glow.get_rect(), border_radius=radius)
    screen.blit(glow, (rect.x - pad, rect.y - pad))


class LevelSelectState(State):
    def __init__(self, game):
        super().__init__(game)

        # Останавливаем все звуковые эффекты при входе в выбор уровня
        self.audio = AudioManager()
        self.audio.stop_all_sfx()

        # ✅ ВСЕ атрибуты — до любых ранних выходов. Иначе состояние,
        # созданное при старте игры (когда профиля ещё нет), остаётся
        # полусобранным и роняет игру при change_state из окна победы.
        self._music_started = False
        self.click_cooldown = 0.0
        self.show_name_input = False
        self.input_name = ""
        self.pending_custom_map = None
        self.error_message = ""
        self.error_timer = 0
        self.title_font = load_title_font(40)
        self.font = load_font(30)
        self.small_font = load_font(20)

        self.back_hovered = False
        self.background = None
        self._load_background()

        self.ui = None
        self.profile_manager = ProfileManager()
        self.profile = self.profile_manager.get_current_profile()

        if self.profile:
            self.ui = LevelSelectUI(self.profile, self.game)
        else:
            print("⚠️ No profile in LevelSelect, going to menu")
            self.game.state_manager.change_state('MENU')

    def _ensure_profile(self) -> bool:
        """Подтягивает актуальный профиль (мог появиться/смениться после создания состояния).

        Возвращает False, если профиля нет — тогда уходим в меню.
        """
        current = self.profile_manager.get_current_profile()
        if current is None:
            print("⚠️ No profile in LevelSelect, going to menu")
            self.game.state_manager.change_state('MENU')
            return False

        if (current is not self.profile or self.ui is None
                or self.ui.unlocked_level != current.unlocked_level
                or self.ui.completed_levels != current.completed_levels):
            # Профиль сменился или прогресс обновился (победа разблокировала уровень)
            self.profile = current
            self.ui = LevelSelectUI(self.profile, self.game)
        return True

    def _load_background(self):
        bg_path = "assets/images/menu_bg.jpg"
        if os.path.exists(bg_path):
            try:
                self.background = pygame.image.load(bg_path).convert()
            except Exception:
                self.background = None
        else:
            self.background = None

    def handle_events(self, events):
        if self.ui is None:
            return
        for event in events:
            if event.type == pygame.MOUSEMOTION:
                self.ui.update_hover(event.pos)
                self.back_hovered = self.ui.back_btn.collidepoint(event.pos)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.click_cooldown <= 0:
                    if self.ui.back_btn.collidepoint(event.pos):
                        self._go_back()
                        return

                    if hasattr(self.ui, 'custom_btn') and self.ui.custom_btn.collidepoint(event.pos):
                        self.ui.toggle_custom()
                        return

                    deleted_file = self.ui.handle_delete_click(event.pos)
                    if deleted_file:
                        self._delete_custom_map(deleted_file)
                        return

                    if self.ui.show_custom and hasattr(self.ui, 'back_custom_btn'):
                        if self.ui.back_custom_btn.collidepoint(event.pos):
                            self.ui.toggle_custom()
                            return

                    if self.ui.handle_click(event.pos):
                        self.click_cooldown = 0.3
                        self.audio.play_sound("button_click")

                        if self.ui.show_custom:
                            custom_maps = self.ui.get_custom_maps()
                            idx = self.ui.selected_custom_index
                            if 0 <= idx < len(custom_maps):
                                map_data = custom_maps[idx]['data']
                                self._start_custom_level(map_data)
                        else:
                            level_num = self.ui.selected_level

                            if self.profile and not self.profile.is_unlocked(level_num):
                                self.error_message = f"Level {level_num} is locked!"
                                self.error_timer = 120
                                return

                            if self.profile:
                                self.profile.current_level = level_num
                                self.profile_manager.save_profile(self.profile)

                            level_data = build_level(level_num)
                            
                            # ✅ Убираем старый PlayState, если он существует
                            if 'PLAYING' in self.game.state_manager._states:
                                del self.game.state_manager._states['PLAYING']
                            
                            play_state = PlayState(self.game, level_num, level_data)
                            self.game.state_manager.add_state('PLAYING', play_state)
                            self.game.state_manager.change_state('PLAYING')

    def _delete_custom_map(self, filename):
        filepath = f"data/maps/{filename}"
        if os.path.exists(filepath):
            os.remove(filepath)
            self.ui._load_custom_maps()
            self.audio.play_sound("button_click")
            self.error_message = f"Deleted: {filename}"
            self.error_timer = 120

    def _generate_custom_waves(self):
        return [
            {'enemies': {'zombie_normal': 5}, 'total_enemies': 5, 'spawn_delay': 1.0, 'is_boss_wave': False},
            {'enemies': {'zombie_normal': 8}, 'total_enemies': 8, 'spawn_delay': 0.8, 'is_boss_wave': False},
            {'enemies': {'zombie_normal': 12}, 'total_enemies': 12, 'spawn_delay': 0.6, 'is_boss_wave': False},
        ]

    def _start_custom_level(self, map_data):
        waypoints = map_data.get('waypoints', [])
        if len(waypoints) < 2:
            self.error_message = "Map has no waypoints!"
            self.error_timer = 120
            return

        tile_size = map_data.get('tile_size', 65)
        path_pixels = []
        for wx, wy in waypoints:
            px = wx * tile_size + tile_size // 2
            py = wy * tile_size + tile_size // 2
            path_pixels.append((px, py))

        waves = self._generate_custom_waves()

        level_data = {
            'name': map_data.get('name', 'Custom Level'),
            'tile_size': tile_size,
            'map': map_data['map'],
            'path': path_pixels,
            'waves': waves,
            'start_x': path_pixels[0][0] if path_pixels else 100,
            'start_y': path_pixels[0][1] if path_pixels else 100,
            'end_x': path_pixels[-1][0] if path_pixels else 100,
            'end_y': path_pixels[-1][1] if path_pixels else 100
        }

        # ✅ Убираем старый PlayState, если он существует
        if 'PLAYING' in self.game.state_manager._states:
            del self.game.state_manager._states['PLAYING']

        play_state = PlayState(self.game, 0, level_data)
        self.game.state_manager.add_state('PLAYING', play_state)
        self.game.state_manager.change_state('PLAYING')

    def update(self, dt):
        if not self._ensure_profile():
            return
        if self.click_cooldown > 0:
            self.click_cooldown -= dt
        if self.error_timer > 0:
            self.error_timer -= 1

    def draw(self, screen):
        screen_w, screen_h = self.game.render_width, self.game.render_height

        self._draw_background(screen, screen_w, screen_h)

        panel_rect = pygame.Rect(50, 50, screen_w - 100, screen_h - 100)
        panel_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel_surface.fill((*STONE_DARK, 190))
        screen.blit(panel_surface, (panel_rect.x, panel_rect.y))
        pygame.draw.rect(screen, GOLD, panel_rect, 2, border_radius=8)

        title = self.title_font.render("SELECT LEVEL", True, GOLD)
        title_shadow = self.title_font.render("SELECT LEVEL", True, (0, 0, 0))
        screen.blit(title_shadow, (panel_rect.x + 32, panel_rect.y + 22))
        screen.blit(title, (panel_rect.x + 30, panel_rect.y + 20))

        if self.profile:
            mode_text = "HARDCORE" if self.profile.mode == 'hardcore' else "NORMAL"
            mode_color = DANGER_BRIGHT if self.profile.mode == 'hardcore' else GOLD
            mode_info = self.small_font.render(f"{mode_text}  •  {self.profile.name}", True, mode_color)
            screen.blit(mode_info, (screen_w - mode_info.get_width() - 70, 70))

        if self.ui is not None:
            self.ui.draw(screen)

        if self.error_timer > 0:
            text = self.font.render(self.error_message, True, DANGER_BRIGHT)
            screen.blit(text, (screen_w // 2 - text.get_width() // 2, screen_h - 60))

    def _draw_background(self, screen, screen_w, screen_h):
        screen.fill((15, 14, 12))
        if self.background:
            bg_scaled = pygame.transform.scale(self.background, (screen_w, screen_h))
            screen.blit(bg_scaled, (0, 0))
        else:
            for i in range(screen_h):
                t = i / screen_h
                r = int(15 + 25 * t)
                g = int(14 + 18 * t)
                b = int(18 + 30 * t)
                pygame.draw.line(screen, (r, g, b), (0, i), (screen_w, i))

        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

    def _go_back(self):
        self.click_cooldown = 0.3
        self.audio.play_sound("button_click")
        
        # Останавливаем все звуковые эффекты перед переходом в меню
        self.audio.stop_all_sfx()

        if self.audio.settings.music_enabled:
            self.audio.play_music("menu_theme.wav")

        self.game.state_manager.change_state('MENU')

    def on_resolution_changed(self, screen_w, screen_h):
        pass