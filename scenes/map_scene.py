import math
import pygame

import settings
from i18n import t
from player import Player
from scenes.scene import Scene
from utils import draw_text


class MapScene(Scene):
    _BROADCAST_INTERVAL = 0.12

    def __init__(self, game):
        super().__init__(game)
        self.room = None
        self._remote_player = None
        self._remote_avatar_x = 0.0
        self._remote_avatar_y = 0.0
        self._remote_room = settings.MAP_START_ROOM
        self._remote_voted_room = None
        self._local_voted_room = None
        self._vote_status = ""
        self._broadcast_timer = 0.0
        self._dragging = False
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._drag_scroll_start_x = 0
        self._drag_scroll_start_y = 0
        self._drag_button = 0
        self._drag_moved = False
        self._hovered_room = None
        self._mouse_pos = (0, 0)

    def enter(self, prev_scene=None):
        self.room = None
        self._local_voted_room = None
        self._remote_voted_room = None
        self._vote_status = ""
        self._broadcast_timer = 0.0
        self._dragging = False
        self._drag_moved = False
        self._hovered_room = None
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

    def _speak_room(self):
        room_id = self.game.world_map.player_room
        room = self.game.world_map.rooms.get(room_id)
        if room:
            text = f"{t(room.name)}. {t(room.narrative)}" if room.state != "locked" else t("unknown")
            self.game.tts.speak(text, lang=settings.LANGUAGE)

    def _net_send(self, msg):
        if self.game.mp_host:
            self.game.mp_host.broadcast(msg)
        elif self.game.mp_client:
            self.game.mp_client.send(msg)

    def _broadcast_position(self):
        self._net_send({"type": "map_position", "room": self.game.world_map.player_room})

    def _broadcast_vote(self, room_pos):
        self._net_send({"type": "map_vote", "room": list(room_pos) if isinstance(room_pos, (list, tuple)) else room_pos})

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
                if pos:
                    self._remote_room = pos
            elif mtype == "map_vote":
                pos = msg.get("room")
                if pos:
                    self._remote_voted_room = pos
                    self._check_votes()
            elif mtype == "map_vote_cancel":
                self._remote_voted_room = None
                self._vote_status = ""
            elif mtype == "map_enter_room":
                room_data = msg.get("room")
                if room_data and len(room_data) == 2:
                    room = self.game.world_map.rooms.get((room_data[0], room_data[1]))
                    if room and self.game.scene_manager.current is self:
                        self.room = room
                        self.game.sfx.play("menu_confirm")
                        self.game.scene_manager.switch("gameplay")

    def _check_votes(self):
        if self._local_voted_room and self._remote_voted_room and self._local_voted_room == self._remote_voted_room:
            room = self.game.world_map.rooms.get(self._local_voted_room)
            if room and room.state in ("available", "completed"):
                if self.game.mp_host:
                    self._net_send({"type": "map_enter_room", "room": [room.col, room.row]})
                    self.room = room
                    self.game.sfx.play("menu_confirm")
                    self.game.scene_manager.switch("gameplay")
                elif not self.game.mp_is_multiplayer:
                    self.room = room
                    self.game.sfx.play("menu_confirm")
                    self.game.scene_manager.switch("gameplay")

    def _cast_vote(self, room_id):
        if not self.game.mp_is_multiplayer:
            room = self.game.world_map.rooms.get(room_id)
            if room:
                self.room = room
                self.game.sfx.play("menu_confirm")
                self.game.scene_manager.switch("gameplay")
            return

        if self._local_voted_room == room_id:
            self._local_voted_room = None
            self._vote_status = ""
            self._net_send({"type": "map_vote_cancel"})
        else:
            self._local_voted_room = room_id
            self._broadcast_vote(room_id)
            self._update_vote_status()
            self._check_votes()

    def _update_vote_status(self):
        local_pos = self._local_voted_room
        remote_pos = self._remote_voted_room
        wmap = self.game.world_map

        if local_pos and remote_pos:
            if local_pos == remote_pos:
                self._vote_status = ""
            else:
                room = wmap.rooms.get(remote_pos)
                room_name = t(room.name) if room else str(remote_pos)
                self._vote_status = t("mp_vote_mismatch", room=room_name)
        elif local_pos:
            self._vote_status = t("mp_waiting_partner")
        else:
            self._vote_status = ""

    def handle_event(self, event):
        wmap = self.game.world_map

        if event.type == pygame.MOUSEBUTTONDOWN:
            self._dragging = True
            self._drag_start_x = event.pos[0]
            self._drag_start_y = event.pos[1]
            self._drag_scroll_start_x = wmap.target_scroll_x
            self._drag_scroll_start_y = wmap.target_scroll_y
            self._drag_button = event.button
            self._drag_moved = False
            return

        if event.type == pygame.MOUSEBUTTONUP:
            if self._dragging and not self._drag_moved and event.button == 1:
                room = wmap.get_room_at_pos(event.pos)
                if room and wmap.set_player_room(room.id):
                    self._broadcast_position()
                    if room.state in ("available", "completed"):
                        self._cast_vote(room.id)
                    else:
                        self.game.sfx.play("menu_select")
            self._dragging = False
            self._drag_moved = False
            return

        if event.type == pygame.MOUSEMOTION:
            self._mouse_pos = event.pos
            if self._dragging:
                dx = self._drag_start_x - event.pos[0]
                dy = self._drag_start_y - event.pos[1]
                if abs(event.pos[0] - self._drag_start_x) > 5 or abs(event.pos[1] - self._drag_start_y) > 5:
                    self._drag_moved = True
                if self._drag_moved:
                    wmap.target_scroll_x = max(wmap.min_scroll_x, min(wmap.max_scroll_x, self._drag_scroll_start_x + dx))
                    wmap.target_scroll_y = max(wmap.min_scroll_y, min(wmap.max_scroll_y, self._drag_scroll_start_y + dy))
            else:
                room = wmap.get_room_at_pos(event.pos)
                self._hovered_room = room if room and room.state != "locked" else None
            return

        if event.type != pygame.KEYDOWN:
            return

        mods = pygame.key.get_mods()
        if (mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_ALT):
            self.game.player.toggle_skin()
            skin_name = self.game.player.skin_names[self.game.player.skin_index]
            self.game.floating_text.add_info(
                wmap.avatar_x, wmap.avatar_y - 40,
                t("class_label", name=skin_name), settings.CYAN)
            self.game.sfx.play("menu_select")
            return

        moved = False
        if event.key == pygame.K_UP:
            moved = wmap.navigate("up")
        elif event.key == pygame.K_DOWN:
            moved = wmap.navigate("down")
        elif event.key == pygame.K_LEFT:
            moved = wmap.navigate("left")
        elif event.key == pygame.K_RIGHT:
            moved = wmap.navigate("right")
        elif event.key == pygame.K_s:
            self.game.sfx.play("menu_select")
            self.game.scene_manager.push("shop")
            return
        elif event.key == pygame.K_u:
            self.game.sfx.play("menu_select")
            self.game.scene_manager.push("upgrades")
            return
        elif event.key == pygame.K_e:
            self.game.sfx.play("menu_select")
            self.game.scene_manager.push("equip_dock")
            return
        elif event.key == pygame.K_TAB:
            self.game.sfx.play("menu_select")
            self.game.scene_manager.push("player_panel")
            return

        if moved:
            self.game.sfx.play("menu_select")
            self._speak_room()
            self._broadcast_position()
            if self._local_voted_room and self._local_voted_room != wmap.player_room:
                self._local_voted_room = None
                self._vote_status = ""
                self._net_send({"type": "map_vote_cancel"})
        elif event.key == pygame.K_RETURN:
            room_id = wmap.player_room
            room = wmap.rooms.get(room_id)
            if room and room.state in ("available", "completed"):
                self._cast_vote(room_id)
        elif event.key == pygame.K_ESCAPE:
            self.game.sfx.play("menu_select")
            self.game.scene_manager.switch("menu")

    def update(self, dt):
        self.game.world_map.update(dt, self.game.player)
        self.game.floating_text.update(dt)

        if not self.game.mp_is_multiplayer:
            return

        self._broadcast_timer -= dt
        if self._broadcast_timer <= 0:
            self._broadcast_timer = self._BROADCAST_INTERVAL
            self._broadcast_position()

        self._poll_network()
        self._update_vote_status()

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
            self._remote_player.update_animation(dt, None)

    def _build_mp_info(self):
        if not self.game.mp_is_multiplayer or self._remote_player is None:
            return None

        is_host = self.game.mp_host is not None
        wmap = self.game.world_map
        local_pos = self._local_voted_room
        remote_pos = self._remote_voted_room
        votes_match = local_pos and remote_pos and local_pos == remote_pos

        local_color = settings.GOLD if is_host else settings.CYAN
        remote_color = settings.CYAN if is_host else settings.GOLD
        if votes_match:
            local_color = settings.GREEN
            remote_color = settings.GREEN

        local_label = "HOST" if is_host else "P2"
        remote_label = "P2" if is_host else "HOST"

        return [
            {"x": wmap.avatar_x, "y": wmap.avatar_y, "label": local_label, "color": local_color, "player": None},
            {"x": self._remote_avatar_x, "y": self._remote_avatar_y, "label": remote_label, "color": remote_color, "player": self._remote_player},
        ]

    def _draw_vote_ui(self, screen):
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
            msg = t("mp_waiting_partner")
            color = settings.YELLOW
        elif local_pos and remote_pos and local_pos != remote_pos:
            room = wmap.rooms.get(remote_pos)
            room_name = t(room.name) if room else str(remote_pos)
            msg = t("mp_vote_mismatch", room=room_name)
            color = settings.ORANGE
        else:
            msg = t("mp_vote_hint")
            color = settings.GRAY

        bar_surf = pygame.Surface((settings.WINDOW_WIDTH, 28), pygame.SRCALPHA)
        bar_surf.fill((0, 0, 0, 130))
        screen.blit(bar_surf, (0, bar_y - 4))
        draw_text(screen, msg, (cx, bar_y + 8), color, 16)

    def _draw_hover_popup(self, screen):
        room = self._hovered_room
        if room is None or room.state == "locked":
            return

        mx, my = self._mouse_pos
        popup_w = 220
        popup_h = 90
        popup_x = mx + 15
        popup_y = my - 10

        if popup_x + popup_w > settings.WINDOW_WIDTH:
            popup_x = mx - popup_w - 15
        if popup_y + popup_h > settings.WINDOW_HEIGHT:
            popup_y = settings.WINDOW_HEIGHT - popup_h - 5
        if popup_y < 5:
            popup_y = 5

        bg = pygame.Surface((popup_w, popup_h), pygame.SRCALPHA)
        bg.fill((15, 15, 30, 220))
        screen.blit(bg, (popup_x, popup_y))
        pygame.draw.rect(screen, settings.LIGHT_GRAY, (popup_x, popup_y, popup_w, popup_h), 1, border_radius=4)

        font = pygame.font.Font(None, 18)
        title_font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 15)

        type_labels = {"hub": "Hub", "normal": "Room", "challenge": "Challenge",
                       "side": "Side Quest", "boss": "Boss", "victory": "Victory"}
        type_label = type_labels.get(room.type, "Room")
        type_color = settings.GRAY
        if room.type == "side":
            type_color = settings.GOLD
        elif room.type == "challenge":
            type_color = settings.ORANGE
        elif room.type == "boss":
            type_color = settings.RED

        title = title_font.render(t(room.name), True, settings.WHITE)
        screen.blit(title, (popup_x + 10, popup_y + 8))

        type_text = small_font.render(type_label, True, type_color)
        screen.blit(type_text, (popup_x + 10, popup_y + 30))

        diff_names = {1: "Easy", 2: "Medium", 3: "Hard", 4: "Extreme"}
        diff_colors = {1: settings.CYAN, 2: settings.ORANGE, 3: settings.RED, 4: settings.PURPLE}
        diff_name = diff_names.get(room.difficulty, "???")
        diff_color = diff_colors.get(room.difficulty, settings.GRAY)

        cx_stars = popup_x + popup_w - 40
        cy_stars = popup_y + 40
        star_size = 5
        spacing = 12
        total_sw = room.difficulty * spacing
        sx_start = cx_stars - total_sw // 2 + spacing // 2
        for i in range(room.difficulty):
            x = int(sx_start + i * spacing)
            y = int(cy_stars)
            points = []
            for angle_idx in range(10):
                angle = math.radians(angle_idx * 36 - 90)
                r = star_size if angle_idx % 2 == 0 else star_size * 0.4
                points.append((x + r * math.cos(angle), y + r * math.sin(angle)))
            if len(points) >= 3:
                pygame.draw.polygon(screen, diff_color, points)

        diff_text = font.render(diff_name, True, diff_color)
        screen.blit(diff_text, (popup_x + 10, popup_y + 48))

        gold_text = font.render(f"+{room.gold_reward} gold", True, settings.GOLD)
        screen.blit(gold_text, (popup_x + 10, popup_y + 68))

    def draw(self, screen):
        mp_info = self._build_mp_info()
        self.game.world_map.hovered_room = self._hovered_room
        self.game.world_map.draw(screen, self.game.player, mp_info=mp_info)
        self._draw_hover_popup(screen)
        self._draw_vote_ui(screen)
        self.game.floating_text.draw(screen)