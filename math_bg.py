import pygame
import random
import settings

# Define the formulas for each theme
THEMES = {
    0: {
        "name": "Default",
        "colors": [settings.CYAN, settings.PURPLE, settings.GOLD, settings.WHITE],
        "bg_color": settings.DARK_BLUE,
        "arena_color": (15, 15, 35),
        "formulas": [
            "\u222bf(x)dx", "\u2211(n=1\u2192\u221e)", "\u221a(a\u00b2+b\u00b2)=c", "\u2202f/\u2202x", "\u2207\u00d7F",
            "e^(i\u03c0)+1=0", "\u222eB\u00b7dl=\u03bc\u2080I", "\u0394S\u22650", "\u03bb=h/p", "F=ma",
            "E=mc\u00b2", "\u2207\u00b2\u03c6=0", "det(A)\u22600", "lim(x\u21920)", "\u220f(1+1/n)",
            "sin\u00b2\u03b8+cos\u00b2\u03b8=1", "a\u00b7b=|a||b|cos\u03b8", "\u222b\u222b\u222b dV", "P(A|B)=P(B|A)P(A)/P(B)",
        ]
    },
    1: {
        "name": "Algebra",
        "colors": [settings.GREEN, settings.YELLOW, settings.WHITE],
        "bg_color": (10, 30, 10), # Dark Green
        "arena_color": (20, 40, 20),
        "formulas": ["x+y=z", "ax\u00b2+bx+c=0", "(a+b)\u00b2", "f(x)", "y=mx+b", "\u2211x_i", "x\u2192\u221e", "a\u22600"]
    },
    2: {
        "name": "Geometry",
        "colors": [settings.BLUE, settings.CYAN, settings.WHITE],
        "bg_color": (10, 20, 40), # Deep Blue
        "arena_color": (20, 30, 50),
        "formulas": ["\u03c0r\u00b2", "sin\u03b8", "cos\u03b8", "tan\u03b8", "a\u00b2+b\u00b2=c\u00b2", "\u25b3ABC", "\u25cb", "\u2220", "2\u03c0r"]
    },
    3: {
        "name": "Calculus",
        "colors": [settings.PURPLE, settings.MAGENTA, settings.WHITE],
        "bg_color": (30, 10, 40), # Dark Purple
        "arena_color": (40, 20, 50),
        "formulas": ["\u222bf(x)dx", "dy/dx", "lim\u2192\u221e", "\u2202f/\u2202x", "\u222b\u222b dA", "\u03b5-\u03b4", "f'(x)", "df"]
    },
    4: {
        "name": "Statistics",
        "colors": [settings.GOLD, settings.YELLOW, settings.ORANGE],
        "bg_color": (40, 35, 10), # Dark Yellow/Amber
        "arena_color": (50, 45, 20),
        "formulas": ["\u03bc", "\u03c3", "\u03a3x", "P(A|B)", "E[X]", "Z-score", "\u03c7\u00b2", "\u03c3\u00b2", "H\u2080"]
    },
    5: {
        "name": "Logic",
        "colors": [settings.CYAN, settings.WHITE, settings.TEAL],
        "bg_color": (0, 30, 30), # Dark Teal
        "arena_color": (10, 40, 40),
        "formulas": ["P\u2227Q", "P\u2228Q", "\u00acP", "P\u2192Q", "\u2200x", "\u2203y", "\u22a2", "\u22a8", "T \u22a2 \u22a5"]
    },
    6: {
        "name": "Number Theory",
        "colors": [settings.ORANGE, settings.GOLD, settings.BROWN],
        "bg_color": (30, 20, 10), # Dark Brownish
        "arena_color": (40, 30, 20),
        "formulas": ["a\u2261b(mod n)", "gcd(a,b)", "lcm(a,b)", "\u03c6(n)", "p \u2208 \u2119", "n!", "a\u207f+b\u207f=c\u207f", "d|n"]
    },
    7: {
        "name": "Set Theory",
        "colors": [settings.PINK, settings.PURPLE, settings.MAGENTA],
        "bg_color": (40, 15, 35), # Dark Pink/Wine
        "arena_color": (50, 25, 45),
        "formulas": ["A\u222aB", "A\u2229B", "x\u2208A", "A\u2282B", "\u2205", "\u2135\u2080", "\u2118(S)", "A\u00d7B"]
    },
    8: {
        "name": "Topology",
        "colors": [settings.BROWN, settings.ORANGE, settings.NAVY],
        "bg_color": (20, 10, 10), # Dark Dark Red
        "arena_color": (30, 20, 20),
        "formulas": ["X\u2245Y", "\u2202M", "\u03c0\u2081(X)", "genus(S)", "f:X\u2192Y", "H_n(X)", "K\u2084", "\u03c7=V-E+F"]
    },
    9: {
        "name": "Physics",
        "colors": [settings.RED, settings.ORANGE, settings.YELLOW],
        "bg_color": (40, 10, 10), # Dark Red
        "arena_color": (50, 20, 20),
        "formulas": ["F=ma", "E=mc\u00b2", "\u2207\u00b7B=0", "L=I\u03c9", "v\u20d7", "a\u20d7", "p=mv", "\u03bb=h/p", "G\u03bc\u03bd=8\u03c0T\u03bc\u03bd"]
    }
}


class FloatingFormula:
    def __init__(self, arena_rect, theme_index=0):
        theme = THEMES.get(theme_index, THEMES[0])
        self.text = random.choice(theme["formulas"])
        self.color = random.choice(theme["colors"])
        self.theme_index = theme_index
        
        side = random.randint(0, 3)
        if side == 0:
            self.x = random.randint(arena_rect.left, arena_rect.right)
            self.y = arena_rect.top - 20
            self.vx = random.uniform(-20, 20)
            self.vy = random.uniform(10, 25)
        elif side == 1:
            self.x = random.randint(arena_rect.left, arena_rect.right)
            self.y = arena_rect.bottom + 20
            self.vx = random.uniform(-20, 20)
            self.vy = random.uniform(-25, -10)
        elif side == 2:
            self.x = arena_rect.left - 20
            self.y = random.randint(arena_rect.top, arena_rect.bottom)
            self.vx = random.uniform(10, 25)
            self.vy = random.uniform(-20, 20)
        else:
            self.x = arena_rect.right + 20
            self.y = random.randint(arena_rect.top, arena_rect.bottom)
            self.vx = random.uniform(-25, -10)
            self.vy = random.uniform(-20, 20)

        self.alpha = 0
        self.max_alpha = random.randint(40, 80) # Much more visible
        self.lifetime = random.uniform(5.0, 10.0)
        self.age = 0
        self.fade_in = 0.8
        self.fade_out = 1.2
        self.font = pygame.font.Font(None, random.choice([26, 30, 34, 40]))
        self.rotation = 0
        self.rotation_speed = random.uniform(-30, 30) if theme_index == 2 else 0 # Rotate only for Geometry

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += self.rotation_speed * dt
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
        
        # Base image
        img = self.font.render(self.text, True, self.color)
        if self.rotation != 0:
            img = pygame.transform.rotate(img, self.rotation)
        
        # Subtle Glow Effect (draw slightly offset and darker/more transparent)
        glow = self.font.render(self.text, True, (max(0, self.color[0]-50), max(0, self.color[1]-50), max(0, self.color[2]-50)))
        if self.rotation != 0:
            glow = pygame.transform.rotate(glow, self.rotation)
        glow.set_alpha(self.alpha // 2)
        
        pos = (self.x - img.get_width() // 2, self.y - img.get_height() // 2)
        screen.blit(glow, (pos[0] + 2, pos[1] + 2)) # Glow offset
        img.set_alpha(self.alpha)
        screen.blit(img, pos)


class MathBackground:
    def __init__(self):
        self.formulas = []
        self.spawn_timer = 0
        self.spawn_interval = 0.8 # Faster spawn
        self.current_theme = 0
        self.transition_timer = 0

    def set_theme(self, index):
        if index in THEMES:
            self.current_theme = index
            self.formulas = [] 
            self.spawn_timer = self.spawn_interval # Immediate spawn
            self.transition_timer = 1.0 # Trigger a "flash" period
            return THEMES[index]["name"]
        return None

    def get_bg_color(self):
        base = list(THEMES[self.current_theme]["bg_color"])
        if self.transition_timer > 0:
            # Add a white flash that fades out
            flash = int(100 * self.transition_timer)
            base[0] = min(255, base[0] + flash)
            base[1] = min(255, base[1] + flash)
            base[2] = min(255, base[2] + flash)
        return tuple(base)

    def get_arena_color(self):
        return THEMES[self.current_theme]["arena_color"]

    def update(self, dt, arena_rect):
        if self.transition_timer > 0:
            self.transition_timer -= dt * 2
            # During transition, spawn many formulas at once
            if len(self.formulas) < 10:
                self.formulas.append(FloatingFormula(arena_rect, self.current_theme))

        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            if len(self.formulas) < 25: # More density
                self.formulas.append(FloatingFormula(arena_rect, self.current_theme))
        self.formulas = [f for f in self.formulas if f.update(dt)]

    def draw(self, screen):
        for f in self.formulas:
            f.draw(screen)
