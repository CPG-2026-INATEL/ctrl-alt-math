import pygame
import math
import random

import settings
from utils import distance, angle_between, clamp
from projectile import Projectile


class Enemy:
    def __init__(self, x, y, enemy_type):
        self.x = x
        self.y = y
        self.type = enemy_type
        self.alive = True
        self.size = settings.ENEMY_SIZE
        self.action_timer = random.uniform(0, 0.5)
        self.attacking = False
        self.attack_timer = 0
        self.attack_telegraphed = False
        self.flash_timer = 0
        self.dead = False

        self.spawn_timer = 0.5
        self.spawn_duration = 0.5
        self.bob_phase = random.random() * math.pi * 2
        self.bob_amplitude = 2

        if enemy_type == "censor":
            self.hp = settings.CENSOR_HP
            self.max_hp = settings.CENSOR_HP
            self.speed = settings.CENSOR_SPEED
            self.damage = settings.CENSOR_DAMAGE
            self.attack_range = settings.CENSOR_ATTACK_RANGE
            self.color = settings.COLOR_CENSOR
            self.move_per_action = 30
        elif enemy_type == "strawman":
            self.hp = settings.STRAWMAN_HP
            self.max_hp = settings.STRAWMAN_HP
            self.speed = settings.STRAWMAN_SPEED
            self.damage = settings.STRAWMAN_DAMAGE
            self.attack_range = 30
            self.color = settings.COLOR_STRAWMAN
            self.move_per_action = 35
            self.decoy_timer = 0
            self.decoy = False
        elif enemy_type == "bayesian":
            self.hp = settings.BAYESIAN_HP
            self.max_hp = settings.BAYESIAN_HP
            self.speed = settings.BAYESIAN_SPEED
            self.damage = settings.BAYESIAN_DAMAGE
            self.attack_range = 200
            self.color = settings.COLOR_BAYESIAN
            self.move_per_action = 28
        elif enemy_type == "boss":
            self.hp = settings.BOSS_HP
            self.max_hp = settings.BOSS_HP
            self.speed = settings.BOSS_SPEED
            self.damage = settings.BOSS_DAMAGE
            self.attack_range = 250
            self.color = settings.COLOR_BOSS
            self.size = settings.BOSS_SIZE
            self.move_per_action = 20
            self.phase = 1
            self.boss_action_type = "move"
            self.area_attack_telegraph = 0
            self.last_phase = 1
            self.pulse_timer = 0

        self.target_x = x
        self.target_y = y

        self.decoy_lifetime = 0
        self.is_decoy = False

    def get_hitbox(self):
        return pygame.Rect(self.x - self.size, self.y - self.size,
                           self.size * 2, self.size * 2)

    def get_action_interval(self):
        if self.type == "boss":
            base = settings.BOSS_ACTION_INTERVAL
            if self.hp < self.max_hp * 0.33:
                return base * 0.6
            if self.hp < self.max_hp * 0.66:
                return base * 0.8
            return base
        return settings.ENEMY_ACTION_INTERVAL

    def take_damage(self, amount):
        self.hp -= amount
        self.flash_timer = 0.15
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            self.dead = True
            return True
        return False

    def get_predicted_position(self, player, steps=1):
        if self.type != "bayesian":
            return (self.x, self.y)
        px = player.x
        py = player.y
        spd = player.speed * 0.3
        dir_x = player.dir_x
        dir_y = player.dir_y
        for _ in range(steps):
            px += dir_x * spd
            py += dir_y * spd
        return (px, py)

    def update(self, dt, player, projectiles, entropy=0):
        if self.dead:
            return

        self.spawn_timer = max(0, self.spawn_timer - dt)
        self.flash_timer = max(0, self.flash_timer - dt)
        self.bob_phase += dt * 3
        speed_mult = 1.0 + (entropy / settings.MAX_ENTROPY) * 0.3
        self.action_timer -= dt * speed_mult

        if self.attacking:
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.execute_attack(player, projectiles)
                self.attacking = False
            return

        if self.action_timer <= 0:
            self.action_timer = self.get_action_interval()
            self.take_action(player, projectiles)

        if self.type == "boss":
            self.pulse_timer += dt * 2

        if self.is_decoy:
            self.decoy_lifetime -= dt
            self.move_per_action = random.randint(10, 40)
            if self.decoy_lifetime <= 0:
                self.dead = True
                self.alive = False

    def take_action(self, player, projectiles):
        dist = distance((self.x, self.y), (player.x, player.y))

        if self.type == "boss":
            self.boss_action(player, projectiles, dist)
        elif dist < self.attack_range and random.random() < 0.4:
            self.start_attack(player, projectiles)
        else:
            self.move_toward(player)

    def move_toward(self, player):
        angle = angle_between((self.x, self.y), (player.x, player.y))
        if self.type == "strawman" and not self.is_decoy and random.random() < 0.2:
            angle += random.uniform(-1.5, 1.5)
        dist = self.move_per_action
        self.target_x = self.x + math.cos(angle) * dist
        self.target_y = self.y + math.sin(angle) * dist

        arena_left = settings.ARENA_OFFSET_X + self.size
        arena_right = settings.ARENA_OFFSET_X + settings.ARENA_WIDTH - self.size
        arena_top = settings.ARENA_OFFSET_Y + self.size
        arena_bottom = settings.ARENA_OFFSET_Y + settings.ARENA_HEIGHT - self.size
        self.target_x = clamp(self.target_x, arena_left, arena_right)
        self.target_y = clamp(self.target_y, arena_top, arena_bottom)

        self.x = self.target_x
        self.y = self.target_y

    def start_attack(self, player, projectiles):
        self.attacking = True
        self.attack_telegraphed = False
        self.attack_timer = 0.5

    def execute_attack(self, player, projectiles):
        if self.type == "censor":
            angle = angle_between((self.x, self.y), (player.x, player.y))
            spd = 200
            proj = Projectile(
                self.x, self.y,
                math.cos(angle) * spd,
                math.sin(angle) * spd,
                self.damage, "enemy",
                color=settings.RED, size=5
            )
            projectiles.append(proj)
        elif self.type == "strawman":
            if self.is_decoy:
                return
            angle = angle_between((self.x, self.y), (player.x, player.y))
            spd = 180
            proj = Projectile(
                self.x, self.y,
                math.cos(angle) * spd,
                math.sin(angle) * spd,
                self.damage, "enemy",
                color=settings.ORANGE, size=3
            )
            projectiles.append(proj)
        elif self.type == "bayesian":
            pred = self.get_predicted_position(player, steps=2)
            angle = angle_between((self.x, self.y), pred)
            spd = settings.BAYESIAN_PROJECTILE_SPEED
            proj = Projectile(
                self.x, self.y,
                math.cos(angle) * spd,
                math.sin(angle) * spd,
                self.damage, "enemy",
                color=settings.PURPLE, size=4
            )
            projectiles.append(proj)

    def boss_action(self, player, projectiles, dist):
        phase = 1
        if self.hp < self.max_hp * 0.33:
            phase = 3
        elif self.hp < self.max_hp * 0.66:
            phase = 2

        if phase != self.last_phase:
            self.last_phase = phase

        choices = []
        if phase == 1:
            choices = ["line_attack", "move"]
        elif phase == 2:
            choices = ["line_attack", "area_attack", "move"]
        else:
            choices = ["line_attack", "area_attack", "line_attack", "move"]

        action = random.choice(choices)

        if action == "move":
            self.move_toward(player)
        elif action == "line_attack":
            angle = angle_between((self.x, self.y), (player.x, player.y))
            count = 3 if phase >= 3 else 2 if phase >= 2 else 1
            spread = 0.3 if count > 1 else 0
            for i in range(count):
                a = angle + (i - (count - 1) / 2) * spread
                spd = 180 + phase * 20
                proj = Projectile(
                    self.x, self.y,
                    math.cos(a) * spd,
                    math.sin(a) * spd,
                    self.damage, "enemy",
                    color=(255, 100, 100), size=7
                )
                projectiles.append(proj)
        elif action == "area_attack":
            self.area_attack_telegraph = 0.5

    def update_area_attack(self, dt, player, projectiles):
        if self.area_attack_telegraph > 0:
            self.area_attack_telegraph -= dt
            if self.area_attack_telegraph <= 0:
                for p in projectiles:
                    dist = distance((self.x, self.y), (p.x, p.y))
                    if dist < 120:
                        p.alive = False
                if distance((self.x, self.y), (player.x, player.y)) < 120:
                    player.take_damage(self.damage)
                self.area_attack_telegraph = 0

    def draw(self, screen):
        if self.dead:
            return

        spawn_scale = 1.0
        spawn_alpha = 255
        if self.spawn_timer > 0:
            progress = 1.0 - (self.spawn_timer / self.spawn_duration)
            spawn_scale = progress
            spawn_alpha = int(255 * progress)

        color = self.color
        if self.flash_timer > 0:
            color = settings.WHITE

        bob_y = math.sin(self.bob_phase) * self.bob_amplitude
        draw_y = self.y + bob_y

        if self.attacking:
            telegraph_alpha = min(1.0, (0.5 - self.attack_timer) / 0.3)
            telegraph_size = int(self.size * 2.5 * telegraph_alpha + 2)
            s = pygame.Surface((telegraph_size * 2, telegraph_size * 2))
            s.set_alpha(int(100 * telegraph_alpha))
            s.fill(settings.RED)
            screen.blit(s, (self.x - telegraph_size, draw_y - telegraph_size))

        area_at = getattr(self, 'area_attack_telegraph', 0)
        if area_at > 0:
            alpha = int(100 * (area_at / 0.5))
            s = pygame.Surface((240, 240))
            s.set_alpha(alpha)
            s.fill(settings.RED)
            screen.blit(s, (self.x - 120, draw_y - 120))
            pygame.draw.circle(screen, settings.RED,
                               (int(self.x), int(draw_y)), 120, 2)

        size = int(self.size * spawn_scale)
        if size < 1:
            size = 1

        if self.type == "censor":
            self._draw_censor(screen, self.x, draw_y, size, color, spawn_alpha)
        elif self.type == "strawman":
            self._draw_strawman(screen, self.x, draw_y, size, color, spawn_alpha)
        elif self.type == "bayesian":
            self._draw_bayesian(screen, self.x, draw_y, size, color, spawn_alpha)
        elif self.type == "boss":
            self._draw_boss(screen, self.x, draw_y, size, color, spawn_alpha)

        if self.type != "boss" and self.hp < self.max_hp:
            self._draw_hp_bar(screen, self.x, draw_y - size - 6, size)

    def _draw_censor(self, screen, x, y, size, color, alpha):
        rect = pygame.Rect(x - size, y - size, size * 2, size * 2)
        s = pygame.Surface((size * 2, size * 2))
        s.set_alpha(alpha)
        s.fill(color)
        screen.blit(s, rect)
        pygame.draw.rect(screen, (255, 255, 255), rect, 1)
        pygame.draw.line(screen, (255, 255, 255),
                         (x - size + 2, y - size + 2),
                         (x + size - 2, y + size - 2), 2)
        pygame.draw.line(screen, (255, 255, 255),
                         (x + size - 2, y - size + 2),
                         (x - size + 2, y + size - 2), 2)

    def _draw_strawman(self, screen, x, y, size, color, alpha):
        s = pygame.Surface((size * 2, size * 2))
        s.set_alpha(alpha)
        s.fill(color)
        screen.blit(s, (x - size, y - size))
        pygame.draw.rect(screen, (255, 255, 255), (x - size, y - size, size * 2, size * 2), 1)
        eye_size = max(2, size // 3)
        pygame.draw.circle(screen, settings.WHITE, (x - size // 2, y - size // 3), eye_size)
        pygame.draw.circle(screen, settings.WHITE, (x + size // 2, y - size // 3), eye_size)

    def _draw_bayesian(self, screen, x, y, size, color, alpha):
        s = pygame.Surface((size * 2, size * 2))
        s.set_alpha(alpha)
        s.fill(color)
        screen.blit(s, (x - size, y - size))
        pygame.draw.rect(screen, (255, 255, 255), (x - size, y - size, size * 2, size * 2), 1)
        eye_size = max(2, size // 3)
        pygame.draw.circle(screen, settings.YELLOW, (x, y - size // 3), eye_size + 1)
        pygame.draw.circle(screen, settings.WHITE, (x, y - size // 3), eye_size - 1)

    def _draw_boss(self, screen, x, y, size, color, alpha):
        pulse = math.sin(self.pulse_timer) * 3
        s = pygame.Surface((size * 2, size * 2))
        s.set_alpha(alpha)
        s.fill(color)
        screen.blit(s, (x - size, y - size))
        pygame.draw.rect(screen, (255, 255, 255),
                         (x - size, y - size, size * 2, size * 2), 2)
        pygame.draw.rect(screen, (255, 100, 100),
                         (x - size - 2, y - size - 2, size * 2 + 4, size * 2 + 4), 1)

        hp_ratio = self.hp / self.max_hp
        bar_w = size * 2.5
        bar_h = 5
        bar_x = x - bar_w // 2
        bar_y = y - size - 10
        pygame.draw.rect(screen, (60, 20, 20), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(screen, settings.RED, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))
        pygame.draw.rect(screen, settings.LIGHT_GRAY, (bar_x, bar_y, bar_w, bar_h), 1)

        eyes_y = y - 4
        eye_r = 5 + int(pulse)
        for ex in (x - 10, x + 10):
            pygame.draw.circle(screen, settings.YELLOW, (ex, eyes_y), eye_r)
            if self.attacking:
                pygame.draw.circle(screen, settings.RED, (ex, eyes_y), eye_r - 2)

        phase_text = ""
        if self.hp >= self.max_hp * 0.66:
            phase_text = "I"
        elif self.hp >= self.max_hp * 0.33:
            phase_text = "II"
        else:
            phase_text = "III"
        font = pygame.font.Font(None, 16)
        img = font.render(phase_text, True, settings.WHITE)
        screen.blit(img, (x - img.get_width() // 2, y + size + 2))

    def _draw_hp_bar(self, screen, x, y, size):
        bar_w = size * 2
        bar_h = 3
        bar_x = x - bar_w // 2
        bar_y = y
        hp_ratio = self.hp / self.max_hp
        pygame.draw.rect(screen, (60, 20, 20), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(screen, settings.RED, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))
        pygame.draw.rect(screen, settings.LIGHT_GRAY, (bar_x, bar_y, bar_w, bar_h), 1)
