import pygame

from scenes.scene import Scene


class MapScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.room = None

    def enter(self, prev_scene=None):
        self.room = None

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_UP:
            self.game.world_map.navigate("up")
            self.game.sfx.play("menu_select")
        elif event.key == pygame.K_DOWN:
            self.game.world_map.navigate("down")
            self.game.sfx.play("menu_select")
        elif event.key == pygame.K_LEFT:
            self.game.world_map.navigate("left")
            self.game.sfx.play("menu_select")
        elif event.key == pygame.K_RIGHT:
            self.game.world_map.navigate("right")
            self.game.sfx.play("menu_select")
        elif event.key == pygame.K_RETURN:
            room = self.game.world_map.select_room()
            if room:
                if room.type == "victory":
                    self.game.scene_manager.switch("victory")
                else:
                    self.room = room
                    self.game.scene_manager.switch("gameplay")
                self.game.sfx.play("menu_confirm")
        elif event.key == pygame.K_ESCAPE:
            self.game.sfx.play("menu_select")
            self.game.scene_manager.switch("menu")

    def update(self, dt):
        self.game.world_map.update(dt)

    def draw(self, screen):
        self.game.world_map.draw(screen)
