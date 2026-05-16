import pygame

import settings
from scene import Scene


class MenuScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.menu_items = [("START GAME", ""), ("HOW TO PLAY", ""), ("QUIT", "")]
        self.selected = 0
        self.showing_how_to_play = False

    def enter(self, prev_scene=None):
        self.selected = 0
        self.showing_how_to_play = False

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
        elif event.key == pygame.K_DOWN:
            self.selected = (self.selected + 1) % len(self.menu_items)
            self.game.sfx.play("menu_select")
        elif event.key == pygame.K_RETURN:
            self.game.sfx.play("menu_confirm")
            if self.selected == 0:
                self.game.reset_game_state()
                self.game.scene_manager.switch("gameplay")
            elif self.selected == 1:
                self.showing_how_to_play = True
            elif self.selected == 2:
                self.game.running = False

    def update(self, dt):
        pass

    def draw(self, screen):
        if self.showing_how_to_play:
            self.game.ui.draw_how_to_play(screen)
        else:
            self.game.ui.draw_main_menu(screen, self.menu_items, self.selected)
