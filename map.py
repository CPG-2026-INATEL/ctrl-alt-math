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
        
        # Smooth avatar movement
        start_room = self.rooms[start]
        self.avatar_x = start_room.rect.centerx
        self.avatar_y = start_room.rect.bottom + 20

    def update(self, dt, player=None):
        self.anim_timer += dt
        for room in self.rooms.values():
            room.bob_phase += dt * 3
            
        # Update avatar position
        target_room = self.rooms[self.player_room]
        target_x = target_room.rect.centerx
        target_y = target_room.rect.bottom + 20
        
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
        target = None
        if direction == "up" and (col, row - 1) in self.rooms:
            target = (col, row - 1)
        elif direction == "down" and (col, row + 1) in self.rooms:
            target = (col, row + 1)
        elif direction == "left" and (col - 1, row) in self.rooms:
            target = (col - 1, row)
        elif direction == "right" and (col + 1, row) in self.rooms:
            target = (col + 1, row)

        if target:
            self.player_room = target
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

        player_room = self.rooms[self.player_room]
        title_text = t(player_room.name) if player_room.state != "locked" else t("unknown")
        
        draw_text(screen, title_text,
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

        bob_y = int(math.sin(self.anim_timer * 4) * 4)
        avatar_draw_y = self.avatar_y + bob_y
        
        if player:
            # Draw player skin
            sprite = player.get_current_sprite()
            if sprite:
                if player.dir_x < 0:
                    sprite = pygame.transform.flip(sprite, True, False)
                sprite = pygame.transform.scale(sprite, (48, 48))
                screen.blit(sprite, (self.avatar_x - 24, avatar_draw_y - 24))
            else:
                pygame.draw.rect(screen, settings.CYAN,
                                (self.avatar_x - 8, avatar_draw_y - 8, 16, 16))
                pygame.draw.rect(screen, settings.WHITE,
                                (self.avatar_x - 8, avatar_draw_y - 8, 16, 16), 1)
        else:
            pygame.draw.rect(screen, settings.CYAN,
                            (self.avatar_x - 8, avatar_draw_y - 8, 16, 16))
            pygame.draw.rect(screen, settings.WHITE,
                            (self.avatar_x - 8, avatar_draw_y - 8, 16, 16), 1)

        if player_room.state != "locked":
            draw_text(screen, t(player_room.name),
                     (settings.WINDOW_WIDTH // 2, 510),
                     settings.WHITE, 20)
            draw_text(screen, t(player_room.narrative),
                     (settings.WINDOW_WIDTH // 2, 535),
                     settings.GRAY, 14)
            if player_room.state == "available":
                draw_text(screen, t("press_enter_room"),
                         (settings.WINDOW_WIDTH // 2, 565),
                         settings.GREEN, 16)
            elif player_room.state == "completed":
                draw_text(screen, t("room_completed_replay"),
                         (settings.WINDOW_WIDTH // 2, 565),
                          settings.GOLD, 16)
        else:
            draw_text(screen, t("unknown"),
                     (settings.WINDOW_WIDTH // 2, 535),
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
