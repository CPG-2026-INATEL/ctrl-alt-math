import pygame

import settings
from i18n import t, LANG_EN, LANG_PT
from scenes.scene import Scene


class MenuScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self._update_menu_items()
        self.selected = 0
        self.showing_how_to_play = False

    def _update_menu_items(self):
        lang_str = "EN" if settings.LANGUAGE == LANG_EN else "PT"
        tts_str = "ON" if settings.TTS_ENABLED else "OFF"
        diff_str = t(f"difficulty_{settings.DIFFICULTY}")
        self.menu_items = [
            (t("menu_start"), ""),
            (t("menu_multiplayer"), ""),
            (t("menu_how_to"), ""),
            (t("menu_lore"), ""),
            (t("menu_achievements"), ""),
            (f"{t('menu_language')}: {lang_str}", ""),
            (f"{t('menu_difficulty')}: {diff_str}", ""),
            (f"TTS: {tts_str}", ""),
            (t("menu_quit"), "")
        ]

    def enter(self, prev_scene=None):
        self.selected = 0
        self.showing_how_to_play = False
        self._update_menu_items()
        self._speak_selection()

    def _speak_selection(self):
        item_text, _ = self.menu_items[self.selected]
        self.game.tts.speak(item_text, lang=settings.LANGUAGE)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if self.showing_how_to_play:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                self.showing_how_to_play = False
                self.game.sfx.play("menu_select")
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
            self.game.sfx.play("menu_confirm")
            if self.selected == 0:
                self.game.reset_game_state()
                self.game.scene_manager.switch("map")
            elif self.selected == 1:
                self.game.scene_manager.switch("lobby")
            elif self.selected == 2:
                self.showing_how_to_play = True
            elif self.selected == 3:
                self.game.scene_manager.switch("lore")
            elif self.selected == 4:
                self.game.scene_manager.switch("achievements")
            elif self.selected == 5:
                # Toggle Language
                if settings.LANGUAGE == LANG_EN:
                    settings.LANGUAGE = LANG_PT
                else:
                    settings.LANGUAGE = LANG_EN
                self._update_menu_items()
                self._speak_selection()
            elif self.selected == 6:
                # Cycle Difficulty
                diffs = [settings.DIFFICULTY_EASY, settings.DIFFICULTY_MEDIUM, settings.DIFFICULTY_HARD]
                curr_idx = diffs.index(settings.DIFFICULTY)
                settings.DIFFICULTY = diffs[(curr_idx + 1) % len(diffs)]
                self._update_menu_items()
                self._speak_selection()
            elif self.selected == 7:
                # Toggle TTS
                settings.TTS_ENABLED = not settings.TTS_ENABLED
                self.game.tts.enabled = settings.TTS_ENABLED
                self._update_menu_items()
                self._speak_selection()
            elif self.selected == 8:
                self.game.running = False

    def update(self, dt):
        pass

    def draw(self, screen):
        if self.showing_how_to_play:
            self.game.ui.draw_how_to_play(screen)
        else:
            self.game.ui.draw_main_menu(screen, self.menu_items, self.selected)
