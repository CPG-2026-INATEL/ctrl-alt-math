import pygame

from scenes.scene import Scene


class GameOverScene(Scene):
    overlay = True

    def __init__(self, game):
        super().__init__(game)

    def handle_event(self, event):
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