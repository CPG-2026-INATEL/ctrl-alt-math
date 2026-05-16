import pygame
import math

import settings
from utils import clamp, distance


class Player:
    def __init__(self):
        self.x = settings.WINDOW_WIDTH // 2
        self.y = settings.WINDOW_HEIGHT // 2 + 50
        self.col = 8
        self.row = 6
        self.size = settings.PLAYER_SIZE
        self.hp = settings.PLAYER_MAX_HP
        self.max_hp = settings.PLAYER_MAX_HP
        self.rigor = settings.PLAYER_MAX_RIGOR
        self.max_rigor = settings.PLAYER_MAX_RIGOR

        self.dir_x = 0
        self.dir_y = -1

        self.invulnerable = 0
        self.flash_timer = 0

        self.glow_phase = 0
        self.trail = []
        self.trail_max = 8

        self.anim_progress = 1.0
        self.anim_from_col = 8
        self.anim_from_row = 6
        self.anim_to_col = 8
        self.anim_to_row = 6
        self.anim_from_px = 0
        self.anim_from_py = 0
        self.anim_to_px = 0
        self.anim_to_py = 0

    def set_grid_position(self, col, row, grid):
        self.col = int(col)
        self.row = int(row)
        self.x, self.y = grid.to_pixel(self.col, self.row)

    def start_move_anim(self, from_col, from_row, to_col, to_row, grid):
        self.anim_from_col = from_col
        self.anim_from_row = from_row
        self.anim_to_col = to_col
        self.anim_to_row = to_row
        self.anim_from_px, self.anim_from_py = grid.to_pixel(from_col, from_row)
        self.anim_to_px, self.anim_to_py = grid.to_pixel(to_col, to_row)
        self.anim_progress = 0.0
        self.dir_x = to_col - from_col
        self.dir_y = to_row - from_row
        length = math.sqrt(self.dir_x ** 2 + self.dir_y ** 2)
        if length > 0:
            self.dir_x /= length
            self.dir_y /= length

    def update_animation(self, dt, grid=None):
        if self.anim_progress < 1.0:
            self.anim_progress = min(1.0, self.anim_progress + dt * 5)
            t = self.anim_progress
            t = t * t * (3 - 2 * t)
            self.x = self.anim_from_px + (self.anim_to_px - self.anim_from_px) * t
            self.y = self.anim_from_py + (self.anim_to_py - self.anim_from_py) * t
            if self.anim_progress >= 1.0:
                self.col = int(self.anim_to_col)
                self.row = int(self.anim_to_row)
                if grid is not None:
                    self.x, self.y = grid.to_pixel(self.col, self.row)

    def update(self, dt, keys):
        self.attack_cooldown = max(0, getattr(self, 'attack_cooldown', 0) - dt)
        self.pitagoras_cooldown = max(0, getattr(self, 'pitagoras_cooldown', 0) - dt)
        self.reflexao_cooldown = max(0, getattr(self, 'reflexao_cooldown', 0) - dt)

        self.invulnerable = max(0, self.invulnerable - dt)
        self.flash_timer = max(0, self.flash_timer - dt)

        
        self.glow_phase += dt * 4

    def basic_attack(self):
        return True

    def pitagoras_attack(self):
        if getattr(self, 'pitagoras_cooldown', 0) > 0:
            return False
        if self.rigor < settings.PITAGORAS_RIGOR_COST:
            return False
        self.rigor -= settings.PITAGORAS_RIGOR_COST
        self.pitagoras_cooldown = 1.0
        return True

    def reflexao_attack(self):
        if getattr(self, 'reflexao_cooldown', 0) > 0:
            return False
        if self.rigor < settings.REFLEXAO_RIGOR_COST:
            return False
        self.rigor -= settings.REFLEXAO_RIGOR_COST
        self.reflexao_active = True
        self.reflexao_timer = 0.3
        self.reflexao_cooldown = 2.0
        return True

    def take_damage(self, amount):
        if self.invulnerable > 0:
            return False
        self.hp -= amount
        self.invulnerable = 0.4
        self.flash_timer = 0.4
        return True

    def set_position(self, pos):
        self.x, self.y = pos

    def set_hp(self, hp, max_hp):
        self.hp = hp
        self.max_hp = max_hp

    def draw(self, screen):
        for tx, ty, t in self.trail:
            alpha = int((t / 0.3) * 80)
            trail_size = int(self.size * (t / 0.3))
            if trail_size > 0:
                s = pygame.Surface((trail_size * 2, trail_size * 2))
                s.set_alpha(alpha)
                s.fill(settings.CYAN)
                screen.blit(s, (tx - trail_size, ty - trail_size))

        glow_size = int(3 + math.sin(self.glow_phase) * 2)
        glow_surf = pygame.Surface((self.size * 2 + glow_size * 2,
                                     self.size * 2 + glow_size * 2))
        glow_surf.set_alpha(40)
        glow_surf.fill(settings.CYAN)
        screen.blit(glow_surf, (self.x - self.size - glow_size,
                                 self.y - self.size - glow_size))

        color = settings.COLOR_PLAYER
        if self.flash_timer > 0:
            color = settings.WHITE
        elif self.invulnerable > 0:
            if int(self.invulnerable * 10) % 2 == 0:
                color = (100, 200, 200)

        rect = pygame.Rect(self.x - self.size, self.y - self.size,
                           self.size * 2, self.size * 2)
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, settings.WHITE, rect, 1)

        tip_x = self.x + self.dir_x * self.size * 1.8
        tip_y = self.y + self.dir_y * self.size * 1.8
        pygame.draw.line(screen, settings.WHITE,
                         (self.x, self.y), (tip_x, tip_y), 3)
