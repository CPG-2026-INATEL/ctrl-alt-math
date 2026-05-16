import pygame

import settings
from utils import distance


class Projectile:
    def __init__(self, x, y, vx, vy, damage, owner="enemy", color=None, size=4):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.owner = owner
        self.color = color or settings.COLOR_PROJECTILE
        self.size = size
        self.alive = True
        self.lifetime = 3.0
        self.age = 0
        self.trail = []
        self.trail_interval = 0.02
        self.trail_timer = 0

    def update(self, dt):
        self.trail_timer += dt
        if self.trail_timer >= self.trail_interval:
            self.trail_timer = 0
            self.trail.append((self.x, self.y, 0.15))
        self.trail = [(tx, ty, t - dt) for tx, ty, t in self.trail if t > 0]

        self.x += self.vx * dt
        self.y += self.vy * dt
        self.age += dt
        if self.age >= self.lifetime:
            self.alive = False
        if (self.x < settings.ARENA_OFFSET_X or
            self.x > settings.ARENA_OFFSET_X + settings.ARENA_WIDTH or
            self.y < settings.ARENA_OFFSET_Y or
            self.y > settings.ARENA_OFFSET_Y + settings.ARENA_HEIGHT):
            self.alive = False

    def draw(self, screen):
        for tx, ty, t in self.trail:
            alpha = int((t / 0.15) * 120)
            trail_size = max(1, int(self.size * (t / 0.15)))
            s = pygame.Surface((trail_size * 2, trail_size * 2))
            s.set_alpha(alpha)
            s.fill(self.color)
            screen.blit(s, (tx - trail_size, ty - trail_size))

        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)
        pygame.draw.circle(screen, settings.WHITE, (int(self.x), int(self.y)), self.size - 1)

    def reflect(self):
        self.vx = -self.vx
        self.vy = -self.vy
        self.owner = "player" if self.owner == "enemy" else "enemy"
        self.color = settings.CYAN
