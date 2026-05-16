import pygame

from scenes.scene import Scene


class PauseScene(Scene):
    overlay = True

    def __init__(self, game):
        super().__init__(game)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.game.scene_manager.pop()
        elif event.key == pygame.K_q:
            self.game.sfx.play("menu_select")
            self.game.scene_manager.switch("menu")

    def update(self, dt):
        pass

    def draw(self, screen):
        self.game.scene_manager.get("gameplay").draw(screen)
        self.game.ui.draw_pause(screen)
