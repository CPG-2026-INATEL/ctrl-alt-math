import pygame
import random
import math

import settings
from utils import draw_text


class RewindEffects:
    def __init__(self):
        self.scanline_surface = pygame.Surface(
            (settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA
        )
        self._build_scanlines()
        self.static_timer = 0

    def _build_scanlines(self):
        self.scanline_surface.fill((0, 0, 0, 0))
        for y in range(0, settings.WINDOW_HEIGHT, 3):
            pygame.draw.line(self.scanline_surface, (0, 0, 0, 40), (0, y),
                           (settings.WINDOW_WIDTH, y))

    def apply_rewind_fx(self, screen, time_val):
        self.scanline_surface.set_alpha(120)
        screen.blit(self.scanline_surface, (0, 0))

        tint = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
        tint.fill((0, 30, 0))
        tint.set_alpha(25)
        screen.blit(tint, (0, 0))

        self.static_timer += 0.016
        for _ in range(50):
            x = random.randint(0, settings.WINDOW_WIDTH)
            y = random.randint(0, settings.WINDOW_HEIGHT)
            alpha = random.randint(10, 30)
            s = pygame.Surface((2, 1))
            s.set_alpha(alpha)
            s.fill(settings.WHITE)
            screen.blit(s, (x, y))

        pulse = int(180 + 75 * (0.5 + 0.5 * math.sin(time_val * 8)))
        draw_text(screen, "\u27e8\u27e8 REWIND \u27e9\u27e9",
                 (settings.WINDOW_WIDTH // 2, 30),
                 (pulse, 255, pulse), 32)
