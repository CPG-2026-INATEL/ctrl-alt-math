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
        self._detail_panel_room = None
        self._detail_panel_alpha = 0.0

    def enter(self, prev_scene=None):
        self.room = None
        self._local_voted_room = None
        self._remote_voted_room = None
        self._vote_status = ""
        self._broadcast_timer = 0.0
        self._dragging = False
        self._drag_moved = False
        self._hovered_room = None
        self._detail_panel_room = None
        self._detail_panel_alpha = 0.0
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

        if self._hovered_room and self._hovered_room.state != "locked":
            self._detail_panel_room = self._hovered_room
            self._detail_panel_alpha = min(1.0, self._detail_panel_alpha + dt * 6)
        else:
            self._detail_panel_alpha = max(0.0, self._detail_panel_alpha - dt * 6)
            if self._detail_panel_alpha <= 0:
                self._detail_panel_room = None

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

        dot_x = cx - 60
        dot_y = bar_y + 8
        dot_color = color
        pulse = int(150 + 105 * math.sin(self.game.world_map.anim_timer * 4))
        pygame.draw.circle(screen, (*dot_color, pulse), (dot_x, dot_y), 5)
        pygame.draw.circle(screen, dot_color, (dot_x, dot_y), 3)

        draw_text(screen, msg, (cx + 10, bar_y + 8), color, 16)

    def _draw_hover_popup(self, screen):
        room = self._hovered_room
        if room is None or room.state == "locked":
            return

        mx, my = self._mouse_pos
        popup_w = 220
        popup_h = 100
        popup_x = mx + 18
        popup_y = my - 15

        if popup_x + popup_w > settings.WINDOW_WIDTH - 200:
            popup_x = mx - popup_w - 18
        if popup_y + popup_h > settings.WINDOW_HEIGHT:
            popup_y = settings.WINDOW_HEIGHT - popup_h - 5
        if popup_y < settings.MAP_HEADER_H + 5:
            popup_y = settings.MAP_HEADER_H + 5

        bg = pygame.Surface((popup_w, popup_h), pygame.SRCALPHA)
        bg.fill((10, 12, 28, 220))
        screen.blit(bg, (popup_x, popup_y))

        type_labels = {"hub": "HUB", "normal": "ROOM", "challenge": "CHALLENGE",
                       "side": "SIDE QUEST", "boss": "BOSS", "victory": "VICTORY"}
        type_label = type_labels.get(room.type, "ROOM")
        type_color = settings.GRAY
        if room.type == "hub":
            type_color = settings.CYAN
        elif room.type == "side":
            type_color = settings.GOLD
        elif room.type == "challenge":
            type_color = settings.ORANGE
        elif room.type == "boss":
            type_color = settings.RED
        elif room.type == "victory":
            type_color = settings.PURPLE

        pygame.draw.rect(screen, type_color, (popup_x, popup_y, popup_w, popup_h), 2, border_radius=6)
        pygame.draw.rect(screen, type_color, (popup_x, popup_y, popup_w, 3), border_radius=6)

        title_font = pygame.font.Font(None, 20)
        title = title_font.render(t(room.name), True, settings.WHITE)
        screen.blit(title, (popup_x + 10, popup_y + 8))

        badge_font = pygame.font.Font(None, 13)
        badge_txt = badge_font.render(type_label, True, type_color)
        screen.blit(badge_txt, (popup_x + 10, popup_y + 28))

        pygame.draw.line(screen, (40, 40, 60),
                         (popup_x + 8, popup_y + 42),
                         (popup_x + popup_w - 8, popup_y + 42), 1)

        diff_colors = {1: settings.CYAN, 2: settings.GOLD, 3: settings.ORANGE, 4: settings.RED}
        diff_color = diff_colors.get(room.difficulty, settings.GRAY)
        diff_names = {1: "Easy", 2: "Medium", 3: "Hard", 4: "Extreme"}
        diff_name = diff_names.get(room.difficulty, "???")

        diff_font = pygame.font.Font(None, 14)
        diff_txt = diff_font.render(f"Difficulty: {diff_name}", True, diff_color)
        screen.blit(diff_txt, (popup_x + 10, popup_y + 48))

        star_y = popup_y + 48
        star_x = popup_x + popup_w - 15 - room.difficulty * 13
        for i in range(room.difficulty):
            pts = []
            for ai in range(10):
                ang = math.radians(ai * 36 - 90)
                r = 4 if ai % 2 == 0 else 2
                pts.append((star_x + i * 13 + r * math.cos(ang),
                             star_y + r * math.sin(ang)))
            pygame.draw.polygon(screen, diff_color, pts)

        gold_font = pygame.font.Font(None, 14)
        gold_txt = gold_font.render(f"+{room.gold_reward} gold", True, settings.GOLD)
        screen.blit(gold_txt, (popup_x + 10, popup_y + 66))

        state_labels = {"available": "ENTER →", "completed": "REVISIT", "locked": "LOCKED"}
        state_colors = {"available": settings.GREEN, "completed": settings.CYAN, "locked": settings.GRAY}
        state_lbl = state_labels.get(room.state, room.state)
        state_col = state_colors.get(room.state, settings.GRAY)
        state_txt = gold_font.render(state_lbl, True, state_col)
        screen.blit(state_txt, (popup_x + popup_w - state_txt.get_width() - 10, popup_y + 66))

        narr_font = pygame.font.Font(None, 12)
        narr_text = t(room.narrative)[:40] + "…" if len(t(room.narrative)) > 40 else t(room.narrative)
        narr_surf = narr_font.render(narr_text, True, (130, 130, 150))
        screen.blit(narr_surf, (popup_x + 10, popup_y + 84))

    def _draw_detail_panel(self, screen):
        room = self._detail_panel_room
        if room is None or self._detail_panel_alpha <= 0:
            return

        panel_w = 190
        panel_h = 260
        panel_x = settings.WINDOW_WIDTH - panel_w - 8
        panel_y = settings.MAP_HEADER_H + 8

        alpha = int(self._detail_panel_alpha * 230)

        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((8, 10, 28, alpha))
        screen.blit(panel_surf, (panel_x, panel_y))

        type_labels = {"hub": "HUB", "normal": "NORMAL", "challenge": "CHALLENGE",
                       "side": "SIDE QUEST", "boss": "BOSS", "victory": "VICTORY"}
        type_label = type_labels.get(room.type, "NORMAL")
        type_color = settings.GRAY
        if room.type == "hub":
            type_color = settings.CYAN
        elif room.type == "side":
            type_color = settings.GOLD
        elif room.type == "challenge":
            type_color = settings.ORANGE
        elif room.type == "boss":
            type_color = settings.RED
        elif room.type == "victory":
            type_color = settings.PURPLE

        pygame.draw.rect(screen, (*type_color, alpha), (panel_x, panel_y, panel_w, panel_h), 2, border_radius=8)
        pygame.draw.rect(screen, (*type_color, alpha), (panel_x, panel_y, panel_w, 3), border_radius=8)

        y = panel_y + 10

        title_font = pygame.font.Font(None, 18)
        title = title_font.render(t(room.name), True, settings.WHITE)
        title.set_alpha(alpha)
        screen.blit(title, (panel_x + 10, y))
        y += 22

        badge_font = pygame.font.Font(None, 13)
        type_badge = badge_font.render(type_label, True, type_color)
        type_badge.set_alpha(alpha)
        screen.blit(type_badge, (panel_x + 10, y))
        y += 20

        pygame.draw.line(screen, (40, 40, 60, alpha // 2),
                         (panel_x + 8, y), (panel_x + panel_w - 8, y), 1)
        y += 10

        diff_colors = {1: settings.CYAN, 2: settings.GOLD, 3: settings.ORANGE, 4: settings.RED}
        diff_color = diff_colors.get(room.difficulty, settings.GRAY)
        diff_names = {1: "Easy", 2: "Medium", 3: "Hard", 4: "Extreme"}
        diff_name = diff_names.get(room.difficulty, "???")

        diff_font = pygame.font.Font(None, 14)
        diff_txt = diff_font.render(f"Difficulty: {diff_name}", True, diff_color)
        diff_txt.set_alpha(alpha)
        screen.blit(diff_txt, (panel_x + 10, y))
        y += 18

        star_cx = panel_x + panel_w // 2
        star_spacing = 14
        star_start = star_cx - room.difficulty * star_spacing // 2
        for i in range(room.difficulty):
            pts = []
            for ai in range(10):
                ang = math.radians(ai * 36 - 90)
                r = 5 if ai % 2 == 0 else 2
                pts.append((star_start + i * star_spacing + r * math.cos(ang),
                             y + r * math.sin(ang)))
            pygame.draw.polygon(screen, diff_color, pts)
        y += 16

        gold_font = pygame.font.Font(None, 14)
        gold_txt = gold_font.render(f"+{room.gold_reward} gold", True, settings.GOLD)
        gold_txt.set_alpha(alpha)
        screen.blit(gold_txt, (panel_x + 10, y))
        y += 20

        if room.enemies:
            enemy_font = pygame.font.Font(None, 13)
            enemy_label = enemy_font.render("Enemies:", True, settings.LIGHT_GRAY)
            enemy_label.set_alpha(alpha)
            screen.blit(enemy_label, (panel_x + 10, y))
            y += 16

            enemy_type_names = {
                "censor": "Censor",
                "strawman": "Strawman",
                "bayesian": "Bayesian",
                "ortogonal": "Ortogonal",
                "atirador": "Atirador",
                "granadeiro": "Granadeiro",
                "boss": "BOSS",
            }
            enemy_colors_map = {
                "censor": settings.RED,
                "strawman": settings.ORANGE,
                "bayesian": settings.PURPLE,
                "ortogonal": settings.CYAN,
                "atirador": settings.YELLOW,
                "granadeiro": settings.ORANGE,
                "boss": settings.RED,
            }
            for e_type, count in room.enemies:
                e_name = enemy_type_names.get(e_type, e_type)
                e_color = enemy_colors_map.get(e_type, settings.GRAY)
                if e_type == "boss":
                    e_text = f"  {e_name} x{count}"
                else:
                    e_text = f"  {e_name} x{count}"
                e_surf = enemy_font.render(e_text, True, e_color)
                e_surf.set_alpha(alpha)
                screen.blit(e_surf, (panel_x + 10, y))
                y += 15

        y = panel_y + panel_h - 35

        state_labels = {"available": "ENTER →", "completed": "REVISIT", "locked": "LOCKED"}
        state_colors = {"available": settings.GREEN, "completed": settings.CYAN, "locked": settings.GRAY}
        state_lbl = state_labels.get(room.state, room.state)
        state_col = state_colors.get(room.state, settings.GRAY)

        state_font = pygame.font.Font(None, 16)
        state_surf = state_font.render(state_lbl, True, state_col)
        state_surf.set_alpha(alpha)
        state_x = panel_x + (panel_w - state_surf.get_width()) // 2
        screen.blit(state_surf, (state_x, y))

    def draw(self, screen):
        mp_info = self._build_mp_info()
        self.game.world_map.hovered_room = self._hovered_room
        self.game.world_map.draw(screen, self.game.player, mp_info=mp_info)
        self._draw_hover_popup(screen)
        self._draw_detail_panel(screen)
        self._draw_vote_ui(screen)
        self.game.floating_text.draw(screen)
