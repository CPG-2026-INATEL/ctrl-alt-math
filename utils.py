import pygame
import math

def draw_text(surf, text, pos, color, size=24, center=True):
    font = pygame.font.Font(None, size)
    for i, line in enumerate(text.split('\n')):
        img = font.render(line, True, color)
        if center:
            rect = img.get_rect(center=(pos[0], pos[1] + i * size * 1.3))
        else:
            rect = img.get_rect(topleft=(pos[0], pos[1] + i * size * 1.3))
        surf.blit(img, rect)

def draw_text_simple(surf, text, pos, color, size=24):
    font = pygame.font.Font(None, size)
    img = font.render(text, True, color)
    surf.blit(img, pos)

def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))

def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def angle_between(p1, p2):
    return math.atan2(p2[1] - p1[1], p2[0] - p1[0])

def lerp(a, b, t):
    return a + (b - a) * t

def point_in_rect(px, py, rx, ry, rw, rh):
    return rx <= px <= rx + rw and ry <= py <= ry + rh
