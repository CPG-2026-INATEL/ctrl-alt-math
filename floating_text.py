import pygame

import settings


class FloatingText:
    def __init__(self, x, y, text, color, size=16, lifetime=0.8):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.age = 0
        self.alive = True
        self.vy = -40

    def update(self, dt):
        self.age += dt
        self.y += self.vy * dt
        self.vy *= 0.95
        if self.age >= self.lifetime:
            self.alive = False

    def draw(self, screen):
        alpha = 1.0 - (self.age / self.lifetime)
        font = pygame.font.Font(None, self.size)
        img = font.render(self.text, True, self.color)
        img.set_alpha(int(255 * alpha))
        rect = img.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(img, rect)


class FloatingTextSystem:
    def __init__(self):
        self.texts = []

    def add(self, x, y, text, color, size=16, lifetime=0.8):
        self.texts.append(FloatingText(x, y, text, color, size, lifetime))

    def add_damage(self, x, y, amount):
        self.add(x, y - 10, f"-{amount}", settings.RED, 14, 0.7)

    def add_heal(self, x, y, amount):
        self.add(x, y - 10, f"+{amount}", settings.GREEN, 14, 0.7)

    def add_info(self, x, y, text, color=settings.CYAN):
        self.add(x, y - 10, text, color, 12, 0.6)

    def update(self, dt):
        for t in self.texts:
            t.update(dt)
        self.texts = [t for t in self.texts if t.alive]

    def draw(self, screen):
        for t in self.texts:
            t.draw(screen)

    def clear(self):
        self.texts.clear()
