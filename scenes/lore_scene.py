import pygame
import settings
from i18n import t
from lore_data import LORE_CATEGORIES
from scenes.scene import Scene

class LoreScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.category_index = 0
        self.scroll_y = 0
        self.max_scroll = 0

    def enter(self, prev_scene=None):
        self.scroll_y = 0
        self._speak_category()

    def _speak_category(self):
        cat_key, _ = LORE_CATEGORIES[self.category_index]
        self.game.tts.speak(t(cat_key), lang=settings.LANGUAGE)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self.game.sfx.play("menu_select")
            self.game.scene_manager.switch("menu")
        elif event.key == pygame.K_LEFT:
            self.category_index = (self.category_index - 1) % len(LORE_CATEGORIES)
            self.scroll_y = 0
            self.game.sfx.play("menu_select")
            self._speak_category()
        elif event.key == pygame.K_RIGHT:
            self.category_index = (self.category_index + 1) % len(LORE_CATEGORIES)
            self.scroll_y = 0
            self.game.sfx.play("menu_select")
            self._speak_category()
        elif event.key == pygame.K_UP:
            self.scroll_y = max(0, self.scroll_y - 40)
        elif event.key == pygame.K_DOWN:
            self.scroll_y = min(self.max_scroll, self.scroll_y + 40)
        elif event.key == pygame.K_SPACE:
            # Read full content
            _, content_key = LORE_CATEGORIES[self.category_index]
            self.game.tts.speak(t(content_key), lang=settings.LANGUAGE)

    def update(self, dt):
        pass

    def draw(self, screen):
        cat_key, content_key = LORE_CATEGORIES[self.category_index]
        self.max_scroll = self.game.ui.draw_lore(
            screen, cat_key, content_key, self.scroll_y, 
            self.category_index, len(LORE_CATEGORIES)
        )
