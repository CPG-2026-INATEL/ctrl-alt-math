import pygame

import settings
from i18n import t, LANG_EN, LANG_PT
from save_game import save_exists
from scenes.scene import Scene
from utils import draw_text


class MenuScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self._update_menu_items()
        self.selected = 0
        self.showing_how_to_play = False
        self.confirm_overwrite = False

    def _menu_item_rect(self, index):
        h = settings.WINDOW_HEIGHT
        item_size = max(20, int(h * 0.038))
        item_gap = max(36, int(h * 0.065))
        y_start = int(h * 0.47)
        text, _ = self.menu_items[index]
        font = pygame.font.Font(None, item_size)
        img = font.render(text, True, settings.WHITE)
        return img.get_rect(
            center=(settings.WINDOW_WIDTH // 2, y_start + index * item_gap)
        ).inflate(50, 20)

    def _update_menu_items(self):
        lang_str = "EN" if settings.LANGUAGE == LANG_EN else "PT"
        tts_str = "ON" if settings.TTS_ENABLED else "OFF"
        diff_str = t(f"difficulty_{settings.DIFFICULTY}")
        self.menu_items = [(t("menu_start"), "start")]
        if save_exists():
            self.menu_items.append((t("menu_continue"), "continue"))
        self.menu_items.extend([
            (t("menu_multiplayer"), "multiplayer"),
            (t("menu_how_to"), "how_to"),
            (t("menu_lore"), "lore"),
            (t("menu_achievements"), "achievements"),
            (f"{t('menu_language')}: {lang_str}", "language"),
            (f"{t('menu_difficulty')}: {diff_str}", "difficulty"),
            (f"TTS: {tts_str}", "tts"),
            (t("menu_quit"), "quit"),
        ])

    def enter(self, prev_scene=None):
        self.selected = 0
        self.showing_how_to_play = False
        self._update_menu_items()
        self._speak_selection()

    def _speak_selection(self):
        item_text, _ = self.menu_items[self.selected]
        self.game.tts.speak(item_text, lang=settings.LANGUAGE)

    def _speak_how_to_play(self):
        keys = [
            "how_to_title", "how_to_intro", "how_to_move", "how_to_combat",
            "how_to_space", "how_to_1", "how_to_2", "how_to_r",
            "how_to_skills", "how_to_tab", "how_to_spend", "how_to_prereq",
            "how_to_enemies", "how_to_censor", "how_to_strawman", "how_to_bayesian",
            "how_to_boss", "how_to_win", "how_to_return"
        ]
        cleaned_lines = []
        for key in keys:
            line = t(key)
            cleaned = line.strip().lstrip("-").strip()
            if cleaned:
                cleaned_lines.append(cleaned)
        
        full_text = ". ".join(cleaned_lines)
        self.game.tts.speak(full_text, lang=settings.LANGUAGE)

    def _activate_selected(self):
        self.game.sfx.play("menu_confirm")
        _, action = self.menu_items[self.selected]
        if action == "start":
            if save_exists():
                self.confirm_overwrite = True
            else:
                self.game.reset_game_state()
                self.game.save_progress()
                self.game.scene_manager.switch("map")
        elif action == "continue":
            if self.game.load_progress():
                self._update_menu_items()
                self.game.scene_manager.switch("map")
        elif action == "multiplayer":
            self.game.scene_manager.switch("lobby")
        elif action == "how_to":
            self.showing_how_to_play = True
            self._speak_how_to_play()
        elif action == "lore":
            self.game.scene_manager.switch("lore")
        elif action == "achievements":
            self.game.scene_manager.switch("achievements")
        elif action == "language":
            if settings.LANGUAGE == LANG_EN:
                settings.LANGUAGE = LANG_PT
            else:
                settings.LANGUAGE = LANG_EN
            self._update_menu_items()
            self._speak_selection()
        elif action == "difficulty":
            diffs = [settings.DIFFICULTY_EASY, settings.DIFFICULTY_MEDIUM, settings.DIFFICULTY_HARD]
            curr_idx = diffs.index(settings.DIFFICULTY)
            settings.DIFFICULTY = diffs[(curr_idx + 1) % len(diffs)]
            self._update_menu_items()
            self._speak_selection()
        elif action == "tts":
            settings.TTS_ENABLED = not settings.TTS_ENABLED
            self.game.tts.enabled = settings.TTS_ENABLED
            self._update_menu_items()
            self._speak_selection()
        elif action == "quit":
            self.game.running = False

    def handle_event(self, event):
        if self.showing_how_to_play:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    self.showing_how_to_play = False
                    self.game.sfx.play("menu_select")
                    self._speak_selection()
                elif event.key == pygame.K_SPACE:
                    self._speak_how_to_play()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.showing_how_to_play = False
                self.game.sfx.play("menu_select")
                self._speak_selection()
            return

        if self.confirm_overwrite:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.confirm_overwrite = False
                    self.game.reset_game_state()
                    self.game.save_progress()
                    self.game.scene_manager.switch("map")
                elif event.key == pygame.K_ESCAPE:
                    self.confirm_overwrite = False
                    self.game.sfx.play("menu_select")
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if event.pos[1] > settings.WINDOW_HEIGHT // 2:
                    self.confirm_overwrite = False
                    self.game.sfx.play("menu_select")
            return

        if event.type == pygame.MOUSEMOTION:
            for i in range(len(self.menu_items)):
                if self._menu_item_rect(i).collidepoint(event.pos):
                    if self.selected != i:
                        self.selected = i
                        self.game.sfx.play("menu_select")
                        self._speak_selection()
                    return
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i in range(len(self.menu_items)):
                if self._menu_item_rect(i).collidepoint(event.pos):
                    self.selected = i
                    self._activate_selected()
                    return
            return

        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_UP:
            self.selected = (self.selected - 1) % len(self.menu_items)
            self.game.sfx.play("menu_select")
            self._speak_selection()
        elif event.key == pygame.K_DOWN:
            self.selected = (self.selected + 1) % len(self.menu_items)
            self.game.sfx.play("menu_select")
            self._speak_selection()
        elif event.key == pygame.K_RETURN:
            self._activate_selected()

    def update(self, dt):
        pass

    def draw(self, screen):
        if self.confirm_overwrite:
            self.game.ui.draw_main_menu(screen, self.menu_items, self.selected)
            overlay = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(settings.BLACK)
            screen.blit(overlay, (0, 0))
            draw_text(screen, "Existing Save Found",
                     (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 - 50),
                     settings.GOLD, 24)
            draw_text(screen, "A save game already exists.",
                     (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 - 10),
                     settings.WHITE, 18)
            draw_text(screen, "Starting a new game will overwrite it.",
                     (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 + 15),
                     settings.LIGHT_GRAY, 16)
            draw_text(screen, "ENTER = Confirm     ESC = Cancel",
                     (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 + 60),
                     settings.GREEN, 16)
        elif self.showing_how_to_play:
            self.game.ui.draw_how_to_play(screen)
        else:
            self.game.ui.draw_main_menu(screen, self.menu_items, self.selected)
