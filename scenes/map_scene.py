import pygame
import math

import settings
from i18n import t
from player import Player
from scenes.scene import Scene
from utils import draw_text


class MapScene(Scene):
    # How often (seconds) to re-broadcast our position even if we haven't moved.
    _BROADCAST_INTERVAL = 0.12

    def __init__(self, game):
        super().__init__(game)
        self.room = None

        # Multiplayer: a lightweight Player instance to mirror the remote avatar
        self._remote_player = None
        self._remote_avatar_x = 0.0
        self._remote_avatar_y = 0.0
        self._remote_room = settings.MAP_START_ROOM

        # Voting: both players must stand on the same room to enter it
        self._remote_voted_room = None   # room the remote player has voted/confirmed
        self._local_voted_room = None    # room we have voted for
        self._vote_status = ""           # message shown in UI

        self._broadcast_timer = 0.0

    def enter(self, prev_scene=None):
        self.room = None
        self._local_voted_room = None
        self._remote_voted_room = None
        self._vote_status = ""
        self._broadcast_timer = 0.0
        self._speak_room()

        if self.game.mp_is_multiplayer:
            self._remote_player = Player()
            self._remote_player.current_anim = "idle"
            start_room = self.game.world_map.rooms.get(settings.MAP_START_ROOM)
            if start_room:
                self._remote_avatar_x = float(start_room.rect.centerx + 18)
                self._remote_avatar_y = float(start_room.rect.top + 20)
            self._remote_room = settings.MAP_START_ROOM
        else:
            self._remote_player = None

    # ------------------------------------------------------------------ helpers

    def _speak_room(self):
        room_pos = self.game.world_map.player_room
        room = self.game.world_map.rooms.get(room_pos)
        if room:
            text = f"{t(room.name)}. {t(room.narrative)}" if room.state != "locked" else t("unknown")
            self.game.tts.speak(text, lang=settings.LANGUAGE)

    def _net_send(self, msg):
        """Send a message to the other player via host-broadcast or client-send."""
        if self.game.mp_host:
            self.game.mp_host.broadcast(msg)
        elif self.game.mp_client:
            self.game.mp_client.send(msg)

    def _broadcast_position(self):
        col, row = self.game.world_map.player_room
        self._net_send({"type": "map_position", "room": [col, row]})

    def _broadcast_vote(self, room_pos):
        """Tell the other player we want to enter room_pos."""
        self._net_send({"type": "map_vote", "room": list(room_pos)})

    def _poll_network(self):
        msgs = []
        if self.game.mp_host:
            msgs = self.game.mp_host.poll()
        elif self.game.mp_client:
            msgs = self.game.mp_client.poll()

        for msg in msgs:
            mtype = msg.get("type")

            if mtype == "map_position":
                pos = msg.get("room")
                if pos and len(pos) == 2:
                    self._remote_room = tuple(pos)

            elif mtype == "map_vote":
                pos = msg.get("room")
                if pos and len(pos) == 2:
                    self._remote_voted_room = tuple(pos)
                    self._check_votes()

            elif mtype == "map_vote_cancel":
                self._remote_voted_room = None
                self._vote_status = ""

    def _check_votes(self):
        """If both players voted for the same room, enter it."""
        if self._local_voted_room and self._remote_voted_room:
            if self._local_voted_room == self._remote_voted_room:
                room = self.game.world_map.rooms.get(self._local_voted_room)
                if room and room.state in ("available", "completed"):
                    self.room = room
                    self.game.sfx.play("menu_confirm")
                    self.game.scene_manager.switch("gameplay")

    # ------------------------------------------------------------------ events

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            room = self.game.world_map.get_room_at_pos(event.pos)
            if room and self.game.world_map.set_player_room((room.col, room.row)):
                self._broadcast_position()
                if room.state in ("available", "completed"):
                    self._cast_vote((room.col, room.row))
                else:
                    self.game.sfx.play("menu_select")
            return

        if event.type != pygame.KEYDOWN:
            return

        mods = pygame.key.get_mods()
        if (mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_ALT):
            self.game.player.toggle_skin()
            skin_name = self.game.player.skin_names[self.game.player.skin_index]
            self.game.floating_text.add_info(
                self.game.world_map.avatar_x,
                self.game.world_map.avatar_y - 40,
                t("class_label", name=skin_name),
                settings.CYAN
            )
            self.game.sfx.play("menu_select")
            return

        moved = False
        if event.key == pygame.K_UP:
            moved = self.game.world_map.navigate("up")
        elif event.key == pygame.K_DOWN:
            moved = self.game.world_map.navigate("down")
        elif event.key == pygame.K_LEFT:
            moved = self.game.world_map.navigate("left")
        elif event.key == pygame.K_RIGHT:
            moved = self.game.world_map.navigate("right")

        if moved:
            self.game.sfx.play("menu_select")
            self._speak_room()
            self._broadcast_position()
            # Cancel any pending vote when we move away
            if self._local_voted_room and self._local_voted_room != self.game.world_map.player_room:
                self._local_voted_room = None
                self._vote_status = ""
                self._net_send({"type": "map_vote_cancel"})

        elif event.key == pygame.K_RETURN:
            room_pos = self.game.world_map.player_room
            room = self.game.world_map.rooms.get(room_pos)
            if room and room.state in ("available", "completed"):
                self._cast_vote(room_pos)

        elif event.key == pygame.K_ESCAPE:
            self.game.sfx.play("menu_select")
            self.game.scene_manager.switch("menu")

    def _cast_vote(self, room_pos):
        """Cast (or toggle off) our vote for room_pos."""
        if not self.game.mp_is_multiplayer:
            # Single player — enter directly
            room = self.game.world_map.rooms.get(room_pos)
            if room:
                self.room = room
                self.game.sfx.play("menu_confirm")
                self.game.scene_manager.switch("gameplay")
            return

        if self._local_voted_room == room_pos:
            # Toggle off
            self._local_voted_room = None
            self._vote_status = ""
            self._net_send({"type": "map_vote_cancel"})
        else:
            self._local_voted_room = room_pos
            self._broadcast_vote(room_pos)
            self._update_vote_status()
            self._check_votes()

    def _update_vote_status(self):
        local_pos = self._local_voted_room
        remote_pos = self._remote_voted_room
        wmap = self.game.world_map

        if local_pos and remote_pos:
            if local_pos == remote_pos:
                self._vote_status = ""   # about to switch — no need to show
            else:
                r = wmap.rooms.get(remote_pos)
                rname = t(r.name) if r else str(remote_pos)
                self._vote_status = t("mp_vote_mismatch", room=rname)
        elif local_pos:
            r = wmap.rooms.get(remote_pos) if remote_pos else None
            self._vote_status = t("mp_waiting_partner")
        else:
            self._vote_status = ""

    # ------------------------------------------------------------------ update

    def update(self, dt):
        self.game.world_map.update(dt, self.game.player)
        self.game.floating_text.update(dt)

        if not self.game.mp_is_multiplayer:
            return

        # Heartbeat: re-broadcast position periodically so the remote never freezes
        self._broadcast_timer -= dt
        if self._broadcast_timer <= 0:
            self._broadcast_timer = self._BROADCAST_INTERVAL
            self._broadcast_position()

        self._poll_network()
        self._update_vote_status()

        # Smoothly move the remote avatar toward the target room
        remote_room = self.game.world_map.rooms.get(self._remote_room)
        if remote_room and self._remote_player:
            target_x = float(remote_room.rect.centerx + 18)
            target_y = float(remote_room.rect.top + 20)
            dx = target_x - self._remote_avatar_x
            dy = target_y - self._remote_avatar_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 2:
                speed = 300
                step = speed * dt
                if dist < step:
                    self._remote_avatar_x = target_x
                    self._remote_avatar_y = target_y
                    self._remote_player.current_anim = "idle"
                else:
                    self._remote_avatar_x += (dx / dist) * step
                    self._remote_avatar_y += (dy / dist) * step
                    self._remote_player.current_anim = "walk"
                    if abs(dx) > 1:
                        self._remote_player.dir_x = 1 if dx > 0 else -1
            else:
                self._remote_avatar_x = target_x
                self._remote_avatar_y = target_y
                self._remote_player.current_anim = "idle"
            self._remote_player.update_animation(dt)

    # ------------------------------------------------------------------ draw

    def _build_mp_info(self):
        if not self.game.mp_is_multiplayer or self._remote_player is None:
            return None

        is_host = self.game.mp_host is not None
        wmap = self.game.world_map

        # Highlight voted rooms
        local_pos = self._local_voted_room
        remote_pos = self._remote_voted_room
        votes_match = local_pos and remote_pos and local_pos == remote_pos

        local_color = settings.GOLD if is_host else settings.CYAN
        remote_color = settings.CYAN if is_host else settings.GOLD
        if votes_match:
            local_color = settings.GREEN
            remote_color = settings.GREEN

        local_label = "HOST ✓" if (is_host and local_pos) else ("HOST" if is_host else ("P2 ✓" if local_pos else "P2"))
        remote_label = "P2 ✓" if (not is_host and remote_pos) else ("P2" if not is_host else ("HOST ✓" if remote_pos else "HOST"))

        return [
            {
                "x": wmap.avatar_x,
                "y": wmap.avatar_y,
                "label": local_label,
                "color": local_color,
                "player": None,  # already drawn by world_map.draw()
            },
            {
                "x": self._remote_avatar_x,
                "y": self._remote_avatar_y,
                "label": remote_label,
                "color": remote_color,
                "player": self._remote_player,
            },
        ]

    def _draw_vote_ui(self, screen):
        """Draw vote status bar at the bottom of the map."""
        if not self.game.mp_is_multiplayer:
            return

        wmap = self.game.world_map
        local_pos = self._local_voted_room
        remote_pos = self._remote_voted_room
        votes_match = local_pos and remote_pos and local_pos == remote_pos

        bar_y = settings.WINDOW_HEIGHT - 48
        cx = settings.WINDOW_WIDTH // 2

        if votes_match:
            msg = t("mp_vote_entering")
            color = settings.GREEN
        elif local_pos and not remote_pos:
            r = wmap.rooms.get(local_pos)
            rname = t(r.name) if r else ""
            msg = t("mp_waiting_partner")
            color = settings.YELLOW
        elif local_pos and remote_pos and local_pos != remote_pos:
            r = wmap.rooms.get(remote_pos)
            rname = t(r.name) if r else str(remote_pos)
            msg = t("mp_vote_mismatch", room=rname)
            color = settings.ORANGE
        else:
            msg = t("mp_vote_hint")
            color = settings.GRAY

        # Semi-transparent background bar
        bar_surf = pygame.Surface((settings.WINDOW_WIDTH, 28), pygame.SRCALPHA)
        bar_surf.fill((0, 0, 0, 130))
        screen.blit(bar_surf, (0, bar_y - 4))
        draw_text(screen, msg, (cx, bar_y + 8), color, 16)

    def draw(self, screen):
        mp_info = self._build_mp_info()
        self.game.world_map.draw(screen, self.game.player, mp_info=mp_info)
        self._draw_vote_ui(screen)
        self.game.floating_text.draw(screen)
