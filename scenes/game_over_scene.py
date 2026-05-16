import pygame

from scenes.scene import Scene


class GameOverScene(Scene):
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
        self.game.sfx.play("game_over")

    def draw(self, screen):
        self.game.scene_manager.get("gameplay").draw(screen)
        self.game.ui.draw_game_over(screen, self.game.current_wave + 1)
