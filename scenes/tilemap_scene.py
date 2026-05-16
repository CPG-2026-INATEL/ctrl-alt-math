import pygame

import settings
from scenes.scene import Scene
from tilemap import TileMap, MapGenerator, TILE_STAIRS_UP, TILE_STAIRS_DOWN, TILE_STAIRS_LEFT, TILE_STAIRS_RIGHT



class TilemapScene(Scene):
    # Configuração do mapa - edite estas variáveis1)
    MAP_WIDTH = 40
    MAP_HEIGHT = 30
    HOLE_DENSITY = 0.12
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

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.scene_manager.switch("menu")
            elif event.key == pygame.K_r:
                self._regenerate()

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
        self.tilemap.draw(screen, -self.cam_x, -self.cam_y)
        font = pygame.font.Font(None, 20)
        lines = [
            "WASD: scroll | ESC: menu | R: regenerate",
            f"Map: {self.MAP_WIDTH}x{self.MAP_HEIGHT} | Seed: {self.SEED}",
            f"Holes: {self.HOLE_DENSITY:.0%} | High: {self.HIGH_TERRAIN_RATIO:.0%} ({self.HIGH_TERRAIN_COUNT} areas)",
            f"Stairs/area: {self.STAIRS_PER_AREA}",
        ]
        for i, line in enumerate(lines):
            txt = font.render(line, True, settings.WHITE)
            screen.blit(txt, (10, 10 + i * 20))
