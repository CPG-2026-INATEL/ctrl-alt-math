import pygame
import random
import math

import settings
from utils import draw_text, distance


class UI:
    def __init__(self):
        pass

    def draw_hud(self, screen, player, wave, skill_points, entropy, wave_count, game=None):
        bar_y = settings.WINDOW_HEIGHT - settings.UI_BAR_HEIGHT
        pygame.draw.rect(screen, settings.DARK_GRAY,
                         (0, bar_y, settings.WINDOW_WIDTH, settings.UI_BAR_HEIGHT))
        pygame.draw.line(screen, settings.GRAY, (0, bar_y),
                         (settings.WINDOW_WIDTH, bar_y), 1)

        hp_pct = player.hp / player.max_hp
        rigor_pct = player.rigor / player.max_rigor
        entropy_pct = entropy / settings.MAX_ENTROPY

        self._draw_bar(screen, settings.UI_PADDING, bar_y + 8, 160, 14,
                       hp_pct, settings.RED, (60, 20, 20))
        draw_text(screen, f"HP: {player.hp}/{player.max_hp}",
                  (settings.UI_PADDING + 80, bar_y + 15),
                  settings.WHITE, 14)

        self._draw_bar(screen, settings.UI_PADDING, bar_y + 26, 160, 14,
                       rigor_pct, settings.BLUE, (20, 20, 60))
        draw_text(screen, f"Rigor: {player.rigor:.0f}/{player.max_rigor}",
                  (settings.UI_PADDING + 80, bar_y + 33),
                  settings.WHITE, 14)

        self._draw_bar(screen, settings.UI_PADDING + 180, bar_y + 8, 120, 14,
                       entropy_pct, settings.COLOR_ENTROPY_BAR, (40, 10, 40))
        draw_text(screen, f"Entropy: {entropy:.0f}",
                  (settings.UI_PADDING + 240, bar_y + 15),
                  settings.WHITE, 14)

        draw_text(screen, f"Wave: {wave}/{wave_count}",
                  (settings.WINDOW_WIDTH // 2, bar_y + 15),
                  settings.LIGHT_GRAY, 18)

        draw_text(screen, f"Skill Points: {skill_points}",
                  (settings.WINDOW_WIDTH // 2, bar_y + 38),
                  settings.GOLD, 16)

        self._draw_skill_cooldowns(screen, bar_y, player, game)
        self._draw_controls(screen, bar_y)

    def _draw_skill_cooldowns(self, screen, bar_y, player, game):
        x = 360
        y = bar_y + 8
        has_pitagoras = game.skill_tree.is_unlocked("pitagoras") if game else False
        has_reflexao = game.skill_tree.is_unlocked("reflexao") if game else False
        has_ctrlz = game.skill_tree.is_unlocked("ctrlz") if game else False

        if has_pitagoras:
            ready = player.pitagoras_cooldown <= 0 and player.rigor >= settings.PITAGORAS_RIGOR_COST
            self._draw_cooldown_icon(screen, x, y, "1", ready,
                                     player.pitagoras_cooldown, 1.0,
                                     player.rigor >= settings.PITAGORAS_RIGOR_COST)
        x += 30

        if has_reflexao:
            ready = player.reflexao_cooldown <= 0 and player.rigor >= settings.REFLEXAO_RIGOR_COST
            self._draw_cooldown_icon(screen, x, y, "2", ready,
                                     player.reflexao_cooldown, 2.0,
                                     player.rigor >= settings.REFLEXAO_RIGOR_COST)
        x += 30

        if has_ctrlz:
            ready = game.rewind_cooldown <= 0 if game else False
            self._draw_cooldown_icon(screen, x, y, "R", ready,
                                     game.rewind_cooldown if game else 0, 2.0,
                                     len(game.rewind_buffer.buffer) > 0 if game else False)

    def _draw_cooldown_icon(self, screen, x, y, key, ready, cooldown, max_cooldown, has_resource):
        size = 20
        rect = pygame.Rect(x, y, size, size)
        if ready and has_resource:
            pygame.draw.rect(screen, (50, 180, 50), rect, border_radius=3)
            pygame.draw.rect(screen, settings.GREEN, rect, 1, border_radius=3)
        elif not ready:
            pygame.draw.rect(screen, (80, 80, 80), rect, border_radius=3)
            pygame.draw.rect(screen, (120, 120, 120), rect, 1, border_radius=3)
            pct = 1.0 - (cooldown / max_cooldown)
            pygame.draw.rect(screen, (100, 100, 100),
                             (x + 1, y + 1, int((size - 2) * pct), size - 2))
        else:
            pygame.draw.rect(screen, (60, 60, 40), rect, border_radius=3)
            pygame.draw.rect(screen, (100, 100, 60), rect, 1, border_radius=3)

        draw_text(screen, key, (x + size // 2, y + size // 2),
                  settings.WHITE, 12)

    def _draw_bar(self, screen, x, y, w, h, pct, fill_color, bg_color):
        pygame.draw.rect(screen, bg_color, (x, y, w, h))
        if pct > 0:
            pygame.draw.rect(screen, fill_color, (x, y, int(w * pct), h))
        pygame.draw.rect(screen, settings.LIGHT_GRAY, (x, y, w, h), 1)

    def _draw_controls(self, screen, bar_y):
        controls = [
            "WASD: Move",
            "Space: Atk",
            "1: Pitagoras",
            "2: Reflexao",
            "R: Rewind",
            "Tab: Skills",
            "Esc: Pause",
            "Q: Quit Menu"
        ]
        x = settings.WINDOW_WIDTH - 120
        y = bar_y + 4
        for c in controls:
            draw_text(screen, c, (x, y), settings.GRAY, 10, center=False)
            y += 11

    def draw_main_menu(self, screen, menu_items, selected_item):
        screen.fill(settings.DARK_BLUE)

        import math
        time_val = pygame.time.get_ticks() / 1000.0

        for i in range(40):
            x = int(400 + math.sin(time_val * 0.5 + i * 0.8) * 350)
            y = int(300 + math.cos(time_val * 0.3 + i * 1.2) * 250)
            alpha = int(30 + math.sin(time_val + i) * 20)
            s = pygame.Surface((2, 2))
            s.set_alpha(alpha)
            s.fill(settings.WHITE)
            screen.blit(s, (x, y))

        symbols = ["\u222b", "\u2211", "\u221a", "\u03c0", "\u221e", "\u0394", "\u2207", "\u03a3"]
        for i, sym in enumerate(symbols):
            x = 50 + i * 95
            y = 80 + int(math.sin(time_val * 2 + i) * 10)
            alpha = int(40 + math.sin(time_val + i * 0.5) * 20)
            font = pygame.font.Font(None, 28)
            img = font.render(sym, True, settings.CYAN)
            img.set_alpha(alpha)
            screen.blit(img, (x, y))

        draw_text(screen, "Ctrl + Alt + Math",
                  (settings.WINDOW_WIDTH // 2, 160),
                  settings.CYAN, 52)

        draw_text(screen, "A Mathematical Rebellion",
                  (settings.WINDOW_WIDTH // 2, 205),
                  settings.LIGHT_GRAY, 18)

        draw_text(screen, "In a world where math is forbidden,",
                  (settings.WINDOW_WIDTH // 2, 250),
                  settings.GRAY, 16)
        draw_text(screen, "you are the last mathematician.",
                  (settings.WINDOW_WIDTH // 2, 272),
                  settings.GRAY, 16)
        draw_text(screen, "Fight the regime with forbidden theorems.",
                  (settings.WINDOW_WIDTH // 2, 294),
                  settings.GRAY, 16)

        y_start = 360
        for i, (text, desc) in enumerate(menu_items):
            color = settings.WHITE if i == selected_item else settings.GRAY
            if i == selected_item:
                draw_text(screen, f"> {text} <", (settings.WINDOW_WIDTH // 2, y_start + i * 50),
                          color, 28)
            else:
                draw_text(screen, text, (settings.WINDOW_WIDTH // 2, y_start + i * 50),
                          color, 28)

        draw_text(screen, "Use UP/DOWN to navigate, ENTER to select",
                  (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT - 40),
                  settings.GRAY, 14)

    def draw_how_to_play(self, screen):
        screen.fill(settings.DARK_BLUE)
        draw_text(screen, "HOW TO PLAY",
                  (settings.WINDOW_WIDTH // 2, 40), settings.CYAN, 36)

        lines = [
            "",
            "You are a mathematician fighting the regime.",
            "Use WASD or Arrow Keys to move around the arena.",
            "",
            "COMBAT:",
            "  Space - Basic attack (melee range)",
            "  1 - Pitagoras theorem attack (if unlocked)",
            "  2 - Reflexao defensive burst (if unlocked)",
            "  R - Ctrl+Z rewind (if unlocked, increases Entropy)",
            "",
            "SKILL TREE:",
            "  Press Tab to open the skill tree.",
            "  Spend skill points to unlock theorem abilities.",
            "  Each skill has prerequisites that must be unlocked first.",
            "",
            "ENEMIES:",
            "  Censor Linear - Moves directly toward you",
            "  Falacia Espantalho - Erratic, creates decoys",
            "  Inquisidor Bayesiano - Predicts your movement",
            "  O Grande Simplificador - The final boss",
            "",
            "Survive all waves and defeat the boss to win!",
            "",
            "Press Esc to return"
        ]

        y = 80
        for line in lines:
            color = settings.LIGHT_GRAY
            if line.startswith("COMBAT:") or line.startswith("SKILL") or line.startswith("ENEMIES"):
                color = settings.GOLD
            draw_text(screen, line, (settings.WINDOW_WIDTH // 2, y), color, 16)
            y += 22

    def draw_pause(self, screen):
        overlay = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
        overlay.set_alpha(160)
        overlay.fill(settings.BLACK)
        screen.blit(overlay, (0, 0))
        draw_text(screen, "PAUSED",
                  (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 - 50),
                  settings.WHITE, 48)
        draw_text(screen, "Press Esc to resume",
                  (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2),
                  settings.GRAY, 20)
        draw_text(screen, "Press Q to quit to main menu",
                  (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 + 30),
                  settings.RED, 18)
        draw_text(screen, "Press Q to quit to menu",
                  (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 + 50),
                  settings.GRAY, 16)

    def draw_game_over(self, screen, wave):
        screen.fill(settings.DARK_RED)
        draw_text(screen, "GAME OVER",
                  (settings.WINDOW_WIDTH // 2, 200),
                  settings.RED, 56)
        draw_text(screen, f"You fell at Wave {wave}",
                  (settings.WINDOW_WIDTH // 2, 270),
                  settings.LIGHT_GRAY, 24)
        draw_text(screen, "The regime has silenced another mind.",
                  (settings.WINDOW_WIDTH // 2, 310),
                  settings.GRAY, 18)
        draw_text(screen, "Press ENTER to restart, Esc to quit to menu",
                  (settings.WINDOW_WIDTH // 2, 380),
                  settings.GRAY, 18)

    def draw_victory(self, screen):
        screen.fill(settings.DARK_BLUE)

        for _ in range(100):
            x = random.randint(0, settings.WINDOW_WIDTH)
            y = random.randint(0, settings.WINDOW_HEIGHT)
            alpha = random.randint(30, 80)
            s = pygame.Surface((3, 3))
            s.set_alpha(alpha)
            colors = [settings.GOLD, settings.CYAN, settings.GREEN, settings.PURPLE]
            s.fill(random.choice(colors))
            screen.blit(s, (x, y))

        draw_text(screen, "VICTORY!",
                  (settings.WINDOW_WIDTH // 2, 150),
                  settings.GOLD, 60)
        draw_text(screen, "You defeated O Grande Simplificador!",
                  (settings.WINDOW_WIDTH // 2, 220),
                  settings.WHITE, 24)
        draw_text(screen, "You proved that complexity survives.",
                  (settings.WINDOW_WIDTH // 2, 260),
                  settings.CYAN, 20)
        draw_text(screen, "Mathematics will never be forgotten.",
                  (settings.WINDOW_WIDTH // 2, 290),
                  settings.LIGHT_GRAY, 18)
        draw_text(screen, "\"The universe cannot be reduced to simple answers.\"",
                  (settings.WINDOW_WIDTH // 2, 350),
                  settings.GRAY, 16)
        draw_text(screen, "Press ENTER to play again, Esc to quit to menu",
                  (settings.WINDOW_WIDTH // 2, 420),
                  settings.GRAY, 18)

    def draw_wave_intro(self, screen, wave_data, wave_num):
        overlay = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
        overlay.set_alpha(220)
        overlay.fill(settings.BLACK)
        screen.blit(overlay, (0, 0))

        draw_text(screen, f"Wave {wave_num}",
                  (settings.WINDOW_WIDTH // 2, 180),
                  settings.RED, 40)
        draw_text(screen, wave_data["narrative"],
                  (settings.WINDOW_WIDTH // 2, 260),
                  settings.WHITE, 20)
        draw_text(screen, "Press any key to begin",
                  (settings.WINDOW_WIDTH // 2, 360),
                  settings.GRAY, 16)

    def draw_wave_complete(self, screen, wave_data):
        overlay = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(settings.BLACK)
        screen.blit(overlay, (0, 0))

        draw_text(screen, "WAVE COMPLETE",
                  (settings.WINDOW_WIDTH // 2, 180),
                  settings.GREEN, 40)
        draw_text(screen, wave_data["post_narrative"],
                  (settings.WINDOW_WIDTH // 2, 250),
                  settings.WHITE, 20)
        draw_text(screen, "You earned 1 Skill Point!",
                  (settings.WINDOW_WIDTH // 2, 310),
                  settings.GOLD, 22)
        draw_text(screen, "Press Tab to open Skill Tree",
                  (settings.WINDOW_WIDTH // 2, 360),
                  settings.CYAN, 18)
        draw_text(screen, "Press any key to continue",
                  (settings.WINDOW_WIDTH // 2, 400),
                  settings.GRAY, 16)

    def draw_prediction(self, screen, enemy, player, skill_tree, entropy=0):
        if not skill_tree.is_unlocked("derivada"):
            return

        has_bayes = skill_tree.is_unlocked("bayes")
        has_teoria = skill_tree.is_unlocked("teoria_jogos")

        if entropy > settings.HIGH_ENTROPY_THRESHOLD:
            flicker = (entropy - settings.HIGH_ENTROPY_THRESHOLD) / (
                settings.MAX_ENTROPY - settings.HIGH_ENTROPY_THRESHOLD
            )
            if random.random() < flicker * 0.6:
                return

        pred_x, pred_y = enemy.x, enemy.y
        if enemy.type == "bayesian":
            pred = enemy.get_predicted_position(player, 1)
            pred_x, pred_y = pred
        else:
            dx = player.x - enemy.x
            dy = player.y - enemy.y
            dist = max(1, (dx * dx + dy * dy) ** 0.5)
            pred_x = enemy.x + (dx / dist) * 30
            pred_y = enemy.y + (dy / dist) * 30

        if distance((pred_x, pred_y), (player.x, player.y)) < player.size + 8:
            return

        color = settings.GREEN if has_bayes else settings.YELLOW
        alpha = 100
        s = pygame.Surface((12, 12))
        s.set_alpha(alpha)
        s.fill(color)
        screen.blit(s, (pred_x - 6, pred_y - 6))
        pygame.draw.rect(screen, color, (pred_x - 6, pred_y - 6, 12, 12), 1)

        if has_bayes:
            if enemy.type == "bayesian":
                pred2 = enemy.get_predicted_position(player, 2)
            else:
                dx = player.x - enemy.x
                dy = player.y - enemy.y
                dist = max(1, (dx * dx + dy * dy) ** 0.5)
                pred2_x = enemy.x + (dx / dist) * 55
                pred2_y = enemy.y + (dy / dist) * 55

            dist_to_player = distance((enemy.x, enemy.y), (player.x, player.y))
            proximity = max(0, 1.0 - (dist_to_player / enemy.attack_range))
            square_size = int(8 + proximity * 16)

            s2 = pygame.Surface((square_size, square_size))
            s2.set_alpha(80)
            s2.fill(settings.PURPLE)
            screen.blit(s2, (pred2_x - square_size // 2, pred2_y - square_size // 2))
            pygame.draw.rect(screen, settings.PURPLE,
                           (pred2_x - square_size // 2, pred2_y - square_size // 2, square_size, square_size), 1)

        if has_teoria:
            dx = player.x - enemy.x
            dy = player.y - enemy.y
            dist = max(1, (dx * dx + dy * dy) ** 0.5)
            nx = dx / dist
            ny = dy / dist
            line_start = (int(enemy.x + nx * enemy.size),
                         int(enemy.y + ny * enemy.size))
            line_end = (int(player.x - nx * player.size),
                       int(player.y - ny * player.size))
            pygame.draw.line(screen, (255, 215, 0), line_start, line_end, 1)
            target_x = int(player.x + nx * 5)
            target_y = int(player.y + ny * 5)
            pygame.draw.circle(screen, settings.GOLD, (target_x, target_y), 4, 1)

        if has_bayes and distance((enemy.x, enemy.y), (player.x, player.y)) < enemy.attack_range:
            dx = player.x - enemy.x
            dy = player.y - enemy.y
            dist = max(1, (dx * dx + dy * dy) ** 0.5)
            nx = dx / dist
            ny = dy / dist
            line_start = (int(enemy.x + nx * enemy.size),
                         int(enemy.y + ny * enemy.size))
            line_end = (int(player.x - nx * player.size),
                       int(player.y - ny * player.size))
            pygame.draw.line(screen, settings.RED, line_start, line_end, 1)

    def draw_entropy_effects(self, screen, entropy):
        if entropy < settings.HIGH_ENTROPY_THRESHOLD:
            return
        intensity = (entropy - settings.HIGH_ENTROPY_THRESHOLD) / (
            settings.MAX_ENTROPY - settings.HIGH_ENTROPY_THRESHOLD
        )
        if random.random() > intensity:
            return

        for _ in range(int(intensity * 5)):
            y = random.randint(0, settings.WINDOW_HEIGHT)
            x = random.randint(0, settings.WINDOW_WIDTH)
            w = random.randint(10, 80)
            s = pygame.Surface((w, 1))
            alpha = int(80 * intensity)
            s.set_alpha(alpha)
            s.fill((random.choice([settings.RED, settings.PURPLE, settings.CYAN])))
            screen.blit(s, (x, y))

        if random.random() < intensity * 0.3:
            y = random.randint(0, settings.WINDOW_HEIGHT - 10)
            x = random.randint(0, settings.WINDOW_WIDTH - 50)
            s = pygame.Surface((50, 8))
            s.set_alpha(40)
            r = random.choice([settings.RED, settings.PURPLE])
            s.fill(r)
            screen.blit(s, (x, y))
