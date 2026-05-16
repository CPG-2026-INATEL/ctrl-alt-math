import pygame
import settings
from i18n import t
from scenes.scene import Scene
from achievement_manager import AchievementManager

class AchievementScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.manager = AchievementManager()
        self.selected_index = 0
        self.ach_list = list(self.manager.achievements.values())
        self.scroll_y = 0

    def enter(self, prev_scene=None):
        self.selected_index = 0
        self.scroll_y = 0
        self._speak_selection()

    def _speak_selection(self):
        ach = self.ach_list[self.selected_index]
        name = t(ach["name"])
        desc = t(ach["desc"])
        stars = self.manager.get_stars(ach["id"])
        status = t(f"ach_stars_{stars}") if stars > 0 else t("ach_locked")
        self.game.tts.speak(f"{name}. {desc}. {status}", lang=settings.LANGUAGE)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self.game.sfx.play("menu_select")
            self.game.scene_manager.switch("menu")
        elif event.key == pygame.K_UP:
            if self.selected_index > 0:
                self.selected_index -= 1
                self.game.sfx.play("menu_select")
                self._speak_selection()
        elif event.key == pygame.K_DOWN:
            if self.selected_index < len(self.ach_list) - 1:
                self.selected_index += 1
                self.game.sfx.play("menu_select")
                self._speak_selection()
        elif event.key == pygame.K_r:
            self.manager.reset()
            self.game.sfx.play("victory") # Positive feedback
            self._speak_selection()

    def update(self, dt):
        # Update scroll to keep selected item visible
        item_h = 80
        view_h = settings.WINDOW_HEIGHT - 160
        target_scroll = self.selected_index * item_h - view_h // 2 + item_h // 2
        max_scroll = max(0, len(self.ach_list) * item_h - view_h)
        target_scroll = max(0, min(max_scroll, target_scroll))
        self.scroll_y += (target_scroll - self.scroll_y) * dt * 10

    def draw(self, screen):
        self.game.ui.draw_achievements(screen, self.ach_list, self.selected_index, self.scroll_y)
