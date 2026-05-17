import pygame
import math
import random
import settings
from utils import draw_text
from i18n import t
from scenes.gameplay_hud import GameplayHUD
from scenes.gameplay_math_renderer import GameplayMathRenderer
from tilemap import TILE_HIGH, TILE_HIGH_EDGE, TILE_LOW, TILE_STAIRS_DOWN, TILE_STAIRS_LEFT, TILE_STAIRS_RIGHT

class GameplayRenderer:
    def __init__(self, scene):
        self.scene = scene
        self.game = scene.game
        self.hud = GameplayHUD(scene, self)
        self.math_renderer = GameplayMathRenderer(scene, self)

    def _draw_derivada_preview(self, screen):
        pc = self.game.player.col
        pr = self.game.player.row

        for enemy in self.game.enemies:
            if enemy.dead:
                continue

            if enemy.type == "boss":
                self.scene.grid.draw_vector_arrow(screen, enemy.col, enemy.row, pc, pr, settings.GREEN, 1)
                continue

            action = enemy.decide_action(pc, pr, self.scene.grid, self.game.enemies)
            if not action:
                continue

            action_type = action.get("type")
            if action_type in ("move", "move_then_attack"):
                tc = action["target_col"]
                tr = action["target_row"]
                color = settings.YELLOW if action_type == "move_then_attack" else settings.GREEN
                self.scene.grid.draw_vector_arrow(screen, enemy.col, enemy.row, tc, tr, color, 2)
                self.scene.grid.draw(screen, highlight_cells=[(tc, tr)], highlight_color=color, highlight_outline=True)
                if action_type == "move_then_attack":
                    self.scene.grid.draw(screen, highlight_cells=[(pc, pr)], highlight_color=settings.GREEN, highlight_outline=True)
            elif action_type in ("attack", "line_attack", "area_attack"):
                self.scene.grid.draw_vector_arrow(screen, enemy.col, enemy.row, pc, pr, settings.GREEN, 1)
                self.scene.grid.draw(screen, highlight_cells=[(pc, pr)], highlight_color=settings.GREEN, highlight_outline=True)

    def draw(self, screen):
        temp = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
        temp.fill(self.game.math_bg.get_bg_color())
        
        world_offset = (-self.scene.camera_x, -self.scene.camera_y)

        arena_rect = pygame.Rect(
            settings.ARENA_OFFSET_X + world_offset[0], 
            settings.ARENA_OFFSET_Y + world_offset[1],
            self.scene.grid.width, 
            self.scene.grid.height
        )

        if self.scene.tilemap:
            scale_x = self.scene.grid.cell_w / self.scene.tilemap.tile_size
            scale_y = self.scene.grid.cell_h / self.scene.tilemap.tile_size
            for row in range(self.scene.tilemap.map_height):
                for col in range(len(self.scene.tilemap.map_data[row])):
                    tile_id = self.scene.tilemap.map_data[row][col]
                    if tile_id < 0:
                        continue
                    ts = self.scene.tilemap.tile_size
                    sx = (tile_id % self.scene.tilemap.tiles_per_row) * ts
                    sy = (tile_id // self.scene.tilemap.tiles_per_row) * ts
                    tile_surf = self.scene.tilemap.tileset.subsurface(sx, sy, ts, ts)
                    rect = self.scene.grid.cell_rect(col, row)
                    rect.x += world_offset[0]
                    rect.y += world_offset[1]
                    scaled_w = rect.width
                    scaled_h = rect.height
                    if scale_x != 1.0 or scale_y != 1.0:
                        tile_surf = pygame.transform.scale(tile_surf, (scaled_w, scaled_h))
                    temp.blit(tile_surf, rect)
            self._draw_high_tile_shadows(temp, world_offset)
        else:
            pygame.draw.rect(temp, self.game.math_bg.get_arena_color(), arena_rect)

        pygame.draw.rect(temp, settings.COLOR_WALL, arena_rect, 2)

        for (col, row) in self.scene.grid.blocked:
            rect = self.scene.grid.cell_rect(col, row)
            rect.x += world_offset[0]
            rect.y += world_offset[1]
            obs_surf = pygame.Surface((int(rect.width), int(rect.height)))
            obs_surf.set_alpha(120)
            obs_surf.fill((20, 20, 40))
            temp.blit(obs_surf, rect)

        self.scene.grid.draw_barriers(temp, offset=world_offset)
        self.game.math_bg.draw(temp, offset=world_offset)

        # Draw math ranges, targets, Bayes heatmaps, Game Theory indicators
        self.math_renderer.draw_math_highlights_and_predictions(temp, world_offset)

        if self.scene.state in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT", "LOCK_INDICATORS", "ENEMY_TURN"):
            self.scene.grid.draw_danger_indicators(temp, pulse_timer=self.scene.cursor_timer, offset=world_offset)
            self.scene.grid.draw_intent_arrows(temp, self.scene.enemy_intents, 
                                        player_skills=self.scene._get_player_skill_ids() if self.scene.state in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT") else None,
                                        offset=world_offset)

        for enemy in self.game.enemies:
            enemy.draw(temp, offset=world_offset)

        for idx, player in enumerate(self.scene.players):
            if player.hp <= 0:
                continue
            player.draw(temp, offset=world_offset)
            if self.scene._is_true_coop():
                px = int(player.x + world_offset[0])
                py = int(player.y + world_offset[1] - player.size - 28)
                label_color = settings.CYAN if idx == 0 else settings.PURPLE
                draw_text(temp, self.scene._player_label(idx), (px, py), label_color, 14)

        cursor_rect = self.scene.grid.cell_rect(self.scene.cursor_col, self.scene.cursor_row)
        cursor_rect.x += world_offset[0]
        cursor_rect.y += world_offset[1]
        cursor_alpha = int(100 + 80 * math.sin(self.scene.cursor_timer * 4))
        s = pygame.Surface((cursor_rect.width, cursor_rect.height))
        s.set_alpha(cursor_alpha)
        s.fill(settings.WHITE)
        temp.blit(s, cursor_rect)
        pygame.draw.rect(temp, settings.WHITE, cursor_rect, 2)

        self.game.particles.draw(temp, offset=world_offset)
        self.game.floating_text.draw(temp, offset=world_offset)

        self.game.ui.draw_entropy_effects(temp, self.game.entropy)
        self.hud.draw_cursor_info(temp)
        self.hud.draw_turn_hud(temp)

        if self.scene.hovered_enemy:
            self.game.ui.draw_enemy_tooltip(temp, self.scene.hovered_enemy, pygame.mouse.get_pos())
        elif self.scene.hovered_intent_data:
            itype, is_fake = self.scene.hovered_intent_data
            self.game.ui.draw_intent_tooltip(temp, itype, is_fake, pygame.mouse.get_pos())

        if self.game.screen_shake > 0:
            sx = random.randint(-int(self.game.shake_intensity),
                                int(self.game.shake_intensity))
            sy = random.randint(-int(self.game.shake_intensity),
                                int(self.game.shake_intensity))
            screen.blit(temp, (sx, sy))
        else:
            screen.blit(temp, (0, 0))

        if self.game.rewind_fx_timer > 0:
            self.game.rewind_fx.apply_rewind_fx(screen, pygame.time.get_ticks() / 1000.0)

        if self.scene.lore_toast:
            self.game.ui.draw_lore_toast(screen, self.scene.lore_toast)

        if self.scene.state == "WAVE_INTRO":
            room = self.game.current_room
            if room:
                draw_text(screen, t(room.name),
                         (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 - 40),
                         settings.CYAN, 28)
                for i, line in enumerate(t(room.narrative).split("\n")):
                    draw_text(screen, line,
                             (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 + i * 24),
                             settings.WHITE, 18)
                draw_text(screen, "Press any key to begin",
                         (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 + 80),
                         settings.GRAY, 14)
            else:
                draw_text(screen, "Press any key to begin",
                         (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2),
                         settings.CYAN, 24)

        elif self.scene.state == "NO_COMBAT":
            room = self.game.current_room
            if room:
                overlay = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
                overlay.set_alpha(180)
                overlay.fill(settings.BLACK)
                screen.blit(overlay, (0, 0))
                draw_text(screen, t(room.name),
                         (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 - 40),
                         settings.CYAN, 32)
                for i, line in enumerate(t(room.narrative).split("\n")):
                    draw_text(screen, line,
                             (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 + i * 24),
                             settings.LIGHT_GRAY, 18)
                draw_text(screen, "Press ENTER to continue",
                         (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 + 80),
                         settings.GREEN, 16)

        if self.scene.state == "GAME_OVER_TRANSITION":
            progress = min(1.0, self.scene.game_over_timer / settings.GAME_OVER_TRANSITION_DURATION)
            fade = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
            fade.set_alpha(int(200 * progress))
            fade.fill(settings.BLACK)
            screen.blit(fade, (0, 0))

    def _draw_high_tile_shadows(self, screen, world_offset):
        high_tiles = {TILE_HIGH, TILE_HIGH_EDGE}
        low_tiles = {TILE_LOW, TILE_STAIRS_DOWN, TILE_STAIRS_LEFT, TILE_STAIRS_RIGHT}

        for (col, row), tile in self.scene.grid.tile_types.items():
            if tile not in high_tiles:
                continue

            for dc, dr, alpha, height_frac in ((0, 1, 70, 0.42), (1, 0, 40, 1.0), (-1, 0, 40, 1.0)):
                neighbor = (col + dc, row + dr)
                if self.scene.grid.tile_types.get(neighbor) not in low_tiles:
                    continue
                rect = self.scene.grid.cell_rect(neighbor[0], neighbor[1])
                rect.x += world_offset[0]
                rect.y += world_offset[1]
                shadow_h = max(4, int(rect.height * height_frac))
                if dr == 1:
                    shadow_rect = pygame.Rect(rect.x, rect.y, rect.width, shadow_h)
                elif dc == 1:
                    shadow_rect = pygame.Rect(rect.x, rect.y, max(4, rect.width // 6), rect.height)
                else:
                    shadow_rect = pygame.Rect(rect.right - max(4, rect.width // 6), rect.y, max(4, rect.width // 6), rect.height)
                shadow = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
                shadow.fill((0, 0, 0, alpha))
                screen.blit(shadow, shadow_rect)

    def _draw_enemy_info(self, screen):
        font = pygame.font.Font(None, 14)
        pc = self.game.player.col
        pr = self.game.player.row

        for enemy in self.game.enemies:
            if enemy.dead:
                continue
            d = self.scene.grid.grid_distance(enemy.col, enemy.row, pc, pr)
            if d <= 6:
                ex, ey = self.scene.grid.to_pixel(enemy.col, enemy.row)
                ex += self.scene.camera_x * -1
                ey += self.scene.camera_y * -1
                type_symbols = {
                    "censor": "NOT",
                    "strawman": "ARG",
                    "bayesian": "P(B|A)",
                    "boss": "BOSS",
                    "ortogonal": "+",
                    "atirador": "AIM",
                    "granadeiro": "3x3",
                }
                symbol = type_symbols.get(enemy.type, "?")
                label = font.render(symbol, True, settings.YELLOW)
                screen.blit(label, (int(ex) - label.get_width() // 2,
                                     int(ey) - enemy.size - 18))

    def _draw_combat_log(self, screen, log_x, log_y):
        if not self.scene.turn_log:
            return

        font = pygame.font.Font(None, 13)
        max_lines = 3
        start_idx = max(0, len(self.scene.turn_log) - max_lines)

        for i, entry in enumerate(self.scene.turn_log[start_idx:start_idx + max_lines]):
            if "CRIT" in entry or "CRITICAL" in entry:
                color = settings.GOLD
            elif "hit" in entry.lower() or "attack" in entry.lower():
                color = settings.RED
            elif "Miss" in entry or "missed" in entry:
                color = settings.GRAY
            elif "moved" in entry:
                color = settings.LIGHT_GRAY
            elif "QED" in entry.upper() or "eliminated" in entry:
                color = settings.GREEN
            else:
                color = (160, 160, 200)

            img = font.render(entry, True, color)
            screen.blit(img, (log_x, log_y + i * 14))

    def _draw_bar_sleek(self, screen, x, y, w, h, pct, fill_color, bg_color):
        pygame.draw.rect(screen, bg_color, (x, y, w, h), border_radius=4)
        if pct > 0:
            filled_w = int(w * min(1.0, pct))
            if filled_w > 0:
                pygame.draw.rect(screen, fill_color, (x, y, filled_w, h), border_radius=4)
                shine_surf = pygame.Surface((filled_w, h // 2), pygame.SRCALPHA)
                shine_surf.fill((255, 255, 255, 40))
                screen.blit(shine_surf, (x, y))
        pygame.draw.rect(screen, (80, 100, 130, 180), (x, y, w, h), 1, border_radius=4)

    def _draw_bar(self, screen, x, y, w, h, pct, fill_color, bg_color):
        pygame.draw.rect(screen, bg_color, (x, y, w, h))
        if pct > 0:
            pygame.draw.rect(screen, fill_color, (x, y, int(w * pct), h))
        pygame.draw.rect(screen, settings.LIGHT_GRAY, (x, y, w, h), 1)
