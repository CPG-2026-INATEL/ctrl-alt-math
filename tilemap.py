import pygame


class TileMap:
    def __init__(self, tileset_path, tile_size=32):
        self.tileset = pygame.image.load(tileset_path).convert_alpha()
        self.tile_size = tile_size
        self.tiles_per_row = self.tileset.get_width() // tile_size
        self.tiles_per_col = self.tileset.get_height() // tile_size
        self.map_data = []
        self.map_width = 0
        self.map_height = 0

    def load_from_list(self, data):
        self.map_data = data
        self.map_height = len(data)
        self.map_width = max(len(row) for row in data) if data else 0

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

    def get_world_size(self):
        return self.map_width * self.tile_size, self.map_height * self.tile_size
