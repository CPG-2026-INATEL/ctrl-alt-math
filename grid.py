import pygame
import math
from collections import deque

import settings


class Grid:
    def __init__(self):
        self.cols = settings.GRID_COLS
        self.rows = settings.GRID_ROWS
        self.offset_x = settings.ARENA_OFFSET_X
        self.offset_y = settings.ARENA_OFFSET_Y
        self.width = settings.ARENA_WIDTH
        self.height = settings.ARENA_HEIGHT
        self.cell_w = self.width / self.cols
        self.cell_h = self.height / self.rows
        self.blocked = set()
        self.barrier_cells = set()

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

    def is_blocked(self, col, row):
        return (col, row) in self.blocked

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

    def pathfind(self, start_col, start_row, end_col, end_row):
        if not self.is_valid(end_col, end_row):
            return []
        if self.is_blocked(end_col, end_row):
            return []
        if (start_col, start_row) == (end_col, end_row):
            return [(end_col, end_row)]

        queue = deque()
        queue.append((start_col, start_row, []))
        visited = {(start_col, start_row)}

        while queue:
            col, row, path = queue.popleft()
            for dc, dr in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                nc, nr = col + dc, row + dr
                if not self.is_valid(nc, nr):
                    continue
                if (nc, nr) in visited:
                    continue
                if self.is_blocked(nc, nr) and (nc, nr) != (end_col, end_row):
                    continue
                new_path = path + [(nc, nr)]
                if (nc, nr) == (end_col, end_row):
                    return new_path
                visited.add((nc, nr))
                queue.append((nc, nr, new_path))

        return []

    def get_reachable_cells(self, start_col, start_row, max_steps):
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
                if self.is_blocked(nc, nr):
                    continue
                visited.add((nc, nr))
                queue.append((nc, nr, steps + 1))

        return reachable

    def grid_distance(self, col1, row1, col2, row2):
        return abs(col1 - col2) + abs(row1 - row2)

    def pixel_distance(self, col1, row1, col2, row2):
        x1, y1 = self.to_pixel(col1, row1)
        x2, y2 = self.to_pixel(col2, row2)
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def draw(self, screen, highlight_cells=None, highlight_color=None,
             show_grid=False, grid_color=None):
        if show_grid:
            gc = grid_color or (30, 30, 60, 40)
            for col in range(self.cols + 1):
                x = self.offset_x + col * self.cell_w
                pygame.draw.line(screen, gc, (x, self.offset_y),
                               (x, self.offset_y + self.height))
            for row in range(self.rows + 1):
                y = self.offset_y + row * self.cell_h
                pygame.draw.line(screen, gc, (self.offset_x, y),
                               (self.offset_x + self.width, y))

        if highlight_cells:
            for col, row in highlight_cells:
                rect = self.cell_rect(col, row)
                s = pygame.Surface((rect.width, rect.height))
                s.set_alpha(60)
                s.fill(highlight_color or settings.BLUE)
                screen.blit(s, rect)
                pygame.draw.rect(screen, highlight_color or settings.BLUE, rect, 1)

    def draw_barriers(self, screen):
        for col, row in self.barrier_cells:
            rect = self.cell_rect(col, row)
            s = pygame.Surface((rect.width, rect.height))
            s.set_alpha(50)
            s.fill(settings.CYAN)
            screen.blit(s, rect)
            pygame.draw.rect(screen, settings.CYAN, rect, 1)
            font = pygame.font.Font(None, 14)
            img = font.render("\u03b8\u1d62=\u03b8\u1d63", True, settings.CYAN)
            screen.blit(img, (rect.centerx - img.get_width() // 2,
                            rect.centery - img.get_height() // 2))

    def draw_vector_arrow(self, screen, from_col, from_row, to_col, to_row,
                           color, width=2):
        fx, fy = self.to_pixel(from_col, from_row)
        tx, ty = self.to_pixel(to_col, to_row)
        pygame.draw.line(screen, color, (fx, fy), (tx, ty), width)
        angle = math.atan2(ty - fy, tx - fx)
        arrow_len = 8
        for a in [angle - math.pi / 6, angle + math.pi / 6]:
            ax = tx - arrow_len * math.cos(a)
            ay = ty - arrow_len * math.sin(a)
            pygame.draw.line(screen, color, (tx, ty), (ax, ay), width)

    def draw_triangle(self, screen, col1, row1, col2, row2, col3, row3,
                      color, width=1):
        p1 = self.to_pixel(col1, row1)
        p2 = self.to_pixel(col2, row2)
        p3 = self.to_pixel(col3, row3)
        pygame.draw.line(screen, color, p1, p2, width)
        pygame.draw.line(screen, color, p2, p3, width)
        pygame.draw.line(screen, color, p3, p1, width)
