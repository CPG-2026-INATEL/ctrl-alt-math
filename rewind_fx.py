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
        self.tracking_y = 0

    def _build_scanlines(self):
        self.scanline_surface.fill((0, 0, 0, 0))
        for y in range(0, settings.WINDOW_HEIGHT, 3):
            pygame.draw.line(self.scanline_surface, (0, 0, 0, 50), (0, y),
                           (settings.WINDOW_WIDTH, y))

    def apply_rewind_fx(self, screen, time_val):
        # 1. Scanlines
        self.scanline_surface.set_alpha(150)
        screen.blit(self.scanline_surface, (0, 0))

        # 2. CRT Neon Green Tint
        tint = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
        tint.fill((10, 45, 15))
        tint.set_alpha(35)
        screen.blit(tint, (0, 0))

        # 3. Dynamic Rolling VHS Tracking Distortion & Horizontal Tear Glitch
        self.tracking_y = (self.tracking_y + 8) % settings.WINDOW_HEIGHT
        try:
            slice_h = 32
            slice_y = max(0, min(settings.WINDOW_HEIGHT - slice_h, self.tracking_y))
            slice_rect = pygame.Rect(0, slice_y, settings.WINDOW_WIDTH, slice_h)
            slice_surf = screen.subsurface(slice_rect).copy()
            # Displace slice horizontally to simulate tracking shift
            disp_x = random.choice([-16, -10, -6, 6, 10, 16]) if random.random() < 0.8 else 0
            screen.blit(slice_surf, (disp_x, slice_y))
            # Border glitch line
            if disp_x != 0:
                pygame.draw.line(screen, (100, 255, 100, 150), (0, slice_y), (settings.WINDOW_WIDTH, slice_y), 1)
                pygame.draw.line(screen, (20, 80, 20, 150), (0, slice_y + slice_h), (settings.WINDOW_WIDTH, slice_y + slice_h), 1)
        except Exception:
            pass

        # 4. Dense Static Noise Sprites
        self.static_timer += 0.016
        for _ in range(80):
            x = random.randint(0, settings.WINDOW_WIDTH)
            y = random.randint(0, settings.WINDOW_HEIGHT)
            w = random.randint(2, 6)
            h = random.randint(1, 2)
            alpha = random.randint(40, 120)
            s = pygame.Surface((w, h))
            s.set_alpha(alpha)
            s.fill((220, 255, 220))
            screen.blit(s, (x, y))

        # 5. Full-Screen Horizontal Noise Glitch Line
        if random.random() < 0.15:
            gy = random.randint(0, settings.WINDOW_HEIGHT)
            pygame.draw.rect(screen, (180, 255, 180), (0, gy, settings.WINDOW_WIDTH, random.randint(2, 5)), 0)

        # 6. VHS Tape HUD Indicators (Green CRT Font)
        pulse = int(180 + 75 * (0.5 + 0.5 * math.sin(time_val * 12)))
        hud_color = (120, 255, 120)
        
        # Center title
        draw_text(screen, "<< ALT+Z REWIND >>",
                 (settings.WINDOW_WIDTH // 2, 50),
                 (pulse, 255, pulse), 28)

        # Top-left corner: PLAY vs REW
        draw_text(screen, "REW ◄◄ 30x", (50, 40), hud_color, 16)
        
        # Top-right corner: MEM RESET active
        draw_text(screen, "STATE: INVERSE ENTROPY", (settings.WINDOW_WIDTH - 150, 40), hud_color, 14)
        
        # Bottom-left: INDEX
        draw_text(screen, "INDEX: -2 TURNS", (50, settings.WINDOW_HEIGHT - 60), hud_color, 14)
        
        # Bottom-right: FAST TIME CODE
        tc_frames = int((time_val * 60) % 30)
        tc_secs = int(time_val) % 60
        tc_mins = int(time_val // 60) % 60
        tc_str = f"TC 00:{tc_mins:02d}:{tc_secs:02d}:{tc_frames:02d}"
        draw_text(screen, tc_str, (settings.WINDOW_WIDTH - 150, settings.WINDOW_HEIGHT - 60), hud_color, 14)
