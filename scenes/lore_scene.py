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

    def _left_rect(self):
        return pygame.Rect(settings.WINDOW_WIDTH // 2 - 220, 70, 80, 40)

    def _right_rect(self):
        return pygame.Rect(settings.WINDOW_WIDTH // 2 + 140, 70, 80, 40)

    def _content_rect(self):
        return pygame.Rect(60, 120, settings.WINDOW_WIDTH - 120, settings.WINDOW_HEIGHT - 200)

    def _footer_rect(self):
        return pygame.Rect(settings.WINDOW_WIDTH // 2 - 220, settings.WINDOW_HEIGHT - 56, 440, 32)

    def enter(self, prev_scene=None):
        self.scroll_y = 0
        self._speak_category()

    def _speak_category(self):
        cat_key, content_key = LORE_CATEGORIES[self.category_index]
        full_text = f"{t(cat_key)}. {t(content_key)}"
        self.game.tts.speak(full_text, lang=settings.LANGUAGE)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Right click
            mx, my = event.pos
            content_rect = self._content_rect()
            if content_rect.collidepoint(mx, my):
                cat_key, content_key = LORE_CATEGORIES[self.category_index]
                font = pygame.font.Font(None, 22)
                wrapped_lines = self.game.ui._wrap_text(t(content_key), font, content_rect.width)
                
                line_height = 24
                relative_y = my - content_rect.y + self.scroll_y
                line_idx = int(relative_y // line_height)
                
                if 0 <= line_idx < len(wrapped_lines):
                    clicked_line = wrapped_lines[line_idx].strip()
                    if clicked_line:
                        self.game.tts.speak(clicked_line, lang=settings.LANGUAGE)
                        self.game.sfx.play("menu_select")
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._left_rect().collidepoint(event.pos):
                self.category_index = (self.category_index - 1) % len(LORE_CATEGORIES)
                self.scroll_y = 0
                self.game.sfx.play("menu_select")
                self._speak_category()
            elif self._right_rect().collidepoint(event.pos):
                self.category_index = (self.category_index + 1) % len(LORE_CATEGORIES)
                self.scroll_y = 0
                self.game.sfx.play("menu_select")
                self._speak_category()
            elif self._footer_rect().collidepoint(event.pos):
                self.game.sfx.play("menu_select")
                self.game.scene_manager.switch("menu")
            return

        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y = max(0, min(self.max_scroll, self.scroll_y - event.y * 40))
            return

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
            self._speak_category()

    def update(self, dt):
        pass

    def draw(self, screen):
        cat_key, content_key = LORE_CATEGORIES[self.category_index]
        self.max_scroll = self.game.ui.draw_lore(
            screen, cat_key, content_key, self.scroll_y, 
            self.category_index, len(LORE_CATEGORIES)
        )
