import pygame
import math
import settings
from utils import draw_text


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
        for (col, row), data in settings.MAP_ROOMS.items():
            self.rooms[(col, row)] = Room(col, row, data)

        start = settings.MAP_START_ROOM
        self.rooms[start].state = "available"
        for conn in self.rooms[start].connections:
            if conn in self.rooms:
                self.rooms[conn].state = "available"

        self.player_room = start
        self.anim_timer = 0

    def update(self, dt):
        self.anim_timer += dt
        for room in self.rooms.values():
            room.bob_phase += dt * 3

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

    def draw(self, screen):
        screen.fill(settings.DARK_BLUE)

        draw_text(screen, "THE FORBIDDEN ARCHIVE",
                 (settings.WINDOW_WIDTH // 2, 25),
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
        bob_y = int(math.sin(player_room.bob_phase) * 4)
        avatar_x = player_room.rect.centerx
        avatar_y = player_room.rect.bottom + 20 + bob_y
        pygame.draw.rect(screen, settings.CYAN,
                        (avatar_x - 8, avatar_y - 8, 16, 16))
        pygame.draw.rect(screen, settings.WHITE,
                        (avatar_x - 8, avatar_y - 8, 16, 16), 1)

        if player_room.state != "locked":
            draw_text(screen, player_room.name,
                     (settings.WINDOW_WIDTH // 2, 510),
                     settings.WHITE, 20)
            draw_text(screen, player_room.narrative,
                     (settings.WINDOW_WIDTH // 2, 535),
                     settings.GRAY, 14)
            if player_room.state == "available":
                draw_text(screen, "Press ENTER to enter",
                         (settings.WINDOW_WIDTH // 2, 565),
                         settings.GREEN, 16)
            elif player_room.state == "completed":
                draw_text(screen, "Completed - ENTER to replay",
                         (settings.WINDOW_WIDTH // 2, 565),
                          settings.GOLD, 16)
        else:
            draw_text(screen, "???",
                     (settings.WINDOW_WIDTH // 2, 535),
                     settings.GRAY, 16)

        draw_text(screen, "WASD: Navigate | ENTER: Enter | ESC: Menu",
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
        draw_text(screen, room.name,
                 (rect.centerx, rect.bottom - 12),
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
