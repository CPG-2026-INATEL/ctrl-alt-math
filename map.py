import pygame
import math
import settings
from utils import draw_text
from i18n import t


class Room:
    def __init__(self, col, row, data):
        self.col = col
        self.row = row
        self.type = data["type"]
        self.name = data["name"]
        self.narrative = data["narrative"]
        self.connections = data["connections"]
        self.enemies = data["enemies"]
        self.obstacles = data["obstacles"]
        self.boss_hp = data.get("boss_hp", settings.BOSS_HP)
        
        # Scale enemies based on difficulty
        scale = settings.DIFFICULTY_SCALING[settings.DIFFICULTY]["enemy_amount"]
        scaled_enemies = []
        for e_type, count in self.enemies:
            new_count = max(1, int(count * scale)) if count > 0 else 0
            # Special case: don't scale bosses to 0 or multiple
            if e_type == "boss":
                new_count = count
            scaled_enemies.append((e_type, new_count))
        self.enemies = scaled_enemies
        
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
    def __init__(self):
        self.rooms = {}
        max_col = settings.DIFFICULTY_SCALING[settings.DIFFICULTY]["map_max_col"]
        
        # Filter rooms and adjust connections
        for (col, row), data in settings.MAP_ROOMS.items():
            if col <= max_col:
                # Special case: If this room connects to something outside max_col, 
                # and it's a boss room, make it connect to victory if victory is outside.
                # Actually, simpler: if victory is outside, find the 'highest' reachable boss 
                # and make it the victory room or connect to a moved victory room.
                
                # Let's just filter the connections list to only include valid rooms
                valid_connections = [conn for conn in data["connections"] if conn[0] <= max_col]
                
                # If we filtered out the victory room, we need a way to win.
                # Find if any removed connection was to a 'victory' type room.
                for conn in data["connections"]:
                    if conn[0] > max_col:
                        target_data = settings.MAP_ROOMS.get(conn)
                        if target_data and target_data["type"] == "victory":
                            # Make a "phantom" victory room at the edge?
                            # Or just change this room to victory? 
                            # Better: if we are at the edge, and this room is completed, you win?
                            pass

                room_data = data.copy()
                room_data["connections"] = valid_connections
                self.rooms[(col, row)] = Room(col, row, room_data)

        # Ensure at least one victory room or boss that leads to end
        has_victory = any(r.type == "victory" for r in self.rooms.values())
        if not has_victory:
            # Prioritize boss rooms as the new victory point
            boss_rooms = [pos for pos, r in self.rooms.items() if r.type == "boss"]
            if boss_rooms:
                target_pos = max(boss_rooms, key=lambda k: k[0])
            else:
                # Fallback to furthest non-hub room
                non_hub_rooms = [pos for pos, r in self.rooms.items() if r.type != "hub"]
                if non_hub_rooms:
                    target_pos = max(non_hub_rooms, key=lambda k: k[0])
                else:
                    target_pos = max(self.rooms.keys(), key=lambda k: k[0])
            
            self.rooms[target_pos].type = "victory"
            self.rooms[target_pos].name = "room_victory_name"
            self.rooms[target_pos].narrative = "room_victory_narr"

        start = settings.MAP_START_ROOM
        self.rooms[start].state = "available"
        for conn in self.rooms[start].connections:
            if conn in self.rooms:
                self.rooms[conn].state = "available"

        self.player_room = start
        self.anim_timer = 0
        
        # Smooth avatar movement
        start_room = self.rooms[start]
        self.avatar_x = start_room.rect.centerx
        self.avatar_y = start_room.rect.top + 20

    def update(self, dt, player=None):
        self.anim_timer += dt
        for room in self.rooms.values():
            room.bob_phase += dt * 3
            
        # Update avatar position
        target_room = self.rooms[self.player_room]
        target_x = target_room.rect.centerx
        target_y = target_room.rect.top + 20
        
        dx = target_x - self.avatar_x
        dy = target_y - self.avatar_y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 2:
            speed = 300
            move_step = speed * dt
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
                    # Only flip if moving significantly horizontally
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
        col, row = self.player_room
        current_room = self.rooms.get((col, row))
        if current_room is None:
            return False

        target = None
        if direction == "up" and (col, row - 1) in self.rooms:
            target = (col, row - 1)
        elif direction == "down" and (col, row + 1) in self.rooms:
            target = (col, row + 1)
        elif direction == "left" and (col - 1, row) in self.rooms:
            target = (col - 1, row)
        elif direction == "right" and (col + 1, row) in self.rooms:
            target = (col + 1, row)

        if target and target in current_room.connections:
            target_room = self.rooms.get(target)
            if target_room and target_room.state != "locked":
                self.player_room = target
                return True
        return False

    def get_room_at_pos(self, pos):
        for room in self.rooms.values():
            if room.rect.collidepoint(pos):
                return room
        return None

    def set_player_room(self, room_pos):
        room = self.rooms.get(room_pos)
        if room and room.state != "locked":
            self.player_room = room_pos
            return True
        return False

    def select_room(self):
        room = self.rooms.get(self.player_room)
        if room and room.state in ("available", "completed"):
            return room
        return None

    def complete_room(self, room_pos):
        room = self.rooms.get(room_pos)
        if room:
            room.state = "completed"
            for conn in room.connections:
                if conn in self.rooms:
                    conn_room = self.rooms[conn]
                    if conn_room.state == "locked":
                        conn_room.state = "available"

    def draw(self, screen, player=None):
        screen.fill(settings.DARK_BLUE)

        title_y = int(30 * settings.UI_SCALE)
        info_name_y = settings.WINDOW_HEIGHT - int(150 * settings.UI_SCALE)
        info_text_y = settings.WINDOW_HEIGHT - int(110 * settings.UI_SCALE)
        info_action_y = settings.WINDOW_HEIGHT - int(65 * settings.UI_SCALE)
        avatar_size = max(36, int(48 * settings.UI_SCALE))
        avatar_offset_y = int(20 * settings.UI_SCALE)

        draw_text(screen, t("archive_title"),
                 (settings.WINDOW_WIDTH // 2, title_y),
                 settings.CYAN, 32)

        for room in self.rooms.values():
            for conn_pos in room.connections:
                conn_room = self.rooms.get(conn_pos)
                if conn_room and conn_room.col >= room.col:
                    start = room.rect.center
                    end = conn_room.rect.center
                    if room.state == "completed" and conn_room.state == "completed":
                        color = settings.GREEN
                    elif room.state != "locked" and conn_room.state != "locked":
                        color = settings.GRAY
                    else:
                        color = (40, 40, 40)
                    pygame.draw.line(screen, color, start, end, 2)

        for room in self.rooms.values():
            self._draw_room(screen, room)

        player_room = self.rooms[self.player_room]
        bob_y = int(math.sin(self.anim_timer * 4) * 4)
        avatar_draw_y = self.avatar_y + bob_y

        if player:
            sprite = player.get_current_sprite()
            if sprite:
                if player.dir_x < 0:
                    sprite = pygame.transform.flip(sprite, True, False)
                sprite = pygame.transform.scale(sprite, (avatar_size, avatar_size))
                screen.blit(sprite, (self.avatar_x - avatar_size // 2, avatar_draw_y - avatar_size // 2))
            else:
                pygame.draw.rect(screen, settings.CYAN,
                                (self.avatar_x - avatar_size // 2, avatar_draw_y - avatar_size // 2, avatar_size, avatar_size))
                pygame.draw.rect(screen, settings.WHITE,
                                (self.avatar_x - avatar_size // 2, avatar_draw_y - avatar_size // 2, avatar_size, avatar_size), 1)
        else:
            pygame.draw.rect(screen, settings.CYAN,
                            (self.avatar_x - avatar_size // 2, avatar_draw_y - avatar_size // 2, avatar_size, avatar_size))
            pygame.draw.rect(screen, settings.WHITE,
                            (self.avatar_x - avatar_size // 2, avatar_draw_y - avatar_size // 2, avatar_size, avatar_size), 1)

        if player_room.state != "locked":
            draw_text(screen, t(player_room.name),
                     (settings.WINDOW_WIDTH // 2, info_name_y),
                     settings.WHITE, 20)
            draw_text(screen, t(player_room.narrative),
                     (settings.WINDOW_WIDTH // 2, info_text_y),
                     settings.GRAY, 14)
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

        draw_text(screen, t("map_footer"),
                 (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT - 15),
                 settings.GRAY, 14)

    def _draw_room(self, screen, room):
        rect = room.rect
        is_player = (room.col, room.row) == self.player_room

        if room.type == "hub":
            bg_color = (20, 30, 50)
            border_color = settings.CYAN
        elif room.type == "boss":
            bg_color = (50, 15, 15)
            border_color = settings.RED
        elif room.type == "challenge":
            bg_color = (40, 30, 15)
            border_color = settings.ORANGE
        elif room.type == "victory":
            bg_color = (28, 22, 42)
            border_color = settings.GOLD
        else:
            bg_color = (25, 25, 40)
            border_color = settings.LIGHT_GRAY

        if room.state == "completed":
            bg_color = (15, 45, 15)
            border_color = settings.GREEN
        elif room.state == "locked":
            bg_color = (15, 15, 15)
            border_color = (40, 40, 40)

        pygame.draw.rect(screen, bg_color, rect, border_radius=6)

        border_width = 3 if is_player else 2
        if is_player:
            pulse = int(180 + 75 * math.sin(room.bob_phase * 2))
            border_color = (pulse, pulse, 255)
            border_width = 3

        pygame.draw.rect(screen, border_color, rect, border_width, border_radius=6)

        if room.state == "completed" and not is_player:
            glow = pygame.Surface((rect.width + 4, rect.height + 4))
            glow.set_alpha(30)
            glow.fill(settings.GREEN)
            screen.blit(glow, (rect.x - 2, rect.y - 2))

        icon = self._get_room_icon(room)
        icon_color = settings.WHITE if room.state != "locked" else (60, 60, 60)
        if room.state == "completed":
            icon_color = settings.GREEN
        draw_text(screen, icon, rect.center, icon_color, 24)

        name_color = settings.LIGHT_GRAY if room.state != "locked" else (50, 50, 50)
        if room.state == "completed":
            name_color = settings.GREEN
        draw_text(screen, t(room.name),
                 (rect.centerx, rect.bottom - int(12 * settings.UI_SCALE)),
                 name_color, 10)

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
