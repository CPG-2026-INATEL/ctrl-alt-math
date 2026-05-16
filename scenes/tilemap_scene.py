import pygame

import settings
from scenes.scene import Scene
from tilemap import TileMap, MapGenerator, TILE_STAIRS_UP, TILE_STAIRS_DOWN, TILE_STAIRS_LEFT, TILE_STAIRS_RIGHT



class TilemapScene(Scene):
    # Configuração do mapa - edite estas variáveis1)
    MAP_WIDTH = 40
    MAP_HEIGHT = 30
    HOLE_DENSITY = 0.01
    HIGH_TERRAIN_RATIO = 0.30
    HIGH_TERRAIN_COUNT = 3
    STAIRS_PER_AREA = 2
    SEED = 42

    def __init__(self, game):
        super().__init__(game)
        self.tilemap = TileMap("assets/Tileset/tileset_arranged.png", tile_size=16)

        gen = MapGenerator(
            width=self.MAP_WIDTH,
            height=self.MAP_HEIGHT,
            hole_density=self.HOLE_DENSITY,
            high_terrain_ratio=self.HIGH_TERRAIN_RATIO,
            high_terrain_count=self.HIGH_TERRAIN_COUNT,
            stairs_per_area=self.STAIRS_PER_AREA,
            seed=self.SEED,
        )
        map_data = gen.generate()
        self.tilemap.load_from_list(map_data)

        self.cam_x = 0
        self.cam_y = 0
        self.cam_speed = 200
        self.zoom = 2.0
        self.zoom_min = 0.5
        self.zoom_max = 6.0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.scene_manager.switch("menu")
            elif event.key == pygame.K_r:
                self._regenerate()
        elif event.type == pygame.MOUSEWHEEL:
            old_zoom = self.zoom
            self.zoom *= 1.1 if event.y > 0 else 1 / 1.1
            self.zoom = max(self.zoom_min, min(self.zoom_max, self.zoom))
            mx, my = pygame.mouse.get_pos()
            sw, sh = self.game.screen.get_size()
            world_x = (mx + self.cam_x) / old_zoom
            world_y = (my + self.cam_y) / old_zoom
            self.cam_x = world_x * self.zoom - mx
            self.cam_y = world_y * self.zoom - my

    def _regenerate(self):
        gen = MapGenerator(
            width=self.MAP_WIDTH,
            height=self.MAP_HEIGHT,
            hole_density=self.HOLE_DENSITY,
            high_terrain_ratio=self.HIGH_TERRAIN_RATIO,
            high_terrain_count=self.HIGH_TERRAIN_COUNT,
            stairs_per_area=self.STAIRS_PER_AREA,
            seed=self.SEED,
        )
        map_data = gen.generate()
        self.tilemap.load_from_list(map_data)
        self.cam_x = 0
        self.cam_y = 0

    def update(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.cam_x -= self.cam_speed * dt
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.cam_x += self.cam_speed * dt
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.cam_y -= self.cam_speed * dt
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.cam_y += self.cam_speed * dt

    def draw(self, screen):
        screen.fill(settings.COLOR_BG)
        ts = self.tilemap.tile_size
        scaled = int(ts * self.zoom)
        for row in range(self.tilemap.map_height):
            for col in range(len(self.tilemap.map_data[row])):
                tile_id = self.tilemap.map_data[row][col]
                if tile_id < 0:
                    continue
                sx = (tile_id % self.tilemap.tiles_per_row) * ts
                sy = (tile_id // self.tilemap.tiles_per_row) * ts
                tile_surf = self.tilemap.tileset.subsurface(sx, sy, ts, ts)
                if self.zoom != 1.0:
                    tile_surf = pygame.transform.scale(tile_surf, (scaled, scaled))
                dx = int(-self.cam_x + col * scaled)
                dy = int(-self.cam_y + row * scaled)
                screen.blit(tile_surf, (dx, dy))
        font = pygame.font.Font(None, 20)
        lines = [
            "WASD: scroll | Scroll: zoom | ESC: menu | R: regenerate",
            f"Map: {self.MAP_WIDTH}x{self.MAP_HEIGHT} | Seed: {self.SEED} | Zoom: {self.zoom:.1f}x",
            f"Holes: {self.HOLE_DENSITY:.0%} | High: {self.HIGH_TERRAIN_RATIO:.0%} ({self.HIGH_TERRAIN_COUNT} areas)",
            f"Stairs/area: {self.STAIRS_PER_AREA}",
        ]
        for i, line in enumerate(lines):
            txt = font.render(line, True, settings.WHITE)
            screen.blit(txt, (10, 10 + i * 20))
