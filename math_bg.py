import pygame
import random
import settings

FORMULAS = [
    "int f(x) dx", "sum(n=1->inf)", "sqrt(a^2+b^2)=c", "df/dx", "curl(F)",
    "e^(i*pi)+1=0", "int B.dl = mu0 I", "dS>=0", "lambda=h/p", "F=ma",
    "E=mc^2", "grad^2 phi=0", "det(A)!=0", "lim(x->0)", "prod(1+1/n)",
    "sin^2(t)+cos^2(t)=1", "a.b=|a||b|cos(t)", "int int int dV", "P(A|B)=P(B|A)P(A)/P(B)",
]


class FloatingFormula:
    def __init__(self, arena_rect):
        self.text = random.choice(FORMULAS)
        side = random.randint(0, 3)
        if side == 0:
            self.x = random.randint(arena_rect.left, arena_rect.right)
            self.y = arena_rect.top - 10
            self.vx = random.uniform(-15, 15)
            self.vy = random.uniform(5, 15)
        elif side == 1:
            self.x = random.randint(arena_rect.left, arena_rect.right)
            self.y = arena_rect.bottom + 10
            self.vx = random.uniform(-15, 15)
            self.vy = random.uniform(-15, -5)
        elif side == 2:
            self.x = arena_rect.left - 10
            self.y = random.randint(arena_rect.top, arena_rect.bottom)
            self.vx = random.uniform(5, 15)
            self.vy = random.uniform(-15, 15)
        else:
            self.x = arena_rect.right + 10
            self.y = random.randint(arena_rect.top, arena_rect.bottom)
            self.vx = random.uniform(-15, -5)
            self.vy = random.uniform(-15, 15)

        self.alpha = 0
        self.max_alpha = random.randint(15, 30)
        self.lifetime = random.uniform(6.0, 12.0)
        self.age = 0
        self.fade_in = 1.5
        self.fade_out = 2.0
        self.font = pygame.font.Font(None, random.choice([20, 24, 28]))
        self.color = random.choice([settings.CYAN, settings.PURPLE, settings.GOLD, settings.WHITE])

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.age += dt
        if self.age < self.fade_in:
            self.alpha = int(self.max_alpha * (self.age / self.fade_in))
        elif self.age > self.lifetime - self.fade_out:
            remaining = self.lifetime - self.age
            self.alpha = int(self.max_alpha * (remaining / self.fade_out))
        else:
            self.alpha = self.max_alpha
        return self.age < self.lifetime

    def draw(self, screen):
        if self.alpha <= 0:
            return
        img = self.font.render(self.text, True, self.color)
        img.set_alpha(self.alpha)
        screen.blit(img, (self.x - img.get_width() // 2, self.y - img.get_height() // 2))


class MathBackground:
    def __init__(self):
        self.formulas = []
        self.spawn_timer = 0
        self.spawn_interval = 2.0

    def update(self, dt, arena_rect):
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            if len(self.formulas) < 15:
                self.formulas.append(FloatingFormula(arena_rect))
        self.formulas = [f for f in self.formulas if f.update(dt)]

    def draw(self, screen):
        for f in self.formulas:
            f.draw(screen)
