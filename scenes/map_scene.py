import pygame

import settings
from i18n import t
from scenes.scene import Scene


class MapScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.room = None

    def enter(self, prev_scene=None):
        self.room = None
        self._speak_room()

    def _speak_room(self):
        room_pos = self.game.world_map.player_room
        room = self.game.world_map.rooms.get(room_pos)
        if room:
            if room.state != "locked":
                text = f"{t(room.name)}. {t(room.narrative)}"
            else:
                text = t("unknown")
            self.game.tts.speak(text, lang=settings.LANGUAGE)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_UP:
            if self.game.world_map.navigate("up"):
                self.game.sfx.play("menu_select")
                self._speak_room()
        elif event.key == pygame.K_DOWN:
            if self.game.world_map.navigate("down"):
                self.game.sfx.play("menu_select")
                self._speak_room()
        elif event.key == pygame.K_LEFT:
            if self.game.world_map.navigate("left"):
                self.game.sfx.play("menu_select")
                self._speak_room()
        elif event.key == pygame.K_RIGHT:
            if self.game.world_map.navigate("right"):
                self.game.sfx.play("menu_select")
                self._speak_room()
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
