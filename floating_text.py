import pygame
import math

import settings


class FloatingText:
    BOUNCE_SPEED = 8.0
    BOUNCE_DAMPING = 0.6
    MIN_BOUNCE_VEL = 5.0

    def __init__(self, x, y, text, color, size=16, lifetime=0.8, bounce=True, shadow=True):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.base_color = color
        self.size = size
        self.lifetime = lifetime
        self.age = 0
        self.alive = True
        self.vy = -60 if bounce else -40
        self.vx = 0
        self.bounce = bounce
        self.shadow = shadow
        self.scale = 0.3 if bounce else 1.0
        self.target_scale = 1.0
        self.hit_ground = False

    def update(self, dt):
        self.age += dt
        self.y += self.vy * dt
        self.x += self.vx * dt
        self.vy += (120 if self.bounce else 60) * dt

        if self.bounce and not self.hit_ground:
            self.scale = min(self.target_scale, self.scale + dt * 12)
        else:
            self.scale = max(0.8, self.scale - dt * 0.5)

        if self.bounce and self.vy > 0 and self.age > 0.05:
            self.hit_ground = True
            self.vy *= -self.BOUNCE_DAMPING
            if abs(self.vy) < self.MIN_BOUNCE_VEL:
                self.vy = 0

        self.vx *= 0.95

        if self.age >= self.lifetime:
            self.alive = False

    def draw(self, screen):
        alpha = 1.0 - (self.age / self.lifetime) ** 0.5
        alpha = max(0, min(1.0, alpha))
        actual_size = max(8, int(self.size * self.scale))
        font = pygame.font.Font(None, actual_size)

        if self.shadow:
            shadow_img = font.render(self.text, True, (0, 0, 0))
            shadow_img.set_alpha(int(alpha * 120))
            shadow_rect = shadow_img.get_rect(center=(int(self.x) + 1, int(self.y) + 1))
            screen.blit(shadow_img, shadow_rect)

        img = font.render(self.text, True, self.color)
        img.set_alpha(int(alpha * 255))
        rect = img.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(img, rect)


class FloatingTextSystem:
    def __init__(self):
        self.texts = []

    def add(self, x, y, text, color, size=16, lifetime=0.8, bounce=True, shadow=True):
        self.texts.append(FloatingText(x, y, text, color, size, lifetime, bounce, shadow))

    def add_damage(self, x, y, amount, crit=False):
        if crit:
            self.add(x, y - 15, f"-{amount}", settings.GOLD, 24, 1.2, bounce=True, shadow=True)
            self.add(x + 15, y - 25, "CRIT!", settings.GOLD, 14, 0.8, bounce=True, shadow=False)
        else:
            self.add(x, y - 10, f"-{amount}", settings.RED, 18, 0.9, bounce=True, shadow=True)

    def add_enemy_damage(self, x, y, amount, crit=False):
        if crit:
            self.add(x, y - 15, f"-{amount}", settings.YELLOW, 26, 1.2, bounce=True, shadow=True)
            self.add(x + 15, y - 28, "CRIT!", settings.YELLOW, 14, 0.8, bounce=True, shadow=False)
        else:
            self.add(x, y - 10, f"-{amount}", settings.WHITE, 18, 0.9, bounce=True, shadow=True)

    def add_heal(self, x, y, amount):
        self.add(x, y - 10, f"+{amount}", settings.GREEN, 18, 1.0, bounce=True, shadow=True)

    def add_rigor(self, x, y, amount):
        self.add(x, y - 10, f"+{amount} \u2211", settings.BLUE, 14, 0.8, bounce=True, shadow=False)

    def add_info(self, x, y, text, color=settings.CYAN):
        self.add(x, y - 10, text, color, 14, 0.8, bounce=False, shadow=False)

    def add_formula(self, x, y, text, color=settings.YELLOW):
        self.add(x, y + 5, text, color, 16, 1.5, bounce=False, shadow=True)

    def add_miss(self, x, y):
        self.add(x, y - 10, "MISS", settings.GRAY, 16, 0.7, bounce=True, shadow=False)

    def add_blocked(self, x, y):
        self.add(x, y - 10, "BLOCKED", settings.LIGHT_GRAY, 14, 0.7, bounce=True, shadow=False)

    def add_evasion(self, x, y):
        self.add(x, y - 10, "∇×0", settings.PURPLE, 14, 0.7, bounce=True, shadow=False)

    def update(self, dt):
        for t in self.texts:
            t.update(dt)
        self.texts = [t for t in self.texts if t.alive]

    def draw(self, screen):
        for t in self.texts:
            t.draw(screen)

    def clear(self):
        self.texts.clear()