import pygame
import random
import math

import settings


class Particle:
    def __init__(self, x, y, vx, vy, color, lifetime, size=2):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime
        self.age = 0
        self.alive = True
        self.size = size

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.age += dt
        if self.age >= self.lifetime:
            self.alive = False

    def draw(self, surface):
        alpha = 1.0 - (self.age / self.lifetime)
        size = max(1, int(self.size * alpha))
        color = tuple(int(c * alpha) for c in self.color)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), size)


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, count, color, speed=80, lifetime=0.4, size=2):
        for _ in range(count):
            angle = random.random() * math.pi * 2
            spd = speed * (0.3 + 0.7 * random.random())
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            lt = lifetime * (0.5 + 0.5 * random.random())
            self.particles.append(Particle(x, y, vx, vy, color, lt, size))

    def emit_burst(self, x, y, color, count=20, speed=120, lifetime=0.5):
        self.emit(x, y, count, color, speed, lifetime)

    def emit_line(self, x1, y1, x2, y2, color, count=10, speed=60, lifetime=0.3):
        for _ in range(count):
            t = random.random()
            px = x1 + (x2 - x1) * t
            py = y1 + (y2 - y1) * t
            angle = math.atan2(y2 - y1, x2 - x1) + random.uniform(-0.5, 0.5)
            spd = speed * (0.5 + 0.5 * random.random())
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            lt = lifetime * (0.5 + 0.5 * random.random())
            self.particles.append(Particle(px, py, vx, vy, color, lt, 2))

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

    def clear(self):
        self.particles.clear()
