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

def resolve_obstacle_collision(entity_x, entity_y, entity_size, obstacles):
    entity_rect = pygame.Rect(
        entity_x - entity_size, entity_y - entity_size,
        entity_size * 2, entity_size * 2
    )
    for obs in obstacles:
        if entity_rect.colliderect(obs):
            overlap_left = entity_rect.right - obs.left
            overlap_right = obs.right - entity_rect.left
            overlap_top = entity_rect.bottom - obs.top
            overlap_bottom = obs.bottom - entity_rect.top
            min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
            if min_overlap == overlap_left:
                entity_x -= overlap_left
            elif min_overlap == overlap_right:
                entity_x += overlap_right
            elif min_overlap == overlap_top:
                entity_y -= overlap_top
            else:
                entity_y += overlap_bottom
            entity_rect = pygame.Rect(
                entity_x - entity_size, entity_y - entity_size,
                entity_size * 2, entity_size * 2
            )
    return entity_x, entity_y
