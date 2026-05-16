import pygame

import settings
from scenes.scene import Scene
from tilemap import TileMap

DEMO_MAP = [
    [0]*20, 
    [0]+[3]*18+[0],
    [0]+[3]+[5]*16+[3]+[0],
    [0]+[3]+[5]*16+[3]+[0],
    [0]+[3]+[5]*16+[3]+[0],
    [0]+[3]+[5]*16+[3]+[0],
    [0]+[3]+[5]*16+[3]+[0],
    [0]+[3]+[5]*16+[3]+[0],
    [0]+[3]+[5]*16+[3]+[0],
    [0]+[3]+[5]*16+[3]+[0],
    [0]+[3]+[5]*16+[3]+[0],
    [0]+[3]+[5]*16+[3]+[0],
    [0]+[3]+[5]*16+[3]+[0],
    [0]+[3]+[5]*16+[3]+[0],
    [0]+[3]+[5]*16+[3]+[0],
    [0]+[3]+[5]*16+[3]+[0],
    [0]+[3]+[5]*16+[3]+[0],
    [0]+[3]*18+[0],
    [0]*20,
]


class TilemapScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.tilemap = TileMap("assets/Tileset/tileset_arranged.png", tile_size=32)
        self.tilemap.load_from_list(DEMO_MAP)
        self.cam_x = 0
        self.cam_y = 0
        self.cam_speed = 200

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.scene_manager.switch("menu")

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
        txt = font.render("WASD: scroll | ESC: menu", True, settings.WHITE)
        screen.blit(txt, (10, 10))
