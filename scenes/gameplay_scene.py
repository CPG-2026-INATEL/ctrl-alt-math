import pygame
import random
import math

import settings
from utils import draw_text, distance, angle_between, resolve_obstacle_collision
from enemy import Enemy
from scenes.scene import Scene


class GameplayScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.state = "WAVE_INTRO"

    def enter(self, prev_scene=None):
        self.state = "WAVE_INTRO"
        if prev_scene and hasattr(prev_scene, "room"):
            room = prev_scene.room
            self.game.current_room = room
            self.game.obstacles = [pygame.Rect(o["x"], o["y"], o["w"], o["h"])
                                   for o in room.obstacles]
            self.game.enemies = []
            for enemy_type, count in room.enemies:
                for _ in range(count):
                    x, y = self._get_spawn_position()
                    enemy = Enemy(x, y, enemy_type)
                    if enemy_type == "boss":
                        enemy.max_hp = room.boss_hp
                        enemy.hp = room.boss_hp
                    self.game.enemies.append(enemy)
        else:
            self.game.obstacles = [pygame.Rect(o["x"], o["y"], o["w"], o["h"])
                                   for o in settings.ARENA_OBSTACLES]

    def _reset_wave_countdown(self):
        self.game.wave_countdown = self.game.wave_countdown_duration

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if self.state == "WAVE_INTRO":
            self.state = "PLAYING"
            self._reset_wave_countdown()
            self.game.sfx.play("wave_start")

        elif self.state == "PLAYING":
            k = event.key
            if k == pygame.K_TAB:
                self.game.scene_manager.push("skill_tree")
            elif k == pygame.K_ESCAPE:
                self.game.scene_manager.push("pause")
            elif k == pygame.K_SPACE:
                if self.game.player.basic_attack():
                    self.game.queue_basic_damage = True
                    self.game.sfx.play("basic_attack")
            elif k == pygame.K_1:
                if self.game.skill_tree.is_unlocked("pitagoras"):
                    if self.game.player.pitagoras_attack():
                        self.game.queue_pitagoras_damage = True
                        self.game.particles.emit(
                            self.game.player.x, self.game.player.y, 15,
                            settings.YELLOW, 100, 0.4, 3
                        )
                        self.game.sfx.play("pitagoras")
            elif k == pygame.K_2:
                if self.game.skill_tree.is_unlocked("reflexao"):
                    if self.game.player.reflexao_attack():
                        self.game.sfx.play("reflexao")
            elif k == pygame.K_r:
                if self.game.skill_tree.is_unlocked("ctrlz"):
                    self._try_rewind()

        elif self.state == "WAVE_COMPLETE":
            if event.key == pygame.K_TAB:
                self.game.scene_manager.push("skill_tree")
            else:
                if self.game.current_room:
                    self.game.world_map.complete_room(
                        (self.game.current_room.col, self.game.current_room.row)
                    )
                    self.game.world_map.save()
                    if self.game.current_room.type == "victory":
                        self.game.scene_manager.switch("victory")
                    else:
                        self.game.scene_manager.switch("map")
                else:
                    self.game.current_wave += 1
                    if self.game.current_wave >= len(settings.WAVES):
                        self.game.scene_manager.switch("victory")
                    else:
                        self.state = "WAVE_INTRO"

    def update(self, dt):
        if self.game.hit_stop_timer > 0:
            self.game.hit_stop_timer -= dt
            if self.game.hit_stop_timer > 0:
                dt = 0
            else:
                self.game.hit_stop_timer = 0

        if self.state == "PLAYING":
            self._update_playing(dt)
        elif self.state in ("WAVE_INTRO", "WAVE_COMPLETE"):
            self.game.particles.update(dt)
            self.game.floating_text.update(dt)

    def _update_playing(self, dt):
        keys = pygame.key.get_pressed()
        self.game.player.update(dt, keys)

        self.game.player.x, self.game.player.y = resolve_obstacle_collision(
            self.game.player.x, self.game.player.y,
            self.game.player.size, self.game.obstacles
        )

        self.game.rewind_cooldown = max(0, self.game.rewind_cooldown - dt)
        self.game.rewind_buffer.record(
            self.game.player, self.game.enemies, self.game.projectiles, dt
        )

        if self.game.wave_countdown > 0:
            self.game.wave_countdown -= dt
            if self.game.wave_countdown <= 0:
                self._spawn_wave(self.game.current_wave)
                self.game.wave_countdown = 0
            self.game.particles.update(dt)
            self.game.floating_text.update(dt)
            return

        self.game.entropy = max(0, self.game.entropy - settings.ENTROPY_DECAY_RATE * dt)

        self._update_enemies(dt)

        for enemy in self.game.enemies:
            if not enemy.dead:
                enemy.x, enemy.y = resolve_obstacle_collision(
                    enemy.x, enemy.y, enemy.size, self.game.obstacles
                )

        self._update_projectiles(dt)
        self.game.particles.update(dt)
        self.game.floating_text.update(dt)

        arena_rect = pygame.Rect(
            settings.ARENA_OFFSET_X, settings.ARENA_OFFSET_Y,
            settings.ARENA_WIDTH, settings.ARENA_HEIGHT
        )
        self.game.math_bg.update(dt, arena_rect)

        self.game.screen_shake = max(0, self.game.screen_shake - dt)
        if self.game.screen_shake > 0:
            self.game.shake_intensity = max(1, self.game.shake_intensity * 0.9)

        self._check_collisions()

        alive = [e for e in self.game.enemies if e.alive and not e.dead]
        if len(alive) == 0 and self.game.wave_countdown <= 0:
            self.game.skill_tree.add_points(1)
            if self.game.current_room and self.game.current_room.type == "victory":
                self.game.scene_manager.switch("victory")
            elif self.game.current_room:
                self.state = "WAVE_COMPLETE"
                self.game.sfx.play("wave_complete")
            else:
                self.game.current_wave += 1
                if self.game.current_wave >= len(settings.WAVES):
                    self.game.scene_manager.switch("victory")
                else:
                    self.state = "WAVE_COMPLETE"
                    self.game.sfx.play("wave_complete")

        if self.game.player.hp <= 0:
            self.game.scene_manager.switch("game_over")

    def _try_rewind(self):
        if self.game.rewind_cooldown > 0:
            return
        if len(self.game.rewind_buffer.buffer) == 0:
            return
        result = self.game.rewind_buffer.rewind()
        if result:
            self.game.prev_scene_name = "gameplay"
            self.game.scene_manager.push("rewind_playback")
            self.game.sfx.play("rewind")

    def _add_hit_stop(self, duration=0.05):
        self.game.hit_stop_timer = duration
        self.game.hit_stop_duration = duration

    def _get_spawn_position(self):
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

    def _spawn_wave(self, wave_idx):
        wave_data = settings.WAVES[wave_idx]
        self.game.enemies = []
        for enemy_type, count in wave_data["enemies"]:
            for _ in range(count):
                x, y = self._get_spawn_position()
                self.game.enemies.append(Enemy(x, y, enemy_type))

    def _update_enemies(self, dt):
        for enemy in list(self.game.enemies):
            if enemy.dead or not enemy.alive:
                continue

            if enemy.type == "boss":
                if enemy.hp < enemy.max_hp * 0.66 and enemy.last_phase == 1:
                    enemy.last_phase = 2
                    self.game.floating_text.add_info(enemy.x, enemy.y, "PHASE II", settings.RED)
                    self.game.sfx.play("boss_phase")
                    self._add_hit_stop(0.1)
                    self.game.screen_shake = 0.15
                    self.game.shake_intensity = 6
                if enemy.hp < enemy.max_hp * 0.33 and enemy.last_phase == 2:
                    enemy.last_phase = 3
                    self.game.floating_text.add_info(enemy.x, enemy.y, "PHASE III", settings.RED)
                    self.game.sfx.play("boss_phase")
                    self._add_hit_stop(0.15)
                    self.game.screen_shake = 0.2
                    self.game.shake_intensity = 8

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
                    self.game.enemies.append(decoy)
                    self.game.particles.emit_burst(
                        decoy.x, decoy.y, settings.COLOR_STRAWMAN, 8, 50, 0.3
                    )

            enemy.update(dt, self.game.player, self.game.projectiles, self.game.entropy)

            if hasattr(enemy, 'area_attack_telegraph') and enemy.area_attack_telegraph > 0:
                enemy.area_attack_telegraph -= dt
                if enemy.area_attack_telegraph <= 0:
                    self._boss_area_attack(enemy)
                    enemy.area_attack_telegraph = 0

            if enemy.dead:
                self.game.particles.emit_burst(
                    enemy.x, enemy.y, enemy.color, 15, 80, 0.4
                )
                self.game.floating_text.add_info(enemy.x, enemy.y, "DESTROYED", settings.GREEN)
                self.game.screen_shake = 0.1
                self.game.shake_intensity = 4
                self.game.sfx.play("enemy_die")

    def _boss_area_attack(self, boss):
        for proj in list(self.game.projectiles):
            if distance((boss.x, boss.y), (proj.x, proj.y)) < 120:
                proj.alive = False
                self.game.particles.emit_burst(proj.x, proj.y, settings.RED, 5, 40, 0.2)
        if distance((boss.x, boss.y), (self.game.player.x, self.game.player.y)) < 120:
            self.game.player.take_damage(boss.damage)
            self.game.particles.emit_burst(
                self.game.player.x, self.game.player.y, settings.RED, 15, 80, 0.4
            )
            self.game.screen_shake = 0.2
            self.game.shake_intensity = 8
            self.game.sfx.play("player_hit")

    def _update_projectiles(self, dt):
        for proj in list(self.game.projectiles):
            proj.update(dt)
            for obs in self.game.obstacles:
                if obs.collidepoint(proj.x, proj.y):
                    proj.alive = False
                    self.game.particles.emit_burst(proj.x, proj.y, settings.WHITE, 5, 30, 0.2)
                    break
            if not proj.alive:
                self.game.projectiles.remove(proj)

    def _check_collisions(self):
        player = self.game.player
        enemies = self.game.enemies

        if self.game.queue_basic_damage:
            self.game.queue_basic_damage = False
            hb = player.get_attack_hitbox()
            for enemy in enemies:
                if not enemy.dead and enemy.get_hitbox().colliderect(hb):
                    enemy.take_damage(settings.PLAYER_ATTACK_DAMAGE)
                    self.game.floating_text.add_damage(enemy.x, enemy.y, settings.PLAYER_ATTACK_DAMAGE)
                    self.game.particles.emit_burst(
                        enemy.x, enemy.y, settings.WHITE, 8, 60, 0.3
                    )
                    self.game.screen_shake = 0.05
                    self.game.shake_intensity = 3
                    self.game.sfx.play("hit")

        if self.game.queue_pitagoras_damage:
            self.game.queue_pitagoras_damage = False
            hb = player.get_pitagoras_hitbox()
            for enemy in enemies:
                if not enemy.dead and enemy.get_hitbox().colliderect(hb):
                    enemy.take_damage(settings.PITAGORAS_DAMAGE)
                    self.game.floating_text.add_damage(enemy.x, enemy.y, settings.PITAGORAS_DAMAGE)
                    self.game.particles.emit_burst(
                        enemy.x, enemy.y, settings.YELLOW, 12, 80, 0.4
                    )
                    self.game.screen_shake = 0.08
                    self.game.shake_intensity = 5
                    self.game.sfx.play("enemy_hit")

        if player.reflexao_active:
            ref_hb = player.get_reflexao_hitbox()
            for enemy in enemies:
                if not enemy.dead and enemy.get_hitbox().colliderect(ref_hb):
                    enemy.take_damage(settings.REFLEXAO_DAMAGE)
                    angle = angle_between((enemy.x, enemy.y), (player.x, player.y))
                    enemy.x += math.cos(angle) * 20
                    enemy.y += math.sin(angle) * 20
                    self.game.floating_text.add_damage(enemy.x, enemy.y, settings.REFLEXAO_DAMAGE)
                    self.game.particles.emit_burst(
                        enemy.x, enemy.y, settings.CYAN, 10, 70, 0.3
                    )
            for proj in list(self.game.projectiles):
                if ref_hb.collidepoint(proj.x, proj.y):
                    proj.reflect()
                    self.game.particles.emit_burst(
                        proj.x, proj.y, settings.CYAN, 8, 50, 0.3
                    )
                    self.game.sfx.play("reflect")

        for proj in list(self.game.projectiles):
            if proj.owner == "enemy":
                if distance((proj.x, proj.y), (player.x, player.y)) < player.size + proj.size:
                    if player.take_damage(proj.damage):
                        self.game.floating_text.add_damage(player.x, player.y, proj.damage)
                        self.game.particles.emit_burst(
                            player.x, player.y, settings.RED, 10, 60, 0.3
                        )
                        self.game.screen_shake = 0.1
                        self.game.shake_intensity = 6
                        self.game.sfx.play("player_hit")
                        self._add_hit_stop(0.06)
                    proj.alive = False

            elif proj.owner == "player":
                for enemy in enemies:
                    if enemy.dead:
                        continue
                    if distance((proj.x, proj.y), (enemy.x, enemy.y)) < enemy.size + proj.size:
                        enemy.take_damage(proj.damage)
                        self.game.floating_text.add_damage(enemy.x, enemy.y, proj.damage)
                        self.game.particles.emit_burst(
                            enemy.x, enemy.y, settings.WHITE, 8, 60, 0.3
                        )
                        proj.alive = False
                        self.game.sfx.play("hit")
                        break

    def draw(self, screen):
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

        for obs in self.game.obstacles:
            pygame.draw.rect(temp, settings.COLOR_OBSTACLE, obs)
            pygame.draw.rect(temp, settings.COLOR_OBSTACLE_BORDER, obs, 1)
            pygame.draw.rect(temp, (50, 50, 80),
                             (obs.x + 2, obs.y + 2, obs.width - 4, obs.height - 4))

        self.game.math_bg.draw(temp)

        for proj in self.game.projectiles:
            proj.draw(temp)

        for enemy in self.game.enemies:
            if not enemy.dead:
                self.game.ui.draw_prediction(
                    temp, enemy, self.game.player,
                    self.game.skill_tree, self.game.entropy
                )

        for enemy in self.game.enemies:
            enemy.draw(temp)

        self.game.player.draw(temp)

        if self.game.queue_pitagoras_damage or self.game.player.pitagoras_cooldown > 0.85:
            hb = self.game.player.get_pitagoras_hitbox()
            s = pygame.Surface((hb.width, hb.height))
            s.set_alpha(80)
            s.fill(settings.YELLOW)
            temp.blit(s, hb)

        self.game.particles.draw(temp)
        self.game.floating_text.draw(temp)

        self.game.ui.draw_entropy_effects(temp, self.game.entropy)

        self.game.ui.draw_hud(
            temp, self.game.player, self.game.current_wave + 1,
            self.game.skill_tree.skill_points, self.game.entropy,
            len(settings.WAVES), self.game
        )

        rewind_available = (self.game.skill_tree.is_unlocked("ctrlz") and
                          self.game.rewind_cooldown <= 0 and
                          len(self.game.rewind_buffer.buffer) > 0)
        if rewind_available:
            draw_text(
                temp, "[R] Rewind Ready",
                (settings.ARENA_OFFSET_X + settings.ARENA_WIDTH // 2,
                 settings.ARENA_OFFSET_Y + settings.ARENA_HEIGHT + 8),
                settings.CYAN, 12
            )

        if self.game.wave_countdown > 0:
            draw_text(temp,
                      f"Wave {self.game.current_wave + 1} begins in {self.game.wave_countdown:.1f}...",
                      (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 - 40),
                      settings.WHITE, 24)

        if self.game.screen_shake > 0:
            sx = random.randint(-int(self.game.shake_intensity),
                                int(self.game.shake_intensity))
            sy = random.randint(-int(self.game.shake_intensity),
                                int(self.game.shake_intensity))
            screen.blit(temp, (sx, sy))
        else:
            screen.blit(temp, (0, 0))

        if self.state == "WAVE_INTRO":
            wave_idx = self.game.current_wave
            if wave_idx >= len(settings.WAVES):
                wave_idx = len(settings.WAVES) - 1
            self.game.ui.draw_wave_intro(
                screen, settings.WAVES[wave_idx],
                self.game.current_wave + 1
            )
        elif self.state == "WAVE_COMPLETE":
            wave_idx = self.game.current_wave
            if wave_idx >= len(settings.WAVES):
                wave_idx = len(settings.WAVES) - 1
            self.game.ui.draw_wave_complete(
                screen, settings.WAVES[wave_idx]
            )
