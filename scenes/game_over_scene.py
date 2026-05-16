import pygame

import settings
from scenes.scene import Scene


class GameOverScene(Scene):
    overlay = True

    def __init__(self, game):
        super().__init__(game)

    def _return_rect(self):
        font = pygame.font.Font(None, 18)
        return font.render("x", True, (0, 0, 0)).get_rect(center=(settings.WINDOW_WIDTH // 2, 380)).inflate(340, 26)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._return_rect().collidepoint(event.pos):
                self.game.reset_player_state()
                self.game.sfx.play("menu_select")
                self.game.scene_manager.switch("menu")
            return

        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
            self.game.reset_player_state()
            self.game.sfx.play("menu_select")
            self.game.scene_manager.switch("menu")

    def update(self, dt):
        self.game.particles.update(dt)
        self.game.floating_text.update(dt)

    def enter(self, prev_scene=None):
        self.game.sfx.play("game_over")

    def draw(self, screen):
        gameplay = self.game.scene_manager.scenes.get("gameplay")
        if gameplay:
            gameplay.draw(screen)

        room_name = ""
        if self.game.current_room:
            room_name = self.game.current_room.name
        self.game.ui.draw_game_over(screen, room_name)
