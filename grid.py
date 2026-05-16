import pygame
import math
from collections import deque

import settings


class Grid:
    def __init__(self, cols=None, rows=None):
        self.cols = cols if cols is not None else settings.GRID_COLS
        self.rows = rows if rows is not None else settings.GRID_ROWS
        self.offset_x = settings.ARENA_OFFSET_X
        self.offset_y = settings.ARENA_OFFSET_Y
        
        # Use integer cell sizes derived from the base arena dimensions
        self.cell_w = int(settings.ARENA_WIDTH / settings.GRID_COLS)
        self.cell_h = int(settings.ARENA_HEIGHT / settings.GRID_ROWS)

        self.width = self.cell_w * self.cols
        self.height = self.cell_h * self.rows

        
        self.blocked = set()
        self.barrier_cells = set()
        self.tile_types = {}
        self.danger_tiles = set()
        self.danger_locked = False

    def to_grid(self, x, y):
        col = int((x - self.offset_x) / self.cell_w)
        row = int((y - self.offset_y) / self.cell_h)
        col = max(0, min(self.cols - 1, col))
        row = max(0, min(self.rows - 1, row))
        return col, row

    def to_pixel(self, col, row):
        cx = self.offset_x + col * self.cell_w + self.cell_w / 2
        cy = self.offset_y + row * self.cell_h + self.cell_h / 2
        return cx, cy

    def cell_rect(self, col, row):
        return pygame.Rect(
            self.offset_x + col * self.cell_w,
            self.offset_y + row * self.cell_h,
            self.cell_w, self.cell_h
        )

    def is_valid(self, col, row):
        return 0 <= col < self.cols and 0 <= row < self.rows

    def is_blocked(self, col, row, include_barriers=False, extra_blocked=None):
        if (col, row) in self.blocked:
            return True
        if include_barriers and (col, row) in self.barrier_cells:
            return True
        if extra_blocked and (col, row) in extra_blocked:
            return True
        return False

    def is_barrier(self, col, row):
        return (col, row) in self.barrier_cells

    def mark_blocked(self, col, row):
        if self.is_valid(col, row):
            self.blocked.add((col, row))

    def mark_barrier(self, col, row, add=True):
        if add:
            if self.is_valid(col, row):
                self.barrier_cells.add((col, row))
        else:
            self.barrier_cells.discard((col, row))

    def clear_barriers(self):
        self.barrier_cells.clear()

    def load_obstacles(self, obstacles):
        self.blocked.clear()
        for obs in obstacles:
            col, row = obs["col"], obs["row"]
            w, h = obs.get("w", 1), obs.get("h", 1)
            for dc in range(w):
                for dr in range(h):
                    c, r = col + dc, row + dr
                    if self.is_valid(c, r):
                        self.blocked.add((c, r))

    def obstacle_rects(self, obstacles):
        rects = []
        for obs in obstacles:
            col, row = obs["col"], obs["row"]
            w, h = obs.get("w", 1), obs.get("h", 1)
            r = self.cell_rect(col, row)
            pw = self.cell_w * w
            ph = self.cell_h * h
            rects.append(pygame.Rect(r.x, r.y, pw, ph))
        return rects

    def get_cells_in_radius(self, center_col, center_row, radius):
        cells = []
        for dc in range(-radius, radius + 1):
            for dr in range(-radius, radius + 1):
                col = center_col + dc
                row = center_row + dr
                if self.is_valid(col, row):
                    dist = math.sqrt(dc * dc + dr * dr)
                    if dist <= radius:
                        cells.append((col, row))
        return cells

    def get_cells_in_range(self, center_col, center_row, max_range):
        cells = []
        for dc in range(-max_range, max_range + 1):
            for dr in range(-max_range, max_range + 1):
                col = center_col + dc
                row = center_row + dr
                if self.is_valid(col, row):
                    dist = abs(dc) + abs(dr)
                    if dist <= max_range:
                        cells.append((col, row))
        return cells

    def get_cells_in_cone(self, origin_col, origin_row, direction, cone_range):
        cells = []
        dx, dy = direction
        for r in range(1, cone_range + 1):
            col = origin_col + dx * r
            row = origin_row + dy * r
            if self.is_valid(col, row) and not self.is_blocked(col, row):
                cells.append((col, row))
                if dx != 0:
                    for side in [-1, 1]:
                        scol = col
                        srow = row + side
                        if self.is_valid(scol, srow) and not self.is_blocked(scol, srow):
                            cells.append((scol, srow))
                if dy != 0:
                    for side in [-1, 1]:
                        scol = col + side
                        srow = row
                        if self.is_valid(scol, srow) and not self.is_blocked(scol, srow):
                            cells.append((scol, srow))
        return cells

    def pathfind(
        self,
        start_col,
        start_row,
        end_col,
        end_row,
        allow_diagonal=True,
        include_barriers=False,
        extra_blocked=None,
    ):
        if not self.is_valid(end_col, end_row):
            return []
        if self.is_blocked(end_col, end_row, include_barriers, extra_blocked):
            return []
        if (start_col, start_row) == (end_col, end_row):
            return [(end_col, end_row)]

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        if allow_diagonal:
            directions += [(-1, -1), (-1, 1), (1, -1), (1, 1)]

        queue = deque()
        queue.append((start_col, start_row, []))
        visited = {(start_col, start_row)}

        while queue:
            col, row, path = queue.popleft()
            for dc, dr in directions:
                nc, nr = col + dc, row + dr
                if not self.is_valid(nc, nr):
                    continue
                if (nc, nr) in visited:
                    continue
                if self.is_blocked(nc, nr, include_barriers, extra_blocked) and (nc, nr) != (end_col, end_row):
                    continue
                if self.is_level_change(col, row, nc, nr):
                    continue
                new_path = path + [(nc, nr)]
                if (nc, nr) == (end_col, end_row):
                    return new_path
                visited.add((nc, nr))
                queue.append((nc, nr, new_path))

        return []

    def get_reachable_cells(self, start_col, start_row, max_steps, include_barriers=False, extra_blocked=None):
        reachable = []
        queue = deque()
        queue.append((start_col, start_row, 0))
        visited = {(start_col, start_row)}

        while queue:
            col, row, steps = queue.popleft()
            if steps > 0:
                reachable.append((col, row))
            if steps >= max_steps:
                continue
            for dc, dr in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nc, nr = col + dc, row + dr
                if not self.is_valid(nc, nr):
                    continue
                if (nc, nr) in visited:
                    continue
                if self.is_blocked(nc, nr, include_barriers, extra_blocked):
                    continue
                if self.is_level_change(col, row, nc, nr):
                    continue
                visited.add((nc, nr))
                queue.append((nc, nr, steps + 1))

        return reachable

    def grid_distance(self, col1, row1, col2, row2):
        return abs(col1 - col2) + abs(row1 - row2)

    def is_level_change(self, from_col, from_row, to_col, to_row):
        from_tile = self.tile_types.get((from_col, from_row))
        to_tile = self.tile_types.get((to_col, to_row))
        if from_tile is None or to_tile is None:
            return False
        LOW_TILES = {0}
        HIGH_TILES = {16, 61}
        STAIR_TILES = {27, 11, 25, 24}
        from_high = from_tile in HIGH_TILES
        to_high = to_tile in HIGH_TILES
        from_stairs = from_tile in STAIR_TILES
        to_stairs = to_tile in STAIR_TILES
        if from_high != to_high and not from_stairs and not to_stairs:
            return True
        return False

    def pixel_distance(self, col1, row1, col2, row2):
        x1, y1 = self.to_pixel(col1, row1)
        x2, y2 = self.to_pixel(col2, row2)
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def set_danger_tiles(self, intents, player_skills=None):
        self.danger_tiles.clear()
        for intent in intents:
            if intent is None or intent.enemy.dead:
                continue
            tiles, is_fake = intent.get_display_tiles(player_skills)
            for tile in tiles:
                if self.is_valid(tile[0], tile[1]):
                    self.danger_tiles.add((tile[0], tile[1], intent.telegraph_type, is_fake, intent.lock_mode))

    def clear_danger_tiles(self):
        self.danger_tiles.clear()
        self.danger_locked = False

    def lock_danger_indicators(self, intents):
        self.danger_locked = True
        self.danger_tiles.clear()
        for intent in intents:
            if intent is None or intent.enemy.dead:
                continue
            intent.lock()
            for tile in intent.danger_tiles:
                if self.is_valid(tile[0], tile[1]):
                    self.danger_tiles.add((tile[0], tile[1], intent.telegraph_type, intent.is_fake, intent.lock_mode))

    def draw_danger_indicators(self, screen, pulse_timer=0, offset=(0, 0)):
        ox, oy = offset
        pulse_alpha = 0.5 + 0.3 * math.sin(pulse_timer * 5)
        for entry in self.danger_tiles:
            if len(entry) == 5:
                col, row, telegraph_type, is_fake, lock_mode = entry
            else:
                col, row = entry[0], entry[1]
                telegraph_type = "line"
                is_fake = False
                lock_mode = "fixed"

            rect = self.cell_rect(col, row)
            rect.x += ox
            rect.y += oy

            if self.danger_locked:
                base_color = (255, 50, 50)
                border_color = (255, 80, 80)
                base_alpha = int(100 * pulse_alpha + 60)
            elif is_fake:
                base_color = (255, 140, 30)
                border_color = (255, 160, 60)
                base_alpha = int(50 * pulse_alpha + 30)
            else:
                base_color = (255, 200, 50)
                border_color = (255, 220, 80)
                base_alpha = int(70 * pulse_alpha + 40)

            s = pygame.Surface((int(rect.width), int(rect.height)))
            s.set_alpha(base_alpha)
            s.fill(base_color)
            screen.blit(s, rect)

            pygame.draw.rect(screen, border_color, rect, 2)

            if telegraph_type == "area":
                inner = rect.inflate(-4, -4)
                pygame.draw.rect(screen, border_color, inner, 1)
            elif telegraph_type == "cross":
                cx, cy = rect.centerx, rect.centery
                sz = min(rect.width, rect.height) // 4
                pygame.draw.line(screen, border_color, (cx - sz, cy), (cx + sz, cy), 2)
                pygame.draw.line(screen, border_color, (cx, cy - sz), (cx, cy + sz), 2)
            elif telegraph_type == "line":
                cx, cy = rect.centerx, rect.centery
                sz = min(rect.width, rect.height) // 3
                pygame.draw.line(screen, border_color, (cx, cy - sz), (cx, cy + sz), 2)

    def draw_intent_arrows(self, screen, intents, player_skills=None, offset=(0, 0)):
        ox, oy = offset
        for intent in intents:
            if intent is None or intent.enemy.dead:
                continue
            if not intent.danger_tiles:
                continue
            origin = intent.attack_origin
            if origin is None:
                origin = (intent.enemy.col, intent.enemy.row)
            fx, fy = self.to_pixel(origin[0], origin[1])
            fx += ox
            fy += oy

            target_list = list(intent.danger_tiles)
            if not target_list:
                continue
            mid_tile = target_list[len(target_list) // 2]
            tx, ty = self.to_pixel(mid_tile[0], mid_tile[1])
            tx += ox
            ty += oy

            if self.danger_locked:
                arrow_color = (255, 80, 80)
            elif intent.is_fake:
                arrow_color = (255, 140, 30)
            else:
                arrow_color = (255, 200, 50)

            pygame.draw.line(screen, arrow_color, (int(fx), int(fy)), (int(tx), int(ty)), 2)

            angle = math.atan2(ty - fy, tx - fx)
            arrow_len = 10
            for a in [angle - math.pi / 5, angle + math.pi / 5]:
                ax = tx - arrow_len * math.cos(a)
                ay = ty - arrow_len * math.sin(a)
                pygame.draw.line(screen, arrow_color, (int(tx), int(ty)), (int(ax), int(ay)), 2)

        if player_skills and "derivada" in player_skills:
            for intent in intents:
                if intent is None or intent.enemy.dead or not intent.move_target:
                    continue
                if intent.move_target == (intent.enemy.col, intent.enemy.row):
                    continue
                sx, sy = self.to_pixel(intent.enemy.col, intent.enemy.row)
                ex, ey = self.to_pixel(intent.move_target[0], intent.move_target[1])
                sx += ox
                sy += oy
                ex += ox
                ey += oy
                ghost_color = (100, 255, 100, 80)
                s = pygame.Surface((16, 16), pygame.SRCALPHA)
                s.fill(ghost_color)
                screen.blit(s, (int(ex) - 8, int(ey) - 8))

    def draw(self, screen, highlight_cells=None, highlight_color=None,
             show_grid=False, grid_color=None, highlight_outline=False, offset=(0, 0)):
        ox, oy = offset
        if show_grid:
            gc = grid_color or (30, 30, 60, 40)
            for col in range(self.cols + 1):
                x = self.offset_x + col * self.cell_w + ox
                pygame.draw.line(screen, gc, (x, self.offset_y + oy),
                               (x, self.offset_y + self.height + oy))
            for row in range(self.rows + 1):
                y = self.offset_y + row * self.cell_h + oy
                pygame.draw.line(screen, gc, (self.offset_x + ox, y),
                               (self.offset_x + self.width + ox, y))

        if highlight_cells:
            for col, row in highlight_cells:
                rect = self.cell_rect(col, row)
                rect.x += ox
                rect.y += oy
                s = pygame.Surface((rect.width, rect.height))
                s.set_alpha(60)
                s.fill(highlight_color or settings.BLUE)
                screen.blit(s, rect)
                if highlight_outline:
                    pygame.draw.rect(screen, highlight_color or settings.BLUE, rect, 1)

    def draw_barriers(self, screen, offset=(0, 0)):
        ox, oy = offset
        for col, row in self.barrier_cells:
            rect = self.cell_rect(col, row)
            rect.x += ox
            rect.y += oy
            s = pygame.Surface((rect.width, rect.height))
            s.set_alpha(50)
            s.fill(settings.CYAN)
            screen.blit(s, rect)
            pygame.draw.rect(screen, settings.CYAN, rect, 1)
            font = pygame.font.Font(None, 14)
            img = font.render("theta_i=theta_r", True, settings.CYAN)
            screen.blit(img, (rect.centerx - img.get_width() // 2,
                            rect.centery - img.get_height() // 2))

    def draw_vector_arrow(self, screen, from_col, from_row, to_col, to_row,
                           color, width=2, offset=(0, 0)):
        ox, oy = offset
        fx, fy = self.to_pixel(from_col, from_row)
        tx, ty = self.to_pixel(to_col, to_row)
        fx += ox
        fy += oy
        tx += ox
        ty += oy
        pygame.draw.line(screen, color, (fx, fy), (tx, ty), width)
        angle = math.atan2(ty - fy, tx - fx)
        arrow_len = 8
        for a in [angle - math.pi / 6, angle + math.pi / 6]:
            ax = tx - arrow_len * math.cos(a)
            ay = ty - arrow_len * math.sin(a)
            pygame.draw.line(screen, color, (tx, ty), (ax, ay), width)

    def draw_triangle(self, screen, col1, row1, col2, row2, col3, row3,
                      color, width=1, offset=(0, 0)):
        ox, oy = offset
        p1 = self.to_pixel(col1, row1)
        p2 = self.to_pixel(col2, row2)
        p3 = self.to_pixel(col3, row3)
        p1 = (p1[0] + ox, p1[1] + oy)
        p2 = (p2[0] + ox, p2[1] + oy)
        p3 = (p3[0] + ox, p3[1] + oy)
        pygame.draw.line(screen, color, p1, p2, width)
        pygame.draw.line(screen, color, p2, p3, width)
        pygame.draw.line(screen, color, p3, p1, width)
