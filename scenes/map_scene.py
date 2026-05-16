import pygame

import settings
from i18n import t
from scenes.scene import Scene


class MapScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.room = None

    def _serialize_map_state(self):
        return {
            "type": "map_state",
            "player_room": list(self.game.world_map.player_room),
            "room_states": {
                f"{room.col},{room.row}": room.state
                for room in self.game.world_map.rooms.values()
            },
        }

    def _apply_map_state(self, msg):
        player_room = tuple(msg.get("player_room", self.game.world_map.player_room))
        self.game.world_map.player_room = player_room
        room_states = msg.get("room_states", {})
        for key, state in room_states.items():
            col, row = [int(v) for v in key.split(",")]
            room = self.game.world_map.rooms.get((col, row))
            if room:
                room.state = state

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
        if self.game.mp_is_multiplayer and self.game.mp_host:
            self.game.mp_host.broadcast({
                "type": "enter_room",
                "room": [room.col, room.row],
            })
        self.room = room
        self.game.scene_manager.switch("gameplay")
        self.game.sfx.play("menu_confirm")

    def handle_event(self, event):
        if self.game.mp_is_multiplayer and self.game.mp_client:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                room = self.game.world_map.get_room_at_pos(event.pos)
                if room:
                    self.game.mp_client.send({"type": "map_click", "room": [room.col, room.row]})
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.game.mp_client.send({"type": "map_nav", "direction": "up"})
                elif event.key == pygame.K_DOWN:
                    self.game.mp_client.send({"type": "map_nav", "direction": "down"})
                elif event.key == pygame.K_LEFT:
                    self.game.mp_client.send({"type": "map_nav", "direction": "left"})
                elif event.key == pygame.K_RIGHT:
                    self.game.mp_client.send({"type": "map_nav", "direction": "right"})
                elif event.key == pygame.K_RETURN:
                    self.game.mp_client.send({"type": "map_enter"})
                elif event.key == pygame.K_ESCAPE:
                    self.game.scene_manager.switch("menu")
                return

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
        if self.game.mp_is_multiplayer and self.game.mp_host:
            for msg in self.game.mp_host.poll():
                mtype = msg.get("type")
                if mtype == "map_nav":
                    if self.game.world_map.navigate(msg.get("direction", "")):
                        self._speak_room()
                elif mtype == "map_click":
                    room_data = msg.get("room")
                    if room_data:
                        room_pos = (room_data[0], room_data[1])
                        room = self.game.world_map.rooms.get(room_pos)
                        if room and self.game.world_map.set_player_room(room_pos):
                            if room.state in ("available", "completed"):
                                self._enter_selected_room()
                                return
                elif mtype == "map_enter":
                    self._enter_selected_room()
                    return

            self.game.mp_host.broadcast(self._serialize_map_state())

        elif self.game.mp_is_multiplayer and self.game.mp_client:
            for msg in self.game.mp_client.poll():
                mtype = msg.get("type")
                if mtype == "map_state":
                    self._apply_map_state(msg)
                elif mtype == "enter_room":
                    room_data = msg.get("room")
                    if room_data:
                        room = self.game.world_map.rooms.get((room_data[0], room_data[1]))
                        if room:
                            self.room = room
                            self.game.scene_manager.switch("gameplay")
                            return

        self.game.world_map.update(dt, self.game.player)
        self.game.floating_text.update(dt)

    def draw(self, screen):
        self.game.world_map.draw(screen, self.game.player)
        self.game.floating_text.draw(screen)
