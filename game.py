import pygame
import sys
import random
import math

import settings
from utils import draw_text, clamp, distance, angle_between, resolve_obstacle_collision
from player import Player
from enemy import Enemy
from projectile import Projectile
from skills import SkillTree
from rewind import RewindBuffer
from particles import ParticleSystem
from ui import UI
from sfx import SFX
from floating_text import FloatingTextSystem
from math_bg import MathBackground
from map import WorldMap
from rewind_fx import RewindEffects


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT)
        )
        pygame.display.set_caption("Ctrl + Alt + Math")
        self.clock = pygame.time.Clock()
        self.running = True

        self.ui = UI()
        self.sfx = SFX()
        self.rewind_fx = RewindEffects()
        self.menu_items = [("START GAME", ""), ("HOW TO PLAY", ""), ("QUIT", "")]
        self.menu_selected = 0

        self._reset_game()

    def _reset_game(self):
        self.state = "MENU"
        self._init_game_state()

    def _init_game_state(self):
        self.player = Player()
        self.skill_tree = SkillTree()
        self.rewind_buffer = RewindBuffer()
        self.particles = ParticleSystem()
        self.enemies = []
        self.projectiles = []
        self.floating_text = FloatingTextSystem()
        self.math_bg = MathBackground()
        self.world_map = WorldMap()
        self.world_map.load()

        self.current_wave = 0
        self.entropy = 0
        self.rewind_cooldown = 0

        self.screen_shake = 0.0
        self.shake_intensity = 0

        self.queue_basic_damage = False
        self.queue_pitagoras_damage = False

        self.prev_state = None

        self.hit_stop_timer = 0
        self.hit_stop_duration = 0

        self.wave_countdown = 0
        self.wave_countdown_duration = 1.5

        self.current_room = None
        self.boss_hp_override = None

        self.rewind_playback_index = 0
        self.rewind_playback_timer = 0

        self.obstacles = [pygame.Rect(o["x"], o["y"], o["w"], o["h"])
                          for o in settings.ARENA_OBSTACLES]

    def start_game(self):
        self._init_game_state()
        self.state = "MAP"

    def get_spawn_position(self):
        side = random.randint(0, 3)
        margin = 30
        ox = settings.ARENA_OFFSET_X
        oy = settings.ARENA_OFFSET_Y
        aw = settings.ARENA_WIDTH
        ah = settings.ARENA_HEIGHT
        if side == 0:
            x = random.randint(ox + margin, ox + aw - margin)
            y = oy + 10
        elif side == 1:
            x = random.randint(ox + margin, ox + aw - margin)
            y = oy + ah - 10
        elif side == 2:
            x = ox + 10
            y = random.randint(oy + margin, oy + ah - margin)
        else:
            x = ox + aw - 10
            y = random.randint(oy + margin, oy + ah - margin)
        return x, y

    def enter_room(self, room):
        self._init_game_state()
        self.current_room = room
        self.obstacles = [pygame.Rect(o["x"], o["y"], o["w"], o["h"])
                          for o in room.obstacles]
        self.state = "WAVE_INTRO"

        self.enemies = []
        for enemy_type, count in room.enemies:
            for _ in range(count):
                x, y = self.get_spawn_position()
                enemy = Enemy(x, y, enemy_type)
                if enemy_type == "boss":
                    enemy.max_hp = room.boss_hp
                    enemy.hp = room.boss_hp
                self.enemies.append(enemy)

    def _add_hit_stop(self, duration=0.05):
        self.hit_stop_timer = duration
        self.hit_stop_duration = duration

    def run(self):
        while self.running:
            dt = self.clock.tick(settings.FPS) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()
        pygame.quit()
        sys.exit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                self._handle_keydown(event)

            if event.type == pygame.MOUSEMOTION and self.state == "SKILL_TREE":
                self.skill_tree.update_hover(event.pos)

            if event.type == pygame.MOUSEBUTTONDOWN and self.state == "SKILL_TREE":
                if event.button == 1:
                    if self.skill_tree.handle_click(event.pos):
                        self.sfx.play("skill_unlock")

    def _handle_keydown(self, event):
        if self.state == "MENU":
            if event.key == pygame.K_UP:
                self.menu_selected = (self.menu_selected - 1) % len(self.menu_items)
                self.sfx.play("menu_select")
            elif event.key == pygame.K_DOWN:
                self.menu_selected = (self.menu_selected + 1) % len(self.menu_items)
                self.sfx.play("menu_select")
            elif event.key == pygame.K_RETURN:
                self.sfx.play("menu_confirm")
                if self.menu_selected == 0:
                    self.start_game()
                elif self.menu_selected == 1:
                    self.state = "HOW_TO_PLAY"
                elif self.menu_selected == 2:
                    self.running = False

        elif self.state == "HOW_TO_PLAY":
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                self.state = "MENU"

        elif self.state == "MAP":
            if event.key == pygame.K_UP:
                self.world_map.navigate("up")
                self.sfx.play("menu_select")
            elif event.key == pygame.K_DOWN:
                self.world_map.navigate("down")
                self.sfx.play("menu_select")
            elif event.key == pygame.K_LEFT:
                self.world_map.navigate("left")
                self.sfx.play("menu_select")
            elif event.key == pygame.K_RIGHT:
                self.world_map.navigate("right")
                self.sfx.play("menu_select")
            elif event.key == pygame.K_RETURN:
                room = self.world_map.select_room()
                if room:
                    self.enter_room(room)
                    self.sfx.play("menu_confirm")
            elif event.key == pygame.K_ESCAPE:
                self.state = "MENU"
                self.sfx.play("menu_select")

        elif self.state == "WAVE_INTRO":
            self.state = "PLAYING"
            self.wave_countdown = self.wave_countdown_duration
            self.sfx.play("wave_start")

        elif self.state == "PLAYING":
            if event.key == pygame.K_TAB:
                self.prev_state = "PLAYING"
                self.state = "SKILL_TREE"
            elif event.key == pygame.K_ESCAPE:
                self.state = "PAUSED"
            elif event.key == pygame.K_SPACE:
                if self.player.basic_attack():
                    self.queue_basic_damage = True
                    self.sfx.play("basic_attack")
            elif event.key == pygame.K_1:
                if self.skill_tree.is_unlocked("pitagoras"):
                    if self.player.pitagoras_attack():
                        self.queue_pitagoras_damage = True
                        self.particles.emit(
                            self.player.x, self.player.y, 15,
                            settings.YELLOW, 100, 0.4, 3
                        )
                        self.sfx.play("pitagoras")
            elif event.key == pygame.K_2:
                if self.skill_tree.is_unlocked("reflexao"):
                    if self.player.reflexao_attack():
                        self.sfx.play("reflexao")
            elif event.key == pygame.K_r:
                if self.skill_tree.is_unlocked("ctrlz"):
                    self._try_rewind()

        elif self.state == "WAVE_COMPLETE":
            if event.key == pygame.K_TAB:
                self.prev_state = "WAVE_COMPLETE"
                self.state = "SKILL_TREE"
            else:
                if self.current_room:
                    self.world_map.complete_room((self.current_room.col, self.current_room.row))
                    self.world_map.save()
                    self.state = "MAP"
                else:
                    self.current_wave += 1
                    if self.current_wave >= len(settings.WAVES):
                        self.state = "VICTORY"
                    else:
                        self.state = "WAVE_INTRO"

        elif self.state == "SKILL_TREE":
            if event.key in (pygame.K_TAB, pygame.K_ESCAPE):
                self.state = self.prev_state or "PLAYING"
                self.prev_state = None

        elif self.state == "PAUSED":
            if event.key == pygame.K_ESCAPE:
                self.state = "PLAYING"
            elif event.key == pygame.K_q:
                self.state = "MENU"
                self.sfx.play("menu_select")

        elif self.state == "GAME_OVER":
            if event.key == pygame.K_RETURN:
                self.start_game()
            elif event.key == pygame.K_ESCAPE:
                self.state = "MENU"
                self.sfx.play("menu_select")

        elif self.state == "VICTORY":
            if event.key == pygame.K_RETURN:
                self.start_game()
            elif event.key == pygame.K_ESCAPE:
                self.state = "MENU"
                self.sfx.play("menu_select")

        elif self.state == "REWIND_PLAYBACK":
            if event.key == pygame.K_ESCAPE:
                self.state = self.prev_state or "PLAYING"
                self.prev_state = None

    def _try_rewind(self):
        if self.rewind_cooldown > 0:
            return
        if len(self.rewind_buffer.buffer) == 0:
            return
        result = self.rewind_buffer.rewind()
        if result:
            self.prev_state = "PLAYING"
            self.state = "REWIND_PLAYBACK"
            self.rewind_playback_index = len(self.rewind_buffer.buffer) - 1
            self.rewind_playback_timer = 0
            self.sfx.play("rewind")

    def _apply_rewind_snapshot(self, snapshot):
        self.player.x = snapshot['player']['x']
        self.player.y = snapshot['player']['y']
        self.player.hp = snapshot['player']['hp']
        self.player.max_hp = snapshot['player']['max_hp']

        restored_enemies = set()
        for e_data in snapshot['enemies']:
            key = (e_data['type'], e_data['x'], e_data['y'])
            restored_enemies.add(key)
            found = False
            for e in self.enemies:
                if e.type == e_data['type'] and not e.dead:
                    e.x = e_data['x']
                    e.y = e_data['y']
                    e.hp = e_data['hp']
                    e.max_hp = e_data['max_hp']
                    found = True
                    break
            if not found:
                new_enemy = Enemy(e_data['x'], e_data['y'], e_data['type'])
                new_enemy.hp = e_data['hp']
                new_enemy.max_hp = e_data['max_hp']
                new_enemy.size = e_data['size']
                new_enemy.color = e_data['color']
                self.enemies.append(new_enemy)

        for e in self.enemies:
            if not e.dead:
                match = False
                for e_data in snapshot['enemies']:
                    if e.type == e_data['type'] and abs(e.x - e_data['x']) < 5 and abs(e.y - e_data['y']) < 5:
                        match = True
                        break
                if not match:
                    e.alive = False
                    e.dead = True

        self.projectiles = []
        for p_data in snapshot['projectiles']:
            proj = Projectile(
                p_data['x'], p_data['y'],
                p_data['vx'], p_data['vy'],
                p_data['damage'], p_data['owner'],
                color=p_data['color'], size=p_data['size']
            )
            self.projectiles.append(proj)

    def _update_rewind_playback(self, dt):
        self.rewind_playback_timer += dt * 4
        step = int(self.rewind_playback_timer * 15)
        target_index = max(0, self.rewind_playback_index - step)

        if target_index <= 0:
            if self.rewind_buffer.buffer:
                self._apply_rewind_snapshot(self.rewind_buffer.buffer[0])
            self.state = self.prev_state or "PLAYING"
            self.prev_state = None
            self.rewind_cooldown = 2.0
            ent_inc = settings.REWIND_ENTROPY_INCREASE
            if self.skill_tree.is_unlocked("entropia"):
                ent_inc *= 0.5
            self.entropy = min(settings.MAX_ENTROPY, self.entropy + ent_inc)
            self.particles.emit_burst(self.player.x, self.player.y, settings.CYAN, 30, 100, 0.6)
            self._add_hit_stop(0.08)
            return

        snapshot = self.rewind_buffer.buffer[target_index]
        self.rewind_playback_index = target_index
        self._apply_rewind_snapshot(snapshot)

    def _update(self, dt):
        if self.hit_stop_timer > 0:
            self.hit_stop_timer -= dt
            dt = 0

        if self.state == "PLAYING":
            self._update_playing(dt)
        elif self.state == "REWIND_PLAYBACK":
            self._update_rewind_playback(dt)
            self.particles.update(dt)
            self.floating_text.update(dt)
        elif self.state == "MAP":
            self.world_map.update(dt)
        elif self.state == "SKILL_TREE":
            self.particles.update(dt)
            self.floating_text.update(dt)
        elif self.state in ("WAVE_INTRO", "WAVE_COMPLETE", "PAUSED"):
            self.particles.update(dt)
            self.floating_text.update(dt)

    def _update_playing(self, dt):
        if self.wave_countdown > 0:
            self.wave_countdown -= dt
            if self.wave_countdown <= 0:
                self.wave_countdown = 0
            self.particles.update(dt)
            self.floating_text.update(dt)
            self.player.update(dt, pygame.key.get_pressed())
            self.player.x, self.player.y = resolve_obstacle_collision(
                self.player.x, self.player.y, self.player.size, self.obstacles
            )
            return

        keys = pygame.key.get_pressed()
        self.player.update(dt, keys)

        self.player.x, self.player.y = resolve_obstacle_collision(
            self.player.x, self.player.y, self.player.size, self.obstacles
        )

        self.rewind_cooldown = max(0, self.rewind_cooldown - dt)
        self.rewind_buffer.record(
            self.player, self.enemies, self.projectiles, dt
        )

        self.entropy = max(0, self.entropy - settings.ENTROPY_DECAY_RATE * dt)

        self._update_enemies(dt)

        for enemy in self.enemies:
            if not enemy.dead:
                enemy.x, enemy.y = resolve_obstacle_collision(
                    enemy.x, enemy.y, enemy.size, self.obstacles
                )

        self._update_projectiles(dt)
        self.particles.update(dt)
        self.floating_text.update(dt)

        arena_rect = pygame.Rect(
            settings.ARENA_OFFSET_X, settings.ARENA_OFFSET_Y,
            settings.ARENA_WIDTH, settings.ARENA_HEIGHT
        )
        self.math_bg.update(dt, arena_rect)

        self.screen_shake = max(0, self.screen_shake - dt)
        if self.screen_shake > 0:
            self.shake_intensity = max(1, self.shake_intensity * 0.9)

        self._check_collisions()

        alive = [e for e in self.enemies if e.alive and not e.dead]
        if len(alive) == 0 and self.wave_countdown <= 0:
            self.skill_tree.add_points(1)
            if self.current_room and self.current_room.type == "victory":
                self.state = "VICTORY"
                self._on_victory()
            elif self.current_room:
                self.state = "WAVE_COMPLETE"
                self.sfx.play("wave_complete")
            else:
                self.current_wave += 1
                if self.current_wave >= len(settings.WAVES):
                    self.state = "VICTORY"
                    self._on_victory()
                else:
                    self.state = "WAVE_COMPLETE"
                    self.sfx.play("wave_complete")

        if self.player.hp <= 0:
            self.state = "GAME_OVER"
            self.sfx.play("game_over")

    def _on_victory(self):
        self.particles.emit_burst(
            settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2,
            settings.GOLD, 50, 150, 1.0
        )
        self.sfx.play("victory")

    def _update_enemies(self, dt):
        for enemy in list(self.enemies):
            if enemy.dead or not enemy.alive:
                continue

            if enemy.type == "boss":
                if enemy.hp < enemy.max_hp * 0.66 and enemy.last_phase == 1:
                    enemy.last_phase = 2
                    self.floating_text.add_info(enemy.x, enemy.y, "PHASE II", settings.RED)
                    self.sfx.play("boss_phase")
                    self._add_hit_stop(0.1)
                    self.screen_shake = 0.15
                    self.shake_intensity = 6
                if enemy.hp < enemy.max_hp * 0.33 and enemy.last_phase == 2:
                    enemy.last_phase = 3
                    self.floating_text.add_info(enemy.x, enemy.y, "PHASE III", settings.RED)
                    self.sfx.play("boss_phase")
                    self._add_hit_stop(0.15)
                    self.screen_shake = 0.2
                    self.shake_intensity = 8

            if enemy.type == "strawman" and not enemy.is_decoy:
                if random.random() < dt * 0.25:
                    decoy = Enemy(
                        enemy.x + random.randint(-30, 30),
                        enemy.y + random.randint(-30, 30),
                        "strawman"
                    )
                    decoy.is_decoy = True
                    decoy.decoy_lifetime = random.uniform(2.0, 4.0)
                    decoy.hp = 5
                    decoy.max_hp = 5
                    decoy.color = (200, 100, 50)
                    decoy.move_per_action = random.randint(15, 35)
                    self.enemies.append(decoy)
                    self.particles.emit_burst(
                        decoy.x, decoy.y, settings.COLOR_STRAWMAN, 8, 50, 0.3
                    )

            enemy.update(dt, self.player, self.projectiles, self.entropy)

            if hasattr(enemy, 'area_attack_telegraph') and enemy.area_attack_telegraph > 0:
                enemy.area_attack_telegraph -= dt
                if enemy.area_attack_telegraph <= 0:
                    self._boss_area_attack(enemy)
                    enemy.area_attack_telegraph = 0

            if enemy.dead:
                self.particles.emit_burst(
                    enemy.x, enemy.y, enemy.color, 15, 80, 0.4
                )
                self.floating_text.add_info(enemy.x, enemy.y, "DESTROYED", settings.GREEN)
                self.screen_shake = 0.1
                self.shake_intensity = 4
                self.sfx.play("enemy_die")

    def _boss_area_attack(self, boss):
        for proj in list(self.projectiles):
            if distance((boss.x, boss.y), (proj.x, proj.y)) < 120:
                proj.alive = False
                self.particles.emit_burst(proj.x, proj.y, settings.RED, 5, 40, 0.2)
        if distance((boss.x, boss.y), (self.player.x, self.player.y)) < 120:
            self.player.take_damage(boss.damage)
            self.particles.emit_burst(
                self.player.x, self.player.y, settings.RED, 15, 80, 0.4
            )
            self.screen_shake = 0.2
            self.shake_intensity = 8
            self.sfx.play("player_hit")

    def _update_projectiles(self, dt):
        for proj in list(self.projectiles):
            proj.update(dt)
            for obs in self.obstacles:
                if obs.collidepoint(proj.x, proj.y):
                    proj.alive = False
                    self.particles.emit_burst(proj.x, proj.y, settings.WHITE, 5, 30, 0.2)
                    break
            if not proj.alive:
                self.projectiles.remove(proj)

    def _check_collisions(self):
        player = self.player
        enemies = self.enemies

        if self.queue_basic_damage:
            self.queue_basic_damage = False
            hb = player.get_attack_hitbox()
            for enemy in enemies:
                if not enemy.dead and enemy.get_hitbox().colliderect(hb):
                    enemy.take_damage(settings.PLAYER_ATTACK_DAMAGE)
                    self.floating_text.add_damage(enemy.x, enemy.y, settings.PLAYER_ATTACK_DAMAGE)
                    self.particles.emit_burst(
                        enemy.x, enemy.y, settings.WHITE, 8, 60, 0.3
                    )
                    self.screen_shake = 0.05
                    self.shake_intensity = 3
                    self.sfx.play("hit")

        if self.queue_pitagoras_damage:
            self.queue_pitagoras_damage = False
            hb = player.get_pitagoras_hitbox()
            for enemy in enemies:
                if not enemy.dead and enemy.get_hitbox().colliderect(hb):
                    enemy.take_damage(settings.PITAGORAS_DAMAGE)
                    self.floating_text.add_damage(enemy.x, enemy.y, settings.PITAGORAS_DAMAGE)
                    self.particles.emit_burst(
                        enemy.x, enemy.y, settings.YELLOW, 12, 80, 0.4
                    )
                    self.screen_shake = 0.08
                    self.shake_intensity = 5
                    self.sfx.play("enemy_hit")

        if player.reflexao_active:
            ref_hb = player.get_reflexao_hitbox()
            for enemy in enemies:
                if not enemy.dead and enemy.get_hitbox().colliderect(ref_hb):
                    enemy.take_damage(settings.REFLEXAO_DAMAGE)
                    angle = angle_between((enemy.x, enemy.y), (player.x, player.y))
                    enemy.x += math.cos(angle) * 20
                    enemy.y += math.sin(angle) * 20
                    self.floating_text.add_damage(enemy.x, enemy.y, settings.REFLEXAO_DAMAGE)
                    self.particles.emit_burst(
                        enemy.x, enemy.y, settings.CYAN, 10, 70, 0.3
                    )
            for proj in list(self.projectiles):
                if ref_hb.collidepoint(proj.x, proj.y):
                    proj.reflect()
                    self.particles.emit_burst(
                        proj.x, proj.y, settings.CYAN, 8, 50, 0.3
                    )
                    self.sfx.play("reflect")

        for proj in list(self.projectiles):
            if proj.owner == "enemy":
                if distance((proj.x, proj.y), (player.x, player.y)) < player.size + proj.size:
                    if player.take_damage(proj.damage):
                        self.floating_text.add_damage(player.x, player.y, proj.damage)
                        self.particles.emit_burst(
                            player.x, player.y, settings.RED, 10, 60, 0.3
                        )
                        self.screen_shake = 0.1
                        self.shake_intensity = 6
                        self.sfx.play("player_hit")
                        self._add_hit_stop(0.06)
                    proj.alive = False

            elif proj.owner == "player":
                for enemy in enemies:
                    if enemy.dead:
                        continue
                    if distance((proj.x, proj.y), (enemy.x, enemy.y)) < enemy.size + proj.size:
                        enemy.take_damage(proj.damage)
                        self.floating_text.add_damage(enemy.x, enemy.y, proj.damage)
                        self.particles.emit_burst(
                            enemy.x, enemy.y, settings.WHITE, 8, 60, 0.3
                        )
                        proj.alive = False
                        self.sfx.play("hit")
                        break

    def _draw(self):
        if self.state == "MENU":
            self.ui.draw_main_menu(self.screen, self.menu_items, self.menu_selected)
        elif self.state == "HOW_TO_PLAY":
            self.ui.draw_how_to_play(self.screen)
        elif self.state == "MAP":
            self.world_map.draw(self.screen)
        elif self.state in ("PLAYING", "WAVE_INTRO", "WAVE_COMPLETE",
                           "PAUSED", "SKILL_TREE", "GAME_OVER", "VICTORY",
                           "REWIND_PLAYBACK"):
            self._draw_game()
            self._draw_overlays()
        pygame.display.flip()

    def _draw_game(self):
        temp = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))

        temp.fill(settings.COLOR_BG)

        arena_rect = pygame.Rect(
            settings.ARENA_OFFSET_X, settings.ARENA_OFFSET_Y,
            settings.ARENA_WIDTH, settings.ARENA_HEIGHT
        )
        pygame.draw.rect(temp, settings.COLOR_ARENA, arena_rect)
        pygame.draw.rect(temp, settings.COLOR_WALL, arena_rect, 2)

        for x in range(settings.ARENA_OFFSET_X + 20,
                       settings.ARENA_OFFSET_X + settings.ARENA_WIDTH, 40):
            for y in range(settings.ARENA_OFFSET_Y + 20,
                           settings.ARENA_OFFSET_Y + settings.ARENA_HEIGHT, 40):
                rect = pygame.Rect(x, y, 20, 20)
                pygame.draw.rect(temp, (18, 18, 42), rect)

        for obs in self.obstacles:
            pygame.draw.rect(temp, settings.COLOR_OBSTACLE, obs)
            pygame.draw.rect(temp, settings.COLOR_OBSTACLE_BORDER, obs, 1)
            pygame.draw.rect(temp, (50, 50, 80),
                             (obs.x + 2, obs.y + 2, obs.width - 4, obs.height - 4))

        self.math_bg.draw(temp)

        for proj in self.projectiles:
            proj.draw(temp)

        for enemy in self.enemies:
            if not enemy.dead:
                self.ui.draw_prediction(
                    temp, enemy, self.player, self.skill_tree, self.entropy
                )

        for enemy in self.enemies:
            enemy.draw(temp)

        self.player.draw(temp)

        if self.queue_pitagoras_damage or self.player.pitagoras_cooldown > 0.85:
            hb = self.player.get_pitagoras_hitbox()
            s = pygame.Surface((hb.width, hb.height))
            s.set_alpha(80)
            s.fill(settings.YELLOW)
            temp.blit(s, hb)

        self.particles.draw(temp)
        self.floating_text.draw(temp)

        self.ui.draw_entropy_effects(temp, self.entropy)

        self.ui.draw_hud(
            temp, self.player, self.current_wave + 1,
            self.skill_tree.skill_points, self.entropy, len(settings.WAVES),
            self
        )

        rewind_available = (self.skill_tree.is_unlocked("ctrlz") and
                          self.rewind_cooldown <= 0 and
                          len(self.rewind_buffer.buffer) > 0)
        if rewind_available:
            draw_text(
                temp, "[R] Rewind Ready",
                (settings.ARENA_OFFSET_X + settings.ARENA_WIDTH // 2,
                 settings.ARENA_OFFSET_Y + settings.ARENA_HEIGHT + 8),
                settings.CYAN, 12
            )

        if self.wave_countdown > 0:
            draw_text(temp, f"Wave {self.current_wave + 1} begins in {self.wave_countdown:.1f}...",
                      (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 - 40),
                      settings.WHITE, 24)

        if self.screen_shake > 0:
            sx = random.randint(-int(self.shake_intensity),
                               int(self.shake_intensity))
            sy = random.randint(-int(self.shake_intensity),
                               int(self.shake_intensity))
            self.screen.blit(temp, (sx, sy))
        else:
            self.screen.blit(temp, (0, 0))

        if self.state == "REWIND_PLAYBACK":
            self.rewind_fx.apply_rewind_fx(self.screen, pygame.time.get_ticks() / 1000.0)

    def _draw_overlays(self):
        if self.state == "WAVE_INTRO":
            self.ui.draw_wave_intro(
                self.screen, settings.WAVES[self.current_wave],
                self.current_wave + 1
            )
        elif self.state == "WAVE_COMPLETE":
            self.ui.draw_wave_complete(
                self.screen, settings.WAVES[self.current_wave]
            )
        elif self.state == "PAUSED":
            self.ui.draw_pause(self.screen)
        elif self.state == "SKILL_TREE":
            self.skill_tree.draw(self.screen)
        elif self.state == "GAME_OVER":
            self.ui.draw_game_over(self.screen, self.current_wave + 1)
        elif self.state == "VICTORY":
            self.ui.draw_victory(self.screen)
