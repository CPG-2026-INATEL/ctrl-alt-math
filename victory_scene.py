import pygame

import settings
from scene import Scene


class VictoryScene(Scene):
    overlay = True

    def __init__(self, game):
        super().__init__(game)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_RETURN:
            self.game.reset_game_state()
            self.game.scene_manager.switch("gameplay")
        elif event.key == pygame.K_ESCAPE:
            self.game.sfx.play("menu_select")
            self.game.scene_manager.switch("menu")

    def update(self, dt):
        self.game.particles.update(dt)
        self.game.floating_text.update(dt)

    def enter(self, prev_scene=None):
        self.game.particles.emit_burst(
            settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2,
            settings.GOLD, 50, 150, 1.0
        )
        self.game.sfx.play("victory")

    def draw(self, screen):
        self.game.scene_manager.get("gameplay").draw(screen)
        self.game.ui.draw_victory(screen)
