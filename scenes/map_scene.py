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

    def _enter_selected_room(self):
        room = self.game.world_map.select_room()
        if not room:
            return
        self.room = room
        self.game.scene_manager.switch("gameplay")
        self.game.sfx.play("menu_confirm")

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            room = self.game.world_map.get_room_at_pos(event.pos)
            if room and self.game.world_map.set_player_room((room.col, room.row)):
                if room.state in ("available", "completed"):
                    self._enter_selected_room()
                else:
                    self.game.sfx.play("menu_select")
            return

        if event.type != pygame.KEYDOWN:
            return

        mods = pygame.key.get_mods()
        if (mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_ALT):
            self.game.player.toggle_skin()
            skin_name = self.game.player.skin_names[self.game.player.skin_index]
            # Use self.avatar_x/y from world_map for floating text position
            self.game.floating_text.add_info(
                self.game.world_map.avatar_x, 
                self.game.world_map.avatar_y - 40,
                t("class_label", name=skin_name), 
                settings.CYAN
            )
            self.game.sfx.play("menu_select")
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
            self._enter_selected_room()
        elif event.key == pygame.K_ESCAPE:
            self.game.sfx.play("menu_select")
            self.game.scene_manager.switch("menu")

    def update(self, dt):
        self.game.world_map.update(dt, self.game.player)
        self.game.floating_text.update(dt)

    def draw(self, screen):
        self.game.world_map.draw(screen, self.game.player)
        self.game.floating_text.draw(screen)
