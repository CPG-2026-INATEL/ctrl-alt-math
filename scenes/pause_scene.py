import pygame

from scenes.scene import Scene


class PauseScene(Scene):
    overlay = True

    def __init__(self, game):
        super().__init__(game)

    def _resume_rect(self):
        font = pygame.font.Font(None, 20)
        return font.render("x", True, (0, 0, 0)).get_rect(
            center=(self.game.screen.get_width() // 2, self.game.screen.get_height() // 2)
        ).inflate(320, 26)

    def _quit_rect(self):
        font = pygame.font.Font(None, 18)
        return font.render("x", True, (0, 0, 0)).get_rect(
            center=(self.game.screen.get_width() // 2, self.game.screen.get_height() // 2 + 30)
        ).inflate(260, 26)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._resume_rect().collidepoint(event.pos):
                self.game.sfx.play("menu_select")
                self.game.scene_manager.pop()
            elif self._quit_rect().collidepoint(event.pos):
                self.game.sfx.play("menu_select")
                self.game.scene_manager.switch("menu")
            return

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
