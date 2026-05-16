import pygame
import math
import settings
from utils import draw_text
from i18n import t
from map_generator import MapGenerator


class Room:
    def __init__(self, room_id, data):
        self.id = room_id
        self.col = data.get("layer", 0)
        self.row = data.get("row", 0)
        self.type = data.get("type", "normal")
        self.name = data.get("name", "room_archive_name")
        self.narrative = data.get("narrative", "room_archive_narr")
        self.enemies = data.get("enemies", [])
        self.obstacles = data.get("obstacles", [])
        self.boss_hp = data.get("boss_hp", settings.BOSS_HP)
        self.difficulty = data.get("difficulty", 1)
        self.gold_reward = data.get("gold_reward", 20)
        self.is_start = data.get("is_start", False)
        self.is_final = data.get("is_final", False)
        self.arena_cols = data.get("arena_cols", settings.GRID_COLS)
        self.arena_rows = data.get("arena_rows", settings.GRID_ROWS)

        scale = settings.DIFFICULTY_SCALING[settings.DIFFICULTY]["enemy_amount"]
        scaled_enemies = []
        for e_type, count in self.enemies:
            new_count = max(1, int(count * scale)) if count > 0 else 0
            if e_type == "boss":
                new_count = count
            scaled_enemies.append((e_type, new_count))
        self.enemies = scaled_enemies

        self.connections_out = data.get("connections_out", [])
        self.connections_in = data.get("connections_in", [])
        self.connections = data.get("connections", data.get("all_connections", []))
        if not self.connections:
            self.connections = list(set(self.connections_out + self.connections_in))

        self.state = "locked"
        self.bob_phase = 0

    @property
    def screen_x(self):
        return settings.MAP_OFFSET_X + self.col * (settings.MAP_ROOM_WIDTH + settings.MAP_ROOM_GAP)

    @property
    def screen_y(self):
        return settings.MAP_OFFSET_Y + self.row * (settings.MAP_ROOM_HEIGHT + settings.MAP_ROOM_GAP)

    @property
    def rect(self):
        return pygame.Rect(self.screen_x, self.screen_y,
                          settings.MAP_ROOM_WIDTH, settings.MAP_ROOM_HEIGHT)


class WorldMap:
    def __init__(self, seed=None):
        self.rooms = {}
        self.connections_map = {}
        self.layers = []
        self.player_room = settings.MAP_START_ROOM
        self.anim_timer = 0
        self.scroll_x = 0
        self.target_scroll_x = 0
        self.max_scroll_x = 0
        self.hovered_room = None

        self.avatar_x = 0
        self.avatar_y = 0
        self.mp_avatars = []

        self._generate_map(seed)

    def _generate_map(self, seed=None):
        gen = MapGenerator(seed)
        rooms, connections, layers = gen.generate(settings.DIFFICULTY)

        for room_id, room_data in rooms.items():
            self.rooms[room_id] = Room(room_id, room_data)

        self.connections_map = connections
        self.layers = layers

        self.max_scroll_x = max(
            (r.screen_x + settings.MAP_ROOM_WIDTH + settings.MAP_ROOM_GAP)
            for r in self.rooms.values()
        ) - settings.WINDOW_WIDTH + 100
        if self.max_scroll_x < 0:
            self.max_scroll_x = 0

        start_id = None
        for room_id, room in self.rooms.items():
            if room.is_start or room.type == "hub":
                start_id = room_id
                break
        if start_id is None:
            start_id = list(self.rooms.keys())[0]

        self.player_room = start_id
        start_room = self.rooms[start_id]
        start_room.state = "available"

        for conn_id in start_room.connections_out:
            if conn_id in self.rooms:
                self.rooms[conn_id].state = "available"

        for conn_id in start_room.connections_in:
            if conn_id in self.rooms:
                room = self.rooms[conn_id]
                if room.state == "locked":
                    room.state = "available"

        self.avatar_x = float(start_room.rect.centerx)
        self.avatar_y = float(start_room.rect.top + 20)
        self._update_scroll_to_player()

    def regenerate(self, seed=None):
        self._generate_map(seed)
        self.anim_timer = 0

    def _update_scroll_to_player(self):
        room = self.rooms.get(self.player_room)
        if not room:
            return
        room_center_x = room.rect.centerx - self.scroll_x
        target_scroll = self.scroll_x + (room_center_x - settings.WINDOW_WIDTH // 2)
        self.target_scroll_x = max(0, min(self.max_scroll_x, target_scroll))

    def update(self, dt, player=None):
        self.anim_timer += dt
        for room in self.rooms.values():
            room.bob_phase += dt * 3

        scroll_speed = 8
        diff = self.target_scroll_x - self.scroll_x
        if abs(diff) > 1:
            self.scroll_x += diff * min(1.0, scroll_speed * dt)
        else:
            self.scroll_x = self.target_scroll_x

        target_room = self.rooms.get(self.player_room)
        if target_room:
            target_x = target_room.rect.centerx
            target_y = target_room.rect.top + 20
        else:
            target_x = self.avatar_x
            target_y = self.avatar_y

        dx = target_x - self.avatar_x
        dy = target_y - self.avatar_y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist > 2:
            move_step = 300 * dt
            if dist < move_step:
                self.avatar_x = target_x
                self.avatar_y = target_y
                if player:
                    player.current_anim = "idle"
            else:
                self.avatar_x += (dx / dist) * move_step
                self.avatar_y += (dy / dist) * move_step
                if player:
                    player.current_anim = "walk"
                    if abs(dx) > 1:
                        player.dir_x = 1 if dx > 0 else -1
        else:
            self.avatar_x = target_x
            self.avatar_y = target_y
            if player:
                player.current_anim = "idle"

        if player:
            player.update_animation(dt)

    def navigate(self, direction):
        current_room = self.rooms.get(self.player_room)
        if current_room is None:
            return False

        target = None
        if direction == "up":
            candidates = [rid for rid in current_room.connections if rid in self.rooms]
            for rid in candidates:
                r = self.rooms[rid]
                if r.row < current_room.row and r.state != "locked":
                    target = rid
                    break
        elif direction == "down":
            candidates = [rid for rid in current_room.connections if rid in self.rooms]
            for rid in candidates:
                r = self.rooms[rid]
                if r.row > current_room.row and r.state != "locked":
                    target = rid
                    break
        elif direction == "left":
            candidates = [rid for rid in current_room.connections if rid in self.rooms]
            for rid in candidates:
                r = self.rooms[rid]
                if r.col < current_room.col and r.state != "locked":
                    target = rid
                    break
        elif direction == "right":
            candidates = [rid for rid in current_room.connections if rid in self.rooms]
            for rid in candidates:
                r = self.rooms[rid]
                if r.col > current_room.col and r.state != "locked":
                    target = rid
                    break

        if target:
            self.player_room = target
            self._update_scroll_to_player()
            return True
        return False

    def get_room_at_pos(self, pos):
        adjusted_x = pos[0] + self.scroll_x
        adjusted_pos = (adjusted_x, pos[1])
        for room in self.rooms.values():
            if room.rect.collidepoint(adjusted_pos):
                return room
        return None

    def set_player_room(self, room_id):
        room = self.rooms.get(room_id)
        if room and room.state != "locked":
            self.player_room = room_id
            self._update_scroll_to_player()
            return True
        return False

    def select_room(self):
        room = self.rooms.get(self.player_room)
        if room and room.state in ("available", "completed"):
            return room
        return None

    def complete_room(self, room_id):
        room = self.rooms.get(room_id)
        if room:
            room.state = "completed"
            for conn_id in room.connections:
                conn_room = self.rooms.get(conn_id)
                if conn_room and conn_room.state == "locked":
                    conn_room.state = "available"

    def draw(self, screen, player=None, mp_info=None):
        screen.fill(settings.DARK_BLUE)

        title_y = int(30 * settings.UI_SCALE)
        info_name_y = settings.WINDOW_HEIGHT - int(150 * settings.UI_SCALE)
        info_text_y = settings.WINDOW_HEIGHT - int(110 * settings.UI_SCALE)
        info_action_y = settings.WINDOW_HEIGHT - int(65 * settings.UI_SCALE)
        avatar_size = max(36, int(48 * settings.UI_SCALE))

        draw_text(screen, t("map_title"),
                 (settings.WINDOW_WIDTH // 2, title_y),
                 settings.CYAN, 32)

        if self.max_scroll_x > 0:
            scroll_frac = self.scroll_x / max(1, self.max_scroll_x)
            draw_text(screen, "<" if scroll_frac > 0.05 else " ",
                     (10, settings.WINDOW_HEIGHT // 2),
                     settings.GRAY, 20)
            draw_text(screen, ">" if scroll_frac < 0.95 else " ",
                     (settings.WINDOW_WIDTH - 20, settings.WINDOW_HEIGHT // 2),
                     settings.GRAY, 20)

        clip_rect = pygame.Rect(0, 0, settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT)
        screen.set_clip(clip_rect)

        map_surface = pygame.Surface((settings.WINDOW_WIDTH + 200, settings.WINDOW_HEIGHT))
        map_surface.fill(settings.DARK_BLUE)

        for room in self.rooms.values():
            draw_x = room.rect.x - int(self.scroll_x)
            draw_y = room.rect.y
            draw_rect = pygame.Rect(draw_x, draw_y, room.rect.width, room.rect.height)

            for conn_id in room.connections:
                conn_room = self.rooms.get(conn_id)
                if conn_room and conn_room.col >= room.col:
                    sx = room.rect.centerx - int(self.scroll_x)
                    sy = room.rect.centery
                    ex = conn_room.rect.centerx - int(self.scroll_x)
                    ey = conn_room.rect.centery
                    if room.state == "completed" and conn_room.state == "completed":
                        color = settings.GREEN
                    elif room.state != "locked" and conn_room.state != "locked":
                        color = settings.GRAY
                    else:
                        color = (40, 40, 40)
                    pygame.draw.line(screen, color, (sx, sy), (ex, ey), 2)

        for room in self.rooms.values():
            self._draw_room(screen, room)

        player_room = self.rooms[self.player_room]
        bob_y = int(math.sin(self.anim_timer * 4) * 4)
        avatar_draw_y = self.avatar_y + bob_y
        avatar_draw_x = self.avatar_x - self.scroll_x

        if player:
            sprite = player.get_current_sprite()
            if sprite:
                if player.dir_x < 0:
                    sprite = pygame.transform.flip(sprite, True, False)
                sprite = pygame.transform.scale(sprite, (avatar_size, avatar_size))
                screen.blit(sprite, (int(avatar_draw_x) - avatar_size // 2, int(avatar_draw_y) - avatar_size // 2))
            else:
                pygame.draw.rect(screen, settings.CYAN,
                                (int(avatar_draw_x) - avatar_size // 2, int(avatar_draw_y) - avatar_size // 2, avatar_size, avatar_size))
                pygame.draw.rect(screen, settings.WHITE,
                                (int(avatar_draw_x) - avatar_size // 2, int(avatar_draw_y) - avatar_size // 2, avatar_size, avatar_size), 1)
        else:
            pygame.draw.rect(screen, settings.CYAN,
                            (int(avatar_draw_x) - avatar_size // 2, int(avatar_draw_y) - avatar_size // 2, avatar_size, avatar_size))
            pygame.draw.rect(screen, settings.WHITE,
                            (int(avatar_draw_x) - avatar_size // 2, int(avatar_draw_y) - avatar_size // 2, avatar_size, avatar_size), 1)

        screen.set_clip(None)

        if player_room.state != "locked":
            draw_text(screen, t(player_room.name),
                     (settings.WINDOW_WIDTH // 2, info_name_y),
                     settings.WHITE, 20)
            difficulty_text = "★" * player_room.difficulty
            draw_text(screen, difficulty_text,
                     (settings.WINDOW_WIDTH // 2, info_name_y + 22),
                     settings.GOLD, 16)
            draw_text(screen, t(player_room.narrative),
                     (settings.WINDOW_WIDTH // 2, info_text_y),
                     settings.GRAY, 14)
            gold_str = f"+{player_room.gold_reward} gold"
            draw_text(screen, gold_str,
                     (settings.WINDOW_WIDTH // 2, info_text_y + 22),
                     settings.GOLD, 13)
            if player_room.state == "available":
                draw_text(screen, t("press_enter_room"),
                         (settings.WINDOW_WIDTH // 2, info_action_y),
                         settings.GREEN, 16)
            elif player_room.state == "completed":
                draw_text(screen, t("room_completed_replay"),
                         (settings.WINDOW_WIDTH // 2, info_action_y),
                          settings.GOLD, 16)
        else:
            draw_text(screen, t("unknown"),
                     (settings.WINDOW_WIDTH // 2, info_text_y),
                     settings.GRAY, 16)

        if mp_info:
            for info in mp_info:
                self._draw_mp_avatar(screen, info, avatar_size, bob_y)

        draw_text(screen, t("map_footer"),
                 (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT - 15),
                 settings.GRAY, 14)

        gold_str = f"Gold: {self._get_gold()}"
        draw_text(screen, gold_str,
                 (settings.WINDOW_WIDTH - 100, title_y),
                 settings.GOLD, 18)

    def _get_gold(self):
        try:
            return self._game.gold
        except:
            return 0

    def _draw_room(self, screen, room):
        draw_x = room.rect.x - int(self.scroll_x)
        draw_y = room.rect.y
        draw_rect = pygame.Rect(draw_x, draw_y, room.rect.width, room.rect.height)

        is_player = room.id == self.player_room

        diff_colors = {
            1: ((25, 35, 50), settings.CYAN),
            2: ((35, 30, 20), settings.ORANGE),
            3: ((45, 20, 20), settings.RED),
            4: ((50, 15, 50), settings.PURPLE),
        }

        if room.type == "hub":
            bg_color = (20, 30, 50)
            border_color = settings.CYAN
        elif room.type == "boss":
            bg_color = (50, 15, 15)
            border_color = settings.RED
        elif room.type == "challenge":
            bg_color = diff_colors.get(room.difficulty, diff_colors[1])[0]
            border_color = diff_colors.get(room.difficulty, diff_colors[1])[1]
        else:
            bg_color = diff_colors.get(room.difficulty, diff_colors[1])[0]
            border_color = diff_colors.get(room.difficulty, diff_colors[1])[1]

        if room.state == "completed":
            bg_color = (15, 45, 15)
            border_color = settings.GREEN
        elif room.state == "locked":
            bg_color = (15, 15, 15)
            border_color = (40, 40, 40)

        pygame.draw.rect(screen, bg_color, draw_rect, border_radius=6)

        border_width = 3 if is_player else 2
        if is_player:
            pulse = int(180 + 75 * math.sin(room.bob_phase * 2))
            border_color = (pulse, pulse, 255)

        pygame.draw.rect(screen, border_color, draw_rect, border_width, border_radius=6)

        if room.state == "completed" and not is_player:
            glow = pygame.Surface((draw_rect.width + 4, draw_rect.height + 4))
            glow.set_alpha(30)
            glow.fill(settings.GREEN)
            screen.blit(glow, (draw_rect.x - 2, draw_rect.y - 2))

        icon = self._get_room_icon(room)
        icon_color = settings.WHITE if room.state != "locked" else (60, 60, 60)
        if room.state == "completed":
            icon_color = settings.GREEN
        draw_text(screen, icon, (draw_rect.centerx, draw_rect.centery - 8), icon_color, 20)

        star_str = "★" * room.difficulty
        star_color = settings.GOLD if room.state != "locked" else (50, 50, 50)
        draw_text(screen, star_str, (draw_rect.centerx, draw_rect.centery + 8), star_color, 10)

        name_color = settings.LIGHT_GRAY if room.state != "locked" else (50, 50, 50)
        if room.state == "completed":
            name_color = settings.GREEN
        draw_text(screen, t(room.name),
                 (draw_rect.centerx, draw_rect.bottom - int(10 * settings.UI_SCALE)),
                 name_color, 8)

    def _get_room_icon(self, room):
        if room.state == "completed":
            return "OK"
        if room.state == "locked":
            return "X"
        if room.type == "hub":
            return "H"
        if room.type == "boss":
            return "B"
        if room.type == "challenge":
            return "!"
        if room.type == "victory":
            return "V"
        return "O"

    def _draw_mp_avatar(self, screen, info, avatar_size, bob_y):
        ax = info.get("x", 0) - self.scroll_x
        ay = info.get("y", 0) + bob_y
        label = info.get("label", "P2")
        color = info.get("color", settings.GOLD)
        remote_player = info.get("player")

        if remote_player is not None:
            sprite = remote_player.get_current_sprite()
            if sprite:
                if remote_player.dir_x < 0:
                    sprite = pygame.transform.flip(sprite, True, False)
                sprite = pygame.transform.scale(sprite, (avatar_size, avatar_size))
                screen.blit(sprite, (int(ax) - avatar_size // 2, int(ay) - avatar_size // 2))
            else:
                pygame.draw.rect(screen, color,
                                 (int(ax) - avatar_size // 2, int(ay) - avatar_size // 2, avatar_size, avatar_size))
                pygame.draw.rect(screen, settings.WHITE,
                                 (int(ax) - avatar_size // 2, int(ay) - avatar_size // 2, avatar_size, avatar_size), 1)

        font = pygame.font.Font(None, 20)
        tag = font.render(label, True, settings.BLACK)
        badge_w = tag.get_width() + 8
        badge_h = tag.get_height() + 4
        badge_x = int(ax) - badge_w // 2
        badge_y = int(ay) - avatar_size // 2 - badge_h - 3
        pygame.draw.rect(screen, color, (badge_x, badge_y, badge_w, badge_h), border_radius=4)
        screen.blit(tag, (badge_x + 4, badge_y + 2))