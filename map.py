import pygame
import math
import random
import settings
from utils import draw_text
from i18n import t
from map_generator import MapGenerator


# --- Pre-rendered symbol cache ---
_symbol_cache = {}

def _get_symbol_surface(symbol, size, color):
    key = (symbol, size, color)
    if key not in _symbol_cache:
        font = pygame.font.Font(None, size)
        _symbol_cache[key] = font.render(symbol, True, color)
    return _symbol_cache[key]


# --- Pre-rendered gradient cache ---
_gradient_cache = {}

def _get_gradient_surface(w, h, bg_color):
    key = (w, h, bg_color)
    if key not in _gradient_cache:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(h):
            ratio = y / h
            r = int(bg_color[0] * (1 - ratio * 0.3))
            g = int(bg_color[1] * (1 - ratio * 0.3))
            b = int(bg_color[2] * (1 - ratio * 0.3))
            pygame.draw.line(surf, (r, g, b, 220), (0, y), (w, y))
        pygame.draw.rect(surf, (255, 255, 255, 8), (1, 1, w - 2, h // 3), border_radius=10)
        _gradient_cache[key] = surf
    return _gradient_cache[key]


# --- Pre-rendered glow surfaces ---
_glow_cache = {}

def _get_glow_surface(w, h, color, alpha, radius):
    key = (w, h, color, alpha, radius)
    if key not in _glow_cache:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (*color, alpha), (0, 0, w, h), border_radius=radius)
        _glow_cache[key] = surf
    return _glow_cache[key]


# --- Shape drawing helpers ---
def _draw_hexagon(surface, cx, cy, radius, color, width=2):
    pts = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        pts.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    pygame.draw.polygon(surface, color, pts, width)


def _draw_diamond(surface, cx, cy, size, color, width=2):
    pts = [(cx, cy - size), (cx + size * 0.7, cy), (cx, cy + size), (cx - size * 0.7, cy)]
    pygame.draw.polygon(surface, color, pts, width)


def _draw_triangle(surface, cx, cy, size, color, width=2):
    pts = [(cx, cy - size), (cx + size * 0.87, cy + size * 0.5), (cx - size * 0.87, cy + size * 0.5)]
    pygame.draw.polygon(surface, color, pts, width)


def _draw_pentagon(surface, cx, cy, radius, color, width=2):
    pts = []
    for i in range(5):
        angle = math.radians(72 * i - 90)
        pts.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    pygame.draw.polygon(surface, color, pts, width)


def _draw_checkmark(surface, cx, cy, size, color, width=3):
    start = (cx - size * 0.5, cy)
    mid = (cx - size * 0.1, cy + size * 0.4)
    end = (cx + size * 0.5, cy - size * 0.5)
    pygame.draw.line(surface, color, start, mid, width)
    pygame.draw.line(surface, color, mid, end, width)


def _draw_lock_icon(surface, cx, cy, size, color, width=2):
    body = pygame.Rect(cx - size * 0.4, cy, size * 0.8, size * 0.6)
    pygame.draw.rect(surface, color, body, width, border_radius=2)
    arc_rect = pygame.Rect(cx - size * 0.3, cy - size * 0.5, size * 0.6, size * 0.5)
    pygame.draw.arc(surface, color, arc_rect, math.pi, 0, width)


def _draw_circle_icon(surface, cx, cy, radius, color, width=2):
    pygame.draw.circle(surface, color, (int(cx), int(cy)), radius, width)


def _draw_victory_crown(surface, cx, cy, size, color, width=2):
    pts = [
        (cx - size, cy + size * 0.5),
        (cx - size, cy - size * 0.3),
        (cx - size * 0.5, cy + size * 0.1),
        (cx, cy - size * 0.6),
        (cx + size * 0.5, cy + size * 0.1),
        (cx + size, cy - size * 0.3),
        (cx + size, cy + size * 0.5),
    ]
    pygame.draw.polygon(surface, color, pts, width)


# --- Particle classes ---
class _MathParticle:
    MATH_SYMBOLS = ["∫", "∂", "∑", "π", "√", "Δ", "∞", "λ", "θ", "φ", "∇", "±", "≈", "≠", "α", "β", "ε", "σ"]
    SYMBOL_COLOR = (100, 140, 200)

    def __init__(self, w, h):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h)
        self.vx = random.uniform(-8, 8)
        self.vy = random.uniform(-12, -3)
        self.symbol = random.choice(self.MATH_SYMBOLS)
        self.alpha = random.uniform(20, 60)
        self.size = random.randint(10, 16)
        self.w = w
        self.h = h

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.alpha -= 10 * dt
        if self.y < -20 or self.alpha <= 0:
            self.reset()

    def reset(self):
        self.x = random.uniform(0, self.w)
        self.y = self.h + random.uniform(0, 30)
        self.vx = random.uniform(-8, 8)
        self.vy = random.uniform(-12, -3)
        self.alpha = random.uniform(20, 60)
        self.symbol = random.choice(self.MATH_SYMBOLS)

    def draw(self, screen, sx, sy, offset_y=0):
        if self.alpha <= 0:
            return
        surf = _get_symbol_surface(self.symbol, self.size, self.SYMBOL_COLOR)
        surf_copy = surf.copy()
        surf_copy.set_alpha(int(self.alpha))
        screen.blit(surf_copy, (int(self.x - sx), int(self.y - sy + offset_y)))


class _FlowParticle:
    def __init__(self, start_pos, end_pos, color, speed=60):
        self.start = start_pos
        self.end = end_pos
        self.t = 0.0
        self.color = color
        self.speed = speed
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        self.length = math.sqrt(dx * dx + dy * dy)
        self.duration = self.length / speed if self.length > 0 else 1.0

    def update(self, dt):
        self.t += dt / self.duration if self.duration > 0 else 0
        return self.t < 1.0

    def get_pos(self):
        t = max(0, min(1, self.t))
        x = self.start[0] + (self.end[0] - self.start[0]) * t
        y = self.start[1] + (self.end[1] - self.start[1]) * t
        return (x, y)

    def draw(self, screen, sx, sy, offset_y=0):
        pos = self.get_pos()
        alpha = max(0, min(255, int(255 * (1 - self.t))))
        px = int(pos[0] - sx)
        py = int(pos[1] - sy + offset_y)
        pygame.draw.circle(screen, (*self.color, alpha), (px, py), 4)
        pygame.draw.circle(screen, self.color, (px, py), 2)


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
        self.jitter_x = data.get("jitter_x", 0)
        self.jitter_y = data.get("jitter_y", 0)

        scale = settings.DIFFICULTY_SCALING[settings.DIFFICULTY]["enemy_amount"]
        scaled_enemies = []
        for e_type, count in self.enemies:
            new_count = max(1, int(count * scale)) if count > 0 else 0
            if e_type == "boss":
                new_count = count
            scaled_enemies.append((e_type, new_count))
        self.enemies = scaled_enemies

        if self.type != "boss" and self.type != "hub":
            total_enemies = sum(c for _, c in self.enemies)
            base = settings.GOLD_PER_STAR.get(self.difficulty, 20)
            gold_per_enemy = settings.GOLD_PER_ENEMY.get(self.difficulty, 5)
            self.gold_reward = base + total_enemies * gold_per_enemy
            if self.type == "side":
                self.gold_reward = int(self.gold_reward * 1.3)

        self.connections_out = data.get("connections_out", [])
        self.connections_in = data.get("connections_in", [])
        self.connections = data.get("connections", data.get("all_connections", []))
        if not self.connections:
            self.connections = list(set(self.connections_out + self.connections_in))

        self.directional_connections = data.get("directional_connections", {})

        self.state = "locked"
        self.bob_phase = 0

    @property
    def screen_x(self):
        return settings.MAP_OFFSET_X + self.col * (settings.MAP_ROOM_WIDTH + settings.MAP_ROOM_GAP) + self.jitter_x

    @property
    def screen_y(self):
        return settings.MAP_OFFSET_Y + self.row * (settings.MAP_ROOM_HEIGHT + settings.MAP_ROOM_GAP) + self.jitter_y

    @property
    def rect(self):
        return pygame.Rect(self.screen_x, self.screen_y,
                          settings.MAP_ROOM_WIDTH, settings.MAP_ROOM_HEIGHT)


class WorldMap:
    def __init__(self, seed=None):
        self.seed = seed
        self.rooms = {}
        self.connections_map = {}
        self.layers = []
        self.player_room = settings.MAP_START_ROOM
        self.anim_timer = 0
        self.scroll_x = 0
        self.target_scroll_x = 0
        self.max_scroll_x = 0
        self.min_scroll_x = 0
        self.scroll_y = 0
        self.target_scroll_y = 0
        self.max_scroll_y = 0
        self.min_scroll_y = 0
        self.hovered_room = None

        self.avatar_x = 0
        self.avatar_y = 0
        self.mp_avatars = []

        self._bg_particles = []
        self._flow_particles = []
        self._avatar_trail = []
        self._bg_grad = None
        self._grid_surf = None
        self._header_surf = None
        self._bottom_bar_surf = None
        self._star_surf_cache = {}

        self._generate_map(seed)
        self._init_bg_particles()
        self._build_grid_surface()
        self._build_header_surface()
        self._build_bottom_bar_surface()

    def _init_bg_particles(self):
        self._bg_particles = [_MathParticle(settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT) for _ in range(25)]

    def _generate_map(self, seed=None):
        gen = MapGenerator(seed)
        self.seed = gen.seed
        rooms, connections, layers = gen.generate(settings.DIFFICULTY)

        for room_id, room_data in rooms.items():
            self.rooms[room_id] = Room(room_id, room_data)

        self.connections_map = connections
        self.layers = layers

        content_right = max(
            (r.screen_x + settings.MAP_ROOM_WIDTH + settings.MAP_ROOM_GAP)
            for r in self.rooms.values()
        )
        content_bottom = max(
            (r.screen_y + settings.MAP_ROOM_HEIGHT + settings.MAP_ROOM_GAP)
            for r in self.rooms.values()
        )
        content_top = min(r.screen_y for r in self.rooms.values())

        visible_width = settings.WINDOW_WIDTH - 40
        visible_height = settings.WINDOW_HEIGHT - settings.MAP_HEADER_H - 40

        self.max_scroll_x = max(0, content_right - visible_width)
        self.min_scroll_x = min(0, content_right - settings.WINDOW_WIDTH + 100)

        self.max_scroll_y = max(0, content_bottom - settings.MAP_HEADER_H - visible_height)
        self.min_scroll_y = min(0, content_top - settings.MAP_HEADER_H + 20)

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

        for conn_id in start_room.directional_connections.values():
            if conn_id and conn_id in self.rooms:
                room = self.rooms[conn_id]
                if room.state == "locked":
                    room.state = "available"

        self.avatar_x = float(start_room.rect.centerx)
        self.avatar_y = float(start_room.rect.top + 20)
        self._update_scroll_to_player()
        self._build_bg_gradient()

    def _build_bg_gradient(self):
        grad = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
        for y in range(settings.WINDOW_HEIGHT):
            ratio = y / settings.WINDOW_HEIGHT
            r = int(5 + ratio * 10)
            g = int(5 + ratio * 5)
            b = int(25 + ratio * 15)
            pygame.draw.line(grad, (r, g, b), (0, y), (settings.WINDOW_WIDTH, y))
        self._bg_grad = grad

    def _build_grid_surface(self):
        self._grid_surf = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
        grid_spacing = 60
        for x in range(0, settings.WINDOW_WIDTH + grid_spacing, grid_spacing):
            pygame.draw.line(self._grid_surf, (30, 40, 60), (x, settings.MAP_HEADER_H), (x, settings.WINDOW_HEIGHT), 1)
        for y in range(settings.MAP_HEADER_H, settings.WINDOW_HEIGHT + grid_spacing, grid_spacing):
            pygame.draw.line(self._grid_surf, (30, 40, 60), (0, y), (settings.WINDOW_WIDTH, y), 1)

    def _build_header_surface(self):
        self._header_surf = pygame.Surface((settings.WINDOW_WIDTH, settings.MAP_HEADER_H), pygame.SRCALPHA)
        for y in range(settings.MAP_HEADER_H):
            ratio = y / settings.MAP_HEADER_H
            alpha = int(220 + 35 * (1 - ratio))
            pygame.draw.line(self._header_surf, (8, 10, 30, alpha), (0, y), (settings.WINDOW_WIDTH, y))
        pygame.draw.line(self._header_surf, (50, 255, 255, 80),
                         (0, settings.MAP_HEADER_H - 1), (settings.WINDOW_WIDTH, settings.MAP_HEADER_H - 1), 2)

    def _build_bottom_bar_surface(self):
        bar_y = 0
        self._bottom_bar_surf = pygame.Surface((settings.WINDOW_WIDTH, 24), pygame.SRCALPHA)
        self._bottom_bar_surf.fill((8, 10, 30, 180))
        pygame.draw.line(self._bottom_bar_surf, (50, 255, 255, 40), (0, bar_y), (settings.WINDOW_WIDTH, bar_y), 1)

    def _get_star_surface(self, color):
        if color in self._star_surf_cache:
            return self._star_surf_cache[color]
        size = 5
        surf = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*color, 40), (size * 1.5, size * 1.5), size * 1.5)
        self._star_surf_cache[color] = surf
        return surf

    def regenerate(self, seed=None):
        self._generate_map(seed)
        self.anim_timer = 0
        self._init_bg_particles()
        self._flow_particles = []
        self._avatar_trail = []
        self._star_surf_cache = {}
        self._build_grid_surface()
        self._build_header_surface()
        self._build_bottom_bar_surface()

    def _update_scroll_to_player(self):
        room = self.rooms.get(self.player_room)
        if not room:
            return

        map_center_y = settings.MAP_HEADER_H + (settings.WINDOW_HEIGHT - settings.MAP_HEADER_H) // 2

        room_center_x = room.rect.centerx - self.scroll_x
        target_sx = self.scroll_x + (room_center_x - settings.WINDOW_WIDTH // 2)
        self.target_scroll_x = max(self.min_scroll_x, min(self.max_scroll_x, target_sx))

        room_center_y = room.rect.centery - self.scroll_y
        target_sy = self.scroll_y + (room_center_y - map_center_y)
        self.target_scroll_y = max(self.min_scroll_y, min(self.max_scroll_y, target_sy))

    def update(self, dt, player=None):
        self.anim_timer += dt
        for room in self.rooms.values():
            room.bob_phase += dt * 3

        scroll_speed = 8
        diff_x = self.target_scroll_x - self.scroll_x
        if abs(diff_x) > 1:
            self.scroll_x += diff_x * min(1.0, scroll_speed * dt)
        else:
            self.scroll_x = self.target_scroll_x

        diff_y = self.target_scroll_y - self.scroll_y
        if abs(diff_y) > 1:
            self.scroll_y += diff_y * min(1.0, scroll_speed * dt)
        else:
            self.scroll_y = self.target_scroll_y

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
                self._avatar_trail.append((self.avatar_x, self.avatar_y, 1.0))
        else:
            self.avatar_x = target_x
            self.avatar_y = target_y
            if player:
                player.current_anim = "idle"

        if player:
            player.update_animation(dt)

        for p in self._bg_particles:
            p.update(dt)

        self._avatar_trail = [(x, y, a - dt * 2) for x, y, a in self._avatar_trail if a > 0]

        self._update_flow_particles(dt)

    def _update_flow_particles(self, dt):
        self._flow_particles = [p for p in self._flow_particles if p.update(dt)]

        if random.random() < 0.08:
            rooms_in_order = sorted(self.rooms.values(), key=lambda r: (r.screen_y, r.screen_x))
            for room in rooms_in_order:
                for conn_id in room.directional_connections.values():
                    if conn_id is None:
                        continue
                    conn_room = self.rooms.get(conn_id)
                    if conn_room and conn_room.col >= room.col:
                        if room.state == "completed" and conn_room.state == "completed":
                            color = settings.GREEN
                        elif room.state != "locked" and conn_room.state != "locked":
                            color = settings.CYAN
                        else:
                            continue
                        start = (room.rect.centerx, room.rect.centery)
                        end = (conn_room.rect.centerx, conn_room.rect.centery)
                        self._flow_particles.append(_FlowParticle(start, end, color, speed=80))
                        break

    def _draw_flow_particles(self, screen, sx, sy):
        for p in self._flow_particles:
            p.draw(screen, sx, sy, settings.MAP_HEADER_H)

    def navigate(self, direction):
        current_room = self.rooms.get(self.player_room)
        if current_room is None:
            return False

        target_id = current_room.directional_connections.get(direction)
        if target_id is None or target_id not in self.rooms:
            return False

        target_room = self.rooms[target_id]
        if target_room.state == "locked":
            return False

        self.player_room = target_id
        self._update_scroll_to_player()
        return True

    def get_room_at_pos(self, pos):
        adjusted_x = pos[0] + self.scroll_x
        adjusted_y = pos[1] - settings.MAP_HEADER_H + self.scroll_y
        adjusted_pos = (adjusted_x, adjusted_y)
        rooms = sorted(self.rooms.values(), key=lambda room: (room.screen_y, room.screen_x), reverse=True)
        for room in rooms:
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
            for conn_id in room.directional_connections.values():
                if conn_id and conn_id in self.rooms:
                    conn_room = self.rooms[conn_id]
                    if conn_room.state == "locked":
                        conn_room.state = "available"

    def all_required_rooms_completed(self):
        required_types = {"normal", "challenge", "boss", "victory"}
        required_rooms = [room for room in self.rooms.values() if room.type in required_types]
        return bool(required_rooms) and all(room.state == "completed" for room in required_rooms)

    def get_state_data(self):
        return {
            "seed": self.seed,
            "player_room": self.player_room,
            "rooms": {room_id: room.state for room_id, room in self.rooms.items()},
        }

    def apply_state_data(self, data):
        if not data:
            return
        seed = data.get("seed")
        if seed is not None and seed != self.seed:
            self._generate_map(seed)
        self.player_room = data.get("player_room", self.player_room)
        for room_id, state in data.get("rooms", {}).items():
            room = self.rooms.get(room_id)
            if room and state in ("locked", "available", "completed"):
                room.state = state
        self._update_scroll_to_player()

    def _get_gold(self):
        try:
            return self._game.gold
        except:
            return 0

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
        if room.type == "side":
            return "$"
        if room.type == "victory":
            return "V"
        return "O"

    def draw(self, screen, player=None, mp_info=None):
        if self._bg_grad:
            screen.blit(self._bg_grad, (0, 0))
        else:
            screen.fill(settings.DARK_BLUE)

        sx = int(self.scroll_x)
        sy = int(self.scroll_y)

        for p in self._bg_particles:
            p.draw(screen, sx, sy, settings.MAP_HEADER_H)

        self._draw_grid(screen, sx, sy)

        map_clip = pygame.Rect(0, settings.MAP_HEADER_H,
                                settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT - settings.MAP_HEADER_H)
        screen.set_clip(map_clip)

        self._draw_connections(screen, sx, sy)
        self._draw_flow_particles(screen, sx, sy)

        rooms_in_draw_order = sorted(self.rooms.values(), key=lambda room: (room.screen_y, room.screen_x))
        for room in rooms_in_draw_order:
            self._draw_room(screen, room, sx, sy)

        self._draw_avatar(screen, player, sx, sy)

        if mp_info:
            avatar_size = max(36, int(48 * settings.UI_SCALE))
            bob_y = int(math.sin(self.anim_timer * 4) * 4)
            for info in mp_info:
                self._draw_mp_avatar(screen, info, avatar_size, bob_y, sx, sy)

        screen.set_clip(None)

        self._draw_header(screen)
        self._draw_bottom_bar(screen)

    def _draw_grid(self, screen, sx, sy):
        if self._grid_surf is None:
            return
        alpha = int(25 + 15 * math.sin(self.anim_timer * 0.5))
        grid_copy = self._grid_surf.copy()
        grid_copy.set_alpha(alpha)
        screen.blit(grid_copy, (0, 0))

    def _draw_connections(self, screen, sx, sy):
        drawn = set()
        rooms_in_draw_order = sorted(self.rooms.values(), key=lambda room: (room.screen_y, room.screen_x))
        for room in rooms_in_draw_order:
            for conn_id in room.directional_connections.values():
                if conn_id is None:
                    continue
                conn_room = self.rooms.get(conn_id)
                if conn_room and conn_room.col >= room.col:
                    pair = tuple(sorted([room.id, conn_room.id]))
                    if pair in drawn:
                        continue
                    drawn.add(pair)

                    start_x = room.rect.centerx - sx
                    start_y = room.rect.centery - sy + settings.MAP_HEADER_H
                    end_x = conn_room.rect.centerx - sx
                    end_y = conn_room.rect.centery - sy + settings.MAP_HEADER_H

                    if room.state == "completed" and conn_room.state == "completed":
                        color = settings.GREEN
                    elif room.state != "locked" and conn_room.state != "locked":
                        color = settings.CYAN
                    else:
                        color = (40, 40, 40)

                    pygame.draw.line(screen, (*color, 40), (start_x, start_y), (end_x, end_y), 8)

                    if room.state == "locked" or conn_room.state == "locked":
                        dx = end_x - start_x
                        dy = end_y - start_y
                        length = math.sqrt(dx * dx + dy * dy)
                        if length > 0:
                            segments = int(length / 10)
                            for i in range(0, segments, 3):
                                t1 = i / segments
                                t2 = min((i + 1.5) / segments, 1)
                                x1 = start_x + dx * t1
                                y1 = start_y + dy * t1
                                x2 = start_x + dx * t2
                                y2 = start_y + dy * t2
                                pygame.draw.line(screen, color, (x1, y1), (x2, y2), 2)
                    else:
                        pygame.draw.line(screen, color, (start_x, start_y), (end_x, end_y), 2)

    def _draw_avatar(self, screen, player, sx, sy):
        bob_y = int(math.sin(self.anim_timer * 4) * 4)
        avatar_draw_y = self.avatar_y - sy + settings.MAP_HEADER_H + bob_y
        avatar_draw_x = self.avatar_x - sx
        avatar_size = max(36, int(48 * settings.UI_SCALE))

        for x, y, a in self._avatar_trail:
            trail_x = x - sx
            trail_y = y - sy + settings.MAP_HEADER_H + bob_y
            trail_alpha = max(0, min(255, int(a * 60)))
            pygame.draw.circle(screen, (50, 255, 255, trail_alpha),
                               (int(trail_x), int(trail_y)), avatar_size // 2)

        pulse = int(40 + 30 * math.sin(self.anim_timer * 5))
        pygame.draw.circle(screen, (50, 255, 255, pulse),
                           (int(avatar_draw_x), int(avatar_draw_y)), avatar_size // 2 + 6)

        if player:
            sprite = player.get_current_sprite()
            if sprite:
                if player.dir_x < 0:
                    sprite = pygame.transform.flip(sprite, True, False)
                sprite = pygame.transform.scale(sprite, (avatar_size, avatar_size))
                screen.blit(sprite, (int(avatar_draw_x) - avatar_size // 2, int(avatar_draw_y) - avatar_size // 2))
            else:
                pygame.draw.rect(screen, settings.CYAN,
                                (int(avatar_draw_x) - avatar_size // 2, int(avatar_draw_y) - avatar_size // 2, avatar_size, avatar_size), border_radius=8)
                pygame.draw.rect(screen, settings.WHITE,
                                (int(avatar_draw_x) - avatar_size // 2, int(avatar_draw_y) - avatar_size // 2, avatar_size, avatar_size), 2, border_radius=8)
        else:
            pygame.draw.rect(screen, settings.CYAN,
                            (int(avatar_draw_x) - avatar_size // 2, int(avatar_draw_y) - avatar_size // 2, avatar_size, avatar_size), border_radius=8)
            pygame.draw.rect(screen, settings.WHITE,
                            (int(avatar_draw_x) - avatar_size // 2, int(avatar_draw_y) - avatar_size // 2, avatar_size, avatar_size), 2, border_radius=8)

    def _draw_header(self, screen):
        if self._header_surf:
            screen.blit(self._header_surf, (0, 0))

        title_y = int(28 * settings.UI_SCALE)
        draw_text(screen, t("map_title"),
                 (settings.WINDOW_WIDTH // 2, title_y),
                 settings.CYAN, 28)

        gold_str = f"Gold: {self._get_gold()}"
        gold_x = settings.WINDOW_WIDTH - 110
        gold_bg = pygame.Surface((100, 26), pygame.SRCALPHA)
        gold_bg.fill((255, 215, 0, 25))
        pygame.draw.rect(gold_bg, (255, 215, 0, 80), (0, 0, 100, 26), 1, border_radius=6)
        screen.blit(gold_bg, (gold_x - 5, title_y - 8))
        draw_text(screen, gold_str, (gold_x + 45, title_y), settings.GOLD, 16)

        total_rooms = len([r for r in self.rooms.values() if r.type not in ("hub", "victory")])
        completed_rooms = len([r for r in self.rooms.values() if r.state == "completed" and r.type not in ("hub", "victory")])

        if total_rooms > 0:
            prog_text = f"{completed_rooms}/{total_rooms}"
            draw_text(screen, prog_text, (15, title_y), settings.GREEN, 16)

            bar_w = 80
            bar_h = 6
            bar_x = 15
            bar_y = title_y + 16
            pygame.draw.rect(screen, (30, 30, 30), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
            if completed_rooms > 0:
                fill_w = int(bar_w * completed_rooms / total_rooms)
                pygame.draw.rect(screen, settings.GREEN, (bar_x, bar_y, fill_w, bar_h), border_radius=3)

        draw_text(screen, "[TAB] Player", (15, settings.MAP_HEADER_H - 18), settings.GRAY, 12, center=False)
        draw_text(screen, "[S] Shop", (100, settings.MAP_HEADER_H - 18), settings.GRAY, 12, center=False)
        draw_text(screen, "[U] Upgrades", (170, settings.MAP_HEADER_H - 18), settings.GRAY, 12, center=False)
        draw_text(screen, "[E] Equip", (265, settings.MAP_HEADER_H - 18), settings.GRAY, 12, center=False)

    def _draw_bottom_bar(self, screen):
        if self._bottom_bar_surf:
            screen.blit(self._bottom_bar_surf, (0, settings.WINDOW_HEIGHT - 24))

        diff_labels = {settings.DIFFICULTY_EASY: "EASY", settings.DIFFICULTY_MEDIUM: "MEDIUM", settings.DIFFICULTY_HARD: "HARD"}
        diff_colors = {settings.DIFFICULTY_EASY: settings.GREEN, settings.DIFFICULTY_MEDIUM: settings.GOLD, settings.DIFFICULTY_HARD: settings.RED}
        diff_label = diff_labels.get(settings.DIFFICULTY, "MEDIUM")
        diff_color = diff_colors.get(settings.DIFFICULTY, settings.GOLD)

        draw_text(screen, f"DIFFICULTY: {diff_label}", (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT - 12), diff_color, 12)

        draw_text(screen, "ESC Menu", (settings.WINDOW_WIDTH - 55, settings.WINDOW_HEIGHT - 12), settings.GRAY, 12, center=False)

    def _draw_room(self, screen, room, sx, sy):
        draw_x = room.rect.x - sx
        draw_y = room.rect.y - sy + settings.MAP_HEADER_H
        draw_rect = pygame.Rect(draw_x, draw_y, room.rect.width, room.rect.height)

        if draw_rect.right < -50 or draw_rect.left > settings.WINDOW_WIDTH + 50:
            return
        if draw_rect.bottom < settings.MAP_HEADER_H - 50 or draw_rect.top > settings.WINDOW_HEIGHT + 50:
            return

        is_player = room.id == self.player_room
        is_hovered = hasattr(self, 'hovered_room') and self.hovered_room and room.id == self.hovered_room.id

        bg_color, border_color = self._get_room_colors(room)

        if room.state == "completed":
            glow_alpha = int(30 + 15 * math.sin(room.bob_phase))
            glow = _get_glow_surface(draw_rect.width + 8, draw_rect.height + 8, (50, 255, 50), glow_alpha, 12)
            screen.blit(glow, (draw_rect.x - 4, draw_rect.y - 4))

        if is_player:
            self._draw_room_pulse(screen, draw_rect, border_color, room.bob_phase)

        if is_hovered:
            hover_glow = _get_glow_surface(draw_rect.width + 12, draw_rect.height + 12, (255, 215, 0), 40, 14)
            screen.blit(hover_glow, (draw_rect.x - 6, draw_rect.y - 6))

        room_grad = _get_gradient_surface(draw_rect.width, draw_rect.height, bg_color)
        screen.blit(room_grad, (draw_rect.x, draw_rect.y))

        border_width = 3 if is_player else (3 if is_hovered else 2)
        pygame.draw.rect(screen, border_color, draw_rect, border_width, border_radius=10)

        if is_player:
            pulse_alpha = int(100 + 80 * math.sin(room.bob_phase * 2))
            pygame.draw.rect(screen, (*border_color, pulse_alpha), draw_rect, 1, border_radius=10)

        self._draw_room_icon(screen, room, draw_rect)

        star_color = settings.GOLD if room.state != "locked" else (50, 50, 50)
        star_y = draw_rect.centery + 14
        self._draw_stars(screen, draw_rect.centerx, star_y, room.difficulty, star_color)

        name_color = settings.LIGHT_GRAY if room.state != "locked" else (50, 50, 50)
        if room.state == "completed":
            name_color = settings.GREEN
        draw_text(screen, t(room.name),
                 (draw_rect.centerx, draw_rect.bottom - int(10 * settings.UI_SCALE)),
                 name_color, 9)

    def _get_room_colors(self, room):
        diff_colors = {
            1: ((25, 35, 50), settings.CYAN),
            2: ((35, 30, 20), settings.ORANGE),
            3: ((45, 20, 20), settings.RED),
            4: ((50, 15, 50), settings.PURPLE),
        }

        if room.type == "hub":
            return (10, 25, 45), settings.CYAN
        elif room.type == "boss":
            return (40, 10, 10), settings.RED
        elif room.type == "challenge":
            return diff_colors.get(room.difficulty, diff_colors[1])[0], diff_colors.get(room.difficulty, diff_colors[1])[1]
        elif room.type == "side":
            return (25, 30, 10), settings.GOLD
        elif room.type == "victory":
            return (20, 15, 40), settings.PURPLE
        else:
            return diff_colors.get(room.difficulty, diff_colors[1])[0], diff_colors.get(room.difficulty, diff_colors[1])[1]

    def _draw_room_icon(self, screen, room, draw_rect):
        cx = draw_rect.centerx
        cy = draw_rect.centery - 6
        icon_size = 14

        if room.state == "completed":
            _draw_checkmark(screen, cx, cy, icon_size * 1.5, settings.GREEN, 3)
        elif room.state == "locked":
            _draw_lock_icon(screen, cx, cy, icon_size, (60, 60, 60), 2)
        elif room.type == "hub":
            _draw_hexagon(screen, cx, cy, icon_size, settings.CYAN, 2)
        elif room.type == "boss":
            _draw_pentagon(screen, cx, cy, icon_size, settings.RED, 2)
        elif room.type == "challenge":
            _draw_triangle(screen, cx, cy, icon_size, settings.ORANGE, 2)
        elif room.type == "side":
            _draw_diamond(screen, cx, cy, icon_size, settings.GOLD, 2)
        elif room.type == "victory":
            _draw_victory_crown(screen, cx, cy, icon_size, settings.PURPLE, 2)
        else:
            _draw_circle_icon(screen, cx, cy, icon_size, settings.WHITE, 2)

    def _draw_room_pulse(self, screen, draw_rect, color, phase):
        pulse_scale = 1 + 0.04 * math.sin(phase * 2)
        w = int(draw_rect.width * pulse_scale)
        h = int(draw_rect.height * pulse_scale)
        ox = (draw_rect.width - w) // 2
        oy = (draw_rect.height - h) // 2

        for i in range(3, 0, -1):
            alpha = int(20 * i)
            glow = _get_glow_surface(w + i * 8, h + i * 8, color, alpha, 10 + i * 2)
            screen.blit(glow, (draw_rect.x + ox - i * 4, draw_rect.y + oy - i * 4))

    def _draw_stars(self, screen, cx, cy, count, color):
        star_size = 5
        spacing = 12
        total_width = count * spacing
        start_x = cx - total_width // 2 + spacing // 2
        star_glow = self._get_star_surface(color)
        for i in range(count):
            x = start_x + i * spacing
            points = []
            for angle_idx in range(10):
                angle = math.radians(angle_idx * 36 - 90)
                r = star_size if angle_idx % 2 == 0 else star_size * 0.4
                px = x + r * math.cos(angle)
                py = cy + r * math.sin(angle)
                points.append((px, py))
            if len(points) >= 3:
                screen.blit(star_glow, (x - star_size * 1.5, cy - star_size * 1.5))
                pygame.draw.polygon(screen, color, points)

    def _draw_mp_avatar(self, screen, info, avatar_size, bob_y, sx, sy):
        ax = info.get("x", 0) - sx
        ay = info.get("y", 0) - sy + settings.MAP_HEADER_H + bob_y
        label = info.get("label", "P2")
        color = info.get("color", settings.GOLD)
        remote_player = info.get("player")

        pygame.draw.circle(screen, (*color, 50),
                           (int(ax), int(ay)), avatar_size // 2 + 4)

        if remote_player is not None:
            sprite = remote_player.get_current_sprite()
            if sprite:
                if remote_player.dir_x < 0:
                    sprite = pygame.transform.flip(sprite, True, False)
                sprite = pygame.transform.scale(sprite, (avatar_size, avatar_size))
                screen.blit(sprite, (int(ax) - avatar_size // 2, int(ay) - avatar_size // 2))
            else:
                pygame.draw.rect(screen, color,
                                 (int(ax) - avatar_size // 2, int(ay) - avatar_size // 2, avatar_size, avatar_size), border_radius=8)
                pygame.draw.rect(screen, settings.WHITE,
                                 (int(ax) - avatar_size // 2, int(ay) - avatar_size // 2, avatar_size, avatar_size), 2, border_radius=8)

        tag_surf = _get_symbol_surface(label, 18, settings.BLACK)
        badge_w = tag_surf.get_width() + 10
        badge_h = tag_surf.get_height() + 6
        badge_x = int(ax) - badge_w // 2
        badge_y = int(ay) - avatar_size // 2 - badge_h - 4
        pygame.draw.rect(screen, color, (badge_x, badge_y, badge_w, badge_h), border_radius=5)
        screen.blit(tag_surf, (badge_x + 5, badge_y + 3))
