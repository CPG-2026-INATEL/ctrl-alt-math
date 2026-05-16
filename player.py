import pygame
import math

import settings
from utils import clamp, distance


class Player:
    def __init__(self):
        self.x = settings.WINDOW_WIDTH // 2
        self.y = settings.WINDOW_HEIGHT // 2 + 50
        self.size = settings.PLAYER_SIZE
        self.speed = settings.PLAYER_SPEED

        self.hp = settings.PLAYER_MAX_HP
        self.max_hp = settings.PLAYER_MAX_HP
        self.rigor = settings.PLAYER_MAX_RIGOR
        self.max_rigor = settings.PLAYER_MAX_RIGOR

        self.dir_x = 0
        self.dir_y = -1

        self.attack_cooldown = 0
        self.basic_attack_active = False
        self.attack_timer = 0

        self.pitagoras_cooldown = 0
        self.reflexao_cooldown = 0
        self.reflexao_active = False
        self.reflexao_timer = 0

        self.invulnerable = 0
        self.flash_timer = 0

        self.glow_phase = 0
        self.trail = []
        self.trail_max = 8

    def update(self, dt, keys):
        mx, my = 0, 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            mx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            mx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            my -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            my += 1

        is_moving = mx != 0 or my != 0
        if is_moving:
            length = math.sqrt(mx * mx + my * my)
            mx /= length
            my /= length
            self.dir_x = mx
            self.dir_y = my

        old_x, old_y = self.x, self.y
        self.x += mx * self.speed * dt
        self.y += my * self.speed * dt

        arena_left = settings.ARENA_OFFSET_X + self.size
        arena_right = settings.ARENA_OFFSET_X + settings.ARENA_WIDTH - self.size
        arena_top = settings.ARENA_OFFSET_Y + self.size
        arena_bottom = settings.ARENA_OFFSET_Y + settings.ARENA_HEIGHT - self.size
        self.x = clamp(self.x, arena_left, arena_right)
        self.y = clamp(self.y, arena_top, arena_bottom)

        if is_moving and (abs(self.x - old_x) > 1 or abs(self.y - old_y) > 1):
            self.trail.append((self.x, self.y, 0.3))
            if len(self.trail) > self.trail_max:
                self.trail.pop(0)
        self.trail = [(tx, ty, t - dt) for tx, ty, t in self.trail if t > 0]

        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        self.pitagoras_cooldown = max(0, self.pitagoras_cooldown - dt)
        self.reflexao_cooldown = max(0, self.reflexao_cooldown - dt)

        if self.basic_attack_active:
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.basic_attack_active = False

        if self.reflexao_active:
            self.reflexao_timer -= dt
            if self.reflexao_timer <= 0:
                self.reflexao_active = False

        self.invulnerable = max(0, self.invulnerable - dt)
        self.flash_timer = max(0, self.flash_timer - dt)

        self.rigor = min(self.max_rigor, self.rigor + settings.RIGOR_REGEN_RATE * dt)

        self.glow_phase += dt * 4

    def basic_attack(self):
        if self.attack_cooldown > 0:
            return False
        self.attack_cooldown = settings.PLAYER_ATTACK_COOLDOWN
        self.basic_attack_active = True
        self.attack_timer = 0.15
        return True

    def get_attack_hitbox(self):
        cx = self.x + self.dir_x * (self.size + settings.PLAYER_ATTACK_RANGE // 2)
        cy = self.y + self.dir_y * (self.size + settings.PLAYER_ATTACK_RANGE // 2)
        w = settings.PLAYER_ATTACK_RANGE
        h = settings.PLAYER_ATTACK_RANGE // 2
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (cx, cy)
        return rect

    def pitagoras_attack(self):
        if self.pitagoras_cooldown > 0:
            return False
        if self.rigor < settings.PITAGORAS_RIGOR_COST:
            return False
        self.rigor -= settings.PITAGORAS_RIGOR_COST
        self.pitagoras_cooldown = 1.0
        return True

    def get_pitagoras_hitbox(self):
        cx = self.x + self.dir_x * (self.size + settings.PITAGORAS_RANGE // 2)
        cy = self.y + self.dir_y * (self.size + settings.PITAGORAS_RANGE // 2)
        w = settings.PITAGORAS_RANGE
        h = settings.PITAGORAS_RANGE // 2
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (cx, cy)
        return rect

    def reflexao_attack(self):
        if self.reflexao_cooldown > 0:
            return False
        if self.rigor < settings.REFLEXAO_RIGOR_COST:
            return False
        self.rigor -= settings.REFLEXAO_RIGOR_COST
        self.reflexao_active = True
        self.reflexao_timer = 0.3
        self.reflexao_cooldown = 2.0
        return True

    def get_reflexao_hitbox(self):
        return pygame.Rect(
            self.x - settings.REFLEXAO_RANGE,
            self.y - settings.REFLEXAO_RANGE,
            settings.REFLEXAO_RANGE * 2,
            settings.REFLEXAO_RANGE * 2
        )

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
        glow_color = (50, 255, 255, 60)
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

        if self.basic_attack_active:
            hb = self.get_attack_hitbox()
            s = pygame.Surface((hb.width, hb.height))
            s.set_alpha(80)
            s.fill(settings.WHITE)
            screen.blit(s, hb)

        if self.reflexao_active:
            progress = 1.0 - (self.reflexao_timer / 0.3)
            radius = int(settings.REFLEXAO_RANGE * progress)
            pygame.draw.circle(screen, settings.CYAN,
                               (int(self.x), int(self.y)), radius, 2)
            if radius > 5:
                inner = pygame.Surface((radius * 2, radius * 2))
                inner.set_alpha(30)
                inner.fill(settings.CYAN)
                screen.blit(inner, (self.x - radius, self.y - radius))
