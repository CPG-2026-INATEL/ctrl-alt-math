import pygame
import random


# ============================================================
# Tile IDs
# Edite aqui para mapear aos tiles do seu tileset (0-63).
# Cada ID corresponde a um tile no tileset 8x8 (256x256, 32x32 cada).
# ============================================================
ROW_SIZE = 16

TILE_HOLE = -1       # buraco (sem tile)
TILE_LOW = 0       # terreno baixo
TILE_HIGH = 16        # terreno alto
TILE_HIGH_EDGE = 45+16   # borda inferior do terreno alto (profundidade)
TILE_STAIRS_UP = 11+ROW_SIZE  # escada subindo (norte)
TILE_STAIRS_DOWN = 11 # escada descendo (sul)
TILE_STAIRS_LEFT = 9+16 # escada esquerda (oeste)
TILE_STAIRS_RIGHT = 8 +16# escada direita (leste)

OBSTACLE_TILE_IDS = [
    64
]

WALKABLE_TILES = {TILE_LOW, TILE_HIGH, TILE_HIGH_EDGE,
                   TILE_STAIRS_UP, TILE_STAIRS_DOWN, TILE_STAIRS_LEFT, TILE_STAIRS_RIGHT}




class TileMap:
    def __init__(self, tileset_path, tile_size=32):
        self.tileset = pygame.image.load(tileset_path).convert_alpha()
        self.tile_size = tile_size
        self.tiles_per_row = self.tileset.get_width() // tile_size
        self.tiles_per_col = self.tileset.get_height() // tile_size
        self.map_data = []
        self.obstacle_data = []
        self.obstacle_tileset = None
        self.map_width = 0
        self.map_height = 0

    def load_from_list(self, data):
        self.map_data = data
        self.map_height = len(data)
        self.map_width = max(len(row) for row in data) if data else 0

    def load_obstacles(self, obstacle_data, tileset_path=None):
        self.obstacle_data = obstacle_data
        if tileset_path:
            self.obstacle_tileset = pygame.image.load(tileset_path).convert_alpha()

    def load_from_file(self, path):
        with open(path) as f:
            self.map_data = [
                [int(v) for v in line.strip().split(",")]
                for line in f if line.strip()
            ]
        self.map_height = len(self.map_data)
        self.map_width = max(len(row) for row in self.map_data) if self.map_data else 0

    def get_tile(self, col, row):
        if row < 0 or row >= self.map_height:
            return None
        if col < 0 or col >= len(self.map_data[row]):
            return None
        tile_id = self.map_data[row][col]
        if tile_id < 0:
            return None
        sx = (tile_id % self.tiles_per_row) * self.tile_size
        sy = (tile_id // self.tiles_per_row) * self.tile_size
        return self.tileset.subsurface(sx, sy, self.tile_size, self.tile_size)

    def draw(self, screen, offset_x=0, offset_y=0):
        for row in range(self.map_height):
            for col in range(len(self.map_data[row])):
                tile_id = self.map_data[row][col]
                if tile_id < 0:
                    continue
                sx = (tile_id % self.tiles_per_row) * self.tile_size
                sy = (tile_id // self.tiles_per_row) * self.tile_size
                dx = offset_x + col * self.tile_size
                dy = offset_y + row * self.tile_size
                screen.blit(self.tileset, (dx, dy), (sx, sy, self.tile_size, self.tile_size))

    def draw_obstacles(self, screen, offset_x=0, offset_y=0):
        if not self.obstacle_data or not self.obstacle_tileset:
            return
        obs_tiles_per_row = self.obstacle_tileset.get_width() // self.tile_size
        for row in range(self.map_height):
            for col in range(len(self.obstacle_data[row])):
                obs_id = self.obstacle_data[row][col]
                if obs_id is None:
                    continue
                sx = (obs_id % obs_tiles_per_row) * self.tile_size
                sy = (obs_id // obs_tiles_per_row) * self.tile_size
                dx = offset_x + col * self.tile_size
                dy = offset_y + row * self.tile_size
                screen.blit(self.obstacle_tileset, (dx, dy), (sx, sy, self.tile_size, self.tile_size))

    def get_world_size(self):
        return self.map_width * self.tile_size, self.map_height * self.tile_size


class MapGenerator:
    DIRS = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]

    def __init__(
        self,
        width,
        height,
        hole_density=0.12,
        high_terrain_ratio=0.30,
        high_terrain_count=3,
        stairs_per_area=2,
        obstacle_density=0.05,
        seed=42,
    ):
        self.width = width
        self.height = height
        self.hole_density = hole_density
        self.high_terrain_ratio = high_terrain_ratio
        self.high_terrain_count = high_terrain_count
        self.stairs_per_area = stairs_per_area
        self.obstacle_density = obstacle_density
        self.seed = seed

    MIN_WALKABLE_RATIO = 0.5

    def generate(self):
        WALKABLE = {TILE_LOW, TILE_HIGH, TILE_STAIRS_UP, TILE_STAIRS_DOWN, TILE_STAIRS_LEFT, TILE_STAIRS_RIGHT}
        total = self.width * self.height
        min_walkable = int(total * self.MIN_WALKABLE_RATIO)
        for attempt in range(20):
            random.seed(self.seed + attempt)
            grid = [[TILE_LOW] * self.width for _ in range(self.height)]

            self._scatter_holes(grid)
            self._grow_high_terrain_islands(grid)
            self._smooth(grid, iterations=3)
            self._enforce_low_connectivity(grid)
            self._prune_small_high_areas(grid)
            self._place_stairs(grid)
            self._enforce_full_connectivity(grid)
            self._apply_high_edge(grid)
            self._fix_stair_edges(grid)
            obstacles = self._place_obstacles(grid)

            walkable = sum(1 for r in grid for c in r if c in WALKABLE)
            if walkable >= min_walkable:
                return grid, obstacles
        return grid, obstacles

    def _apply_high_edge(self, grid):
        ALL_STAIRS = {TILE_STAIRS_UP, TILE_STAIRS_DOWN, TILE_STAIRS_LEFT, TILE_STAIRS_RIGHT}
        BELOW = {TILE_LOW, TILE_HOLE, TILE_STAIRS_DOWN, TILE_STAIRS_LEFT, TILE_STAIRS_RIGHT}
        changes = []
        for r in range(self.height - 1):
            for c in range(self.width):
                if grid[r][c] == TILE_HIGH and grid[r + 1][c] in BELOW:
                    changes.append((r, c))
        for r, c in changes:
            grid[r][c] = TILE_HIGH_EDGE

    def _fix_stair_edges(self, grid):
        ALL_STAIRS = {TILE_STAIRS_UP, TILE_STAIRS_DOWN, TILE_STAIRS_LEFT, TILE_STAIRS_RIGHT}
        STAIR_DIR = {
            TILE_STAIRS_UP: (-1, 0),
            TILE_STAIRS_DOWN: (1, 0),
            TILE_STAIRS_LEFT: (0, -1),
            TILE_STAIRS_RIGHT: (0, 1),
        }
        changes = set()
        for r in range(self.height):
            for c in range(self.width):
                if grid[r][c] in STAIR_DIR:
                    dr, dc = STAIR_DIR[grid[r][c]]
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.height and 0 <= nc < self.width:
                        if grid[nr][nc] == TILE_HIGH_EDGE:
                            changes.add((nr, nc))
        for r in range(self.height):
            for c in range(self.width):
                if grid[r][c] == TILE_HIGH_EDGE:
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.height and 0 <= nc < self.width:
                            if grid[nr][nc] in ALL_STAIRS:
                                changes.add((r, c))
                                break
        for r, c in changes:
            grid[r][c] = TILE_HIGH

    def _scatter_holes(self, grid):
        total = self.width * self.height
        target = int(total * self.hole_density)
        positions = [(r, c) for r in range(self.height) for c in range(self.width)]
        random.shuffle(positions)
        for i in range(min(target, len(positions))):
            r, c = positions[i]
            grid[r][c] = TILE_HOLE

    def _grow_high_terrain_islands(self, grid):
        total_cells = self.width * self.height
        high_count = int(total_cells * self.high_terrain_ratio)
        per_island = max(5, high_count // self.high_terrain_count)

        grown = 0
        attempts = 0
        max_attempts = self.high_terrain_count * 20

        while grown < self.high_terrain_count and attempts < max_attempts:
            attempts += 1
            seed_r = random.randint(1, self.height - 2)
            seed_c = random.randint(1, self.width - 2)
            if grid[seed_r][seed_c] != TILE_LOW:
                continue

            frontier = [(seed_r, seed_c)]
            grid[seed_r][seed_c] = TILE_HIGH
            island_size = 1
            grow_prob = 0.85

            while frontier and island_size < per_island:
                new_frontier = []
                for r, c in frontier:
                    if island_size >= per_island:
                        break
                    random.shuffle(self.DIRS)
                    for dr, dc in self.DIRS:
                        if island_size >= per_island:
                            break
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.height and 0 <= nc < self.width:
                            if grid[nr][nc] == TILE_LOW:
                                if random.random() < grow_prob:
                                    grid[nr][nc] = TILE_HIGH
                                    new_frontier.append((nr, nc))
                                    island_size += 1
                frontier = new_frontier
                grow_prob *= 0.92

            if island_size >= 5:
                grown += 1

    def _smooth(self, grid, iterations=3):
        for _ in range(iterations):
            new_grid = [row[:] for row in grid]
            for r in range(1, self.height - 1):
                for c in range(1, self.width - 1):
                    if grid[r][c] == TILE_HOLE:
                        continue
                    counts = {TILE_LOW: 0, TILE_HIGH: 0}
                    for dr, dc in self.DIRS:
                        neighbor = grid[r + dr][c + dc]
                        if neighbor in counts:
                            counts[neighbor] += 1
                    majority = max(counts, key=counts.get)
                    if counts[majority] >= 5:
                        new_grid[r][c] = majority
            grid[:] = new_grid

    def _enforce_low_connectivity(self, grid):
        start = None
        for r in range(self.height):
            for c in range(self.width):
                if grid[r][c] == TILE_LOW:
                    start = (r, c)
                    break
            if start:
                break

        if not start:
            return

        visited = set()
        queue = [start]
        visited.add(start)
        while queue:
            r, c = queue.pop(0)
            for dr, dc in self.DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.height and 0 <= nc < self.width:
                    if (nr, nc) not in visited and grid[nr][nc] == TILE_LOW:
                        visited.add((nr, nc))
                        queue.append((nr, nc))

        for r in range(self.height):
            for c in range(self.width):
                if grid[r][c] == TILE_LOW and (r, c) not in visited:
                    grid[r][c] = TILE_HOLE

    def _enforce_full_connectivity(self, grid):
        WALKABLE = {TILE_LOW, TILE_HIGH, TILE_STAIRS_UP, TILE_STAIRS_DOWN, TILE_STAIRS_LEFT, TILE_STAIRS_RIGHT}
        CARDINAL = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        visited_all = set()
        components = []
        for r in range(self.height):
            for c in range(self.width):
                if grid[r][c] in WALKABLE and (r, c) not in visited_all:
                    component = set()
                    queue = [(r, c)]
                    component.add((r, c))
                    visited_all.add((r, c))
                    while queue:
                        cr, cc = queue.pop(0)
                        for dr, dc in CARDINAL:
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < self.height and 0 <= nc < self.width:
                                if (nr, nc) not in component and grid[nr][nc] in WALKABLE:
                                    component.add((nr, nc))
                                    visited_all.add((nr, nc))
                                    queue.append((nr, nc))
                    components.append(component)
        if not components:
            return
        largest = max(components, key=len)
        for r in range(self.height):
            for c in range(self.width):
                if grid[r][c] in WALKABLE and (r, c) not in largest:
                    grid[r][c] = TILE_HOLE

    def _prune_small_high_areas(self, grid):
        visited = set()
        areas = []
        for r in range(self.height):
            for c in range(self.width):
                if grid[r][c] == TILE_HIGH and (r, c) not in visited:
                    area = []
                    queue = [(r, c)]
                    visited.add((r, c))
                    while queue:
                        cr, cc = queue.pop(0)
                        area.append((cr, cc))
                        for dr, dc in self.DIRS:
                            nr, nc = cr + dr, c + dc
                            if 0 <= nr < self.height and 0 <= nc < self.width:
                                if (nr, nc) not in visited and grid[nr][nc] == TILE_HIGH:
                                    visited.add((nr, nc))
                                    queue.append((nr, nc))
                    areas.append(area)

        for area in areas:
            if len(area) < 5:
                for r, c in area:
                    grid[r][c] = TILE_LOW

    def _place_stairs(self, grid):
        CARDINAL = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        CARDINAL_TILES = {
            (-1, 0): TILE_STAIRS_UP,
            (1, 0): TILE_STAIRS_DOWN,
            (0, -1): TILE_STAIRS_LEFT,
            (0, 1): TILE_STAIRS_RIGHT,
        }

        visited = set()
        for r in range(self.height):
            for c in range(self.width):
                if grid[r][c] == TILE_HIGH and (r, c) not in visited:
                    area = []
                    queue = [(r, c)]
                    visited.add((r, c))
                    while queue:
                        cr, cc = queue.pop(0)
                        area.append((cr, cc))
                        for dr, dc in self.DIRS:
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < self.height and 0 <= nc < self.width:
                                if (nr, nc) not in visited and grid[nr][nc] == TILE_HIGH:
                                    visited.add((nr, nc))
                                    queue.append((nr, nc))

                    border_candidates = []
                    for ar, ac in area:
                        for dr, dc in CARDINAL:
                            nr, nc = ar + dr, ac + dc
                            if 0 <= nr < self.height and 0 <= nc < self.width:
                                if grid[nr][nc] == TILE_LOW:
                                    stair_dir = (-dr, -dc)
                                    opposite_r = nr - stair_dir[0]
                                    opposite_c = nc - stair_dir[1]
                                    if 0 <= opposite_r < self.height and 0 <= opposite_c < self.width:
                                        if grid[opposite_r][opposite_c] == TILE_LOW:
                                            border_candidates.append((nr, nc, stair_dir))

                    random.shuffle(border_candidates)
                    placed = 0
                    used_positions = set()
                    for lr, lc, stair_dir in border_candidates:
                        if placed >= self.stairs_per_area:
                            break
                        if (lr, lc) in used_positions:
                            continue
                        if grid[lr][lc] == TILE_LOW:
                            grid[lr][lc] = CARDINAL_TILES[stair_dir]
                            used_positions.add((lr, lc))
                            placed += 1

                    if placed == 0 and border_candidates:
                        lr, lc, stair_dir = border_candidates[0]
                        grid[lr][lc] = CARDINAL_TILES[stair_dir]

    def _place_obstacles(self, grid):
        obstacles = [[None] * self.width for _ in range(self.height)]
        candidates = []
        for r in range(self.height):
            for c in range(self.width):
                if grid[r][c] in WALKABLE_TILES:
                    candidates.append((r, c))
        random.shuffle(candidates)
        count = int(len(candidates) * self.obstacle_density)
        for i in range(count):
            r, c = candidates[i]
            obstacles[r][c] = random.choice(OBSTACLE_TILE_IDS)
        return obstacles
