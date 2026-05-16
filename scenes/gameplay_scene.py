import pygame
import random
import math

import settings
from utils import draw_text, distance, angle_between
from enemy import Enemy
from grid import Grid
from turn_manager import TurnManager
from tilemap import TileMap, MapGenerator
from tilemap import TILE_HOLE, TILE_LOW, TILE_HIGH, TILE_HIGH_EDGE
from tilemap import TILE_STAIRS_UP, TILE_STAIRS_DOWN, TILE_STAIRS_LEFT, TILE_STAIRS_RIGHT
from scenes.scene import Scene


class GameplayScene(Scene):
    TILESET_PATH = "assets/Tileset/tileset_arranged.png"
    TILE_SIZE = 16

    def __init__(self, game):
        super().__init__(game)
        self.state = "WAVE_INTRO"
        self.grid = Grid()
        self.turn_manager = TurnManager()
        self.obstacles_data = settings.ARENA_OBSTACLES
        self.tilemap = None
        self.tile_offset_x = 0
        self.tile_offset_y = 0

        self.cursor_col = 8
        self.cursor_row = 6
        self.cursor_timer = 0

        self.show_move_range = False
        self.show_action_range = False
        self.selected_skill = None

        self.enemy_actions = []
        self.enemy_resolve_idx = 0

        self.victory_timer = 0
        self.qed_position = None

        self.turn_log = []
        self.last_enemy_death_pos = None

        self.pending_player_col = None
        self.pending_player_row = None

    def enter(self, prev_scene=None):
        self.state = "WAVE_INTRO"
        self.turn_manager = TurnManager()
        self.enemy_actions = []
        self.enemy_resolve_idx = 0
        self.victory_timer = 0
        self.show_move_range = False
        self.show_action_range = False
        self.selected_skill = None
        self.turn_log = []

        if prev_scene and hasattr(prev_scene, "room"):
            room = prev_scene.room
            self.game.current_room = room
            self.obstacles_data = room.obstacles
            self.game.obstacles = self.grid.obstacle_rects(room.obstacles)
            self.game.enemies = []
            for enemy_type, count in room.enemies:
                for _ in range(count):
                    ex, ey = self._get_spawn_position()
                    enemy = Enemy(ex, ey, enemy_type)
                    if enemy_type == "boss":
                        enemy.max_hp = room.boss_hp
                        enemy.hp = room.boss_hp
                    self.game.enemies.append(enemy)

            if len(room.enemies) == 0:
                self.state = "NO_COMBAT"
        else:
            self.obstacles_data = settings.ARENA_OBSTACLES
            self.game.obstacles = self.grid.obstacle_rects(settings.ARENA_OBSTACLES)

        self.grid.load_obstacles(self.obstacles_data)

        self._generate_tilemap()

        pcol, prow = self.grid.cols // 2, self.grid.rows - 2
        self.game.player.set_grid_position(pcol, prow, self.grid)
        self.cursor_col = pcol
        self.cursor_row = prow

        for enemy in self.game.enemies:
            if not enemy.dead:
                ec, er = self._find_spawn_grid_cell()
                enemy.set_grid_position(ec, er, self.grid)

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

    def _find_spawn_grid_cell(self):
        side = random.randint(0, 3)
        if side == 0:
            col = random.randint(2, self.grid.cols - 3)
            row = 0
        elif side == 1:
            col = random.randint(2, self.grid.cols - 3)
            row = self.grid.rows - 1
        elif side == 2:
            col = 0
            row = random.randint(2, self.grid.rows - 3)
        else:
            col = self.grid.cols - 1
            row = random.randint(2, self.grid.rows - 3)

        if self.grid.is_blocked(col, row):
            for dc in range(-2, 3):
                for dr in range(-2, 3):
                    nc, nr = col + dc, row + dr
                    if self.grid.is_valid(nc, nr) and not self.grid.is_blocked(nc, nr):
                        return nc, nr
        return col, row

    def _generate_tilemap(self):
        seed = 42
        if self.game.current_room:
            seed = hash((self.game.current_room.col, self.game.current_room.row)) & 0xFFFFFFFF
        gen = MapGenerator(
            width=self.grid.cols,
            height=self.grid.rows,
            hole_density=0.05,
            high_terrain_ratio=0.20,
            high_terrain_count=2,
            stairs_per_area=1,
            seed=seed,
        )
        map_data = gen.generate()

        ALL_STAIRS = {TILE_STAIRS_UP, TILE_STAIRS_DOWN, TILE_STAIRS_LEFT, TILE_STAIRS_RIGHT}
        HIGH_TILES = {TILE_HIGH, TILE_HIGH_EDGE}

        reachable_high = set()
        queue = []
        for r in range(self.grid.rows):
            for c in range(len(map_data[r]) if r < len(map_data) else 0):
                if r < len(map_data) and c < len(map_data[r]):
                    tile = map_data[r][c]
                    self.grid.tile_types[(c, r)] = tile
                    if tile in ALL_STAIRS:
                        queue.append((c, r))
                        reachable_high.add((c, r))

        while queue:
            cx, cy = queue.pop(0)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.grid.cols and 0 <= ny < self.grid.rows:
                    if (nx, ny) not in reachable_high and ny < len(map_data) and nx < len(map_data[ny]):
                        if map_data[ny][nx] in HIGH_TILES:
                            reachable_high.add((nx, ny))
                            queue.append((nx, ny))

        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                if r < len(map_data) and c < len(map_data[r]):
                    tile = map_data[r][c]
                    if tile == TILE_HOLE:
                        self.grid.blocked.add((c, r))
                    elif tile in HIGH_TILES and (c, r) not in reachable_high:
                        self.grid.blocked.add((c, r))

        for col, row in self.grid.blocked:
            if self.grid.is_valid(col, row):
                r_idx = min(row, len(map_data) - 1)
                c_idx = min(col, len(map_data[r_idx]) - 1)
                map_data[r_idx][c_idx] = TILE_HOLE

        try:
            self.tilemap = TileMap(self.TILESET_PATH, tile_size=self.TILE_SIZE)
            self.tilemap.load_from_list(map_data)
        except Exception:
            self.tilemap = None

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if self.state == "WAVE_INTRO":
            self.state = "PLAYER_INPUT"
            self.turn_manager.start_turn()
            self.show_move_range = True
            self.game.sfx.play("wave_start")
            return

        if self.state == "NO_COMBAT":
            if event.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                if self.game.current_room:
                    self.game.world_map.complete_room(
                        (self.game.current_room.col, self.game.current_room.row)
                    )
                    self.game.world_map.save()
                self.game.scene_manager.switch("map")
            return

        if self.state == "PLAYER_INPUT":
            self._handle_player_input(event)
        elif self.state == "PLAYER_ACTION_SELECT":
            self._handle_action_input(event)
        elif self.state == "VICTORY_TRANSITION":
            pass

    def _handle_player_input(self, event):
        k = event.key

        if k == pygame.K_TAB:
            self.game.scene_manager.push("skill_tree")
            return
        elif k == pygame.K_ESCAPE:
            self.game.scene_manager.push("pause")
            return

        if k in (pygame.K_w, pygame.K_UP):
            self.cursor_row = max(0, self.cursor_row - 1)
        elif k in (pygame.K_s, pygame.K_DOWN):
            self.cursor_row = min(self.grid.rows - 1, self.cursor_row + 1)
        elif k in (pygame.K_a, pygame.K_LEFT):
            self.cursor_col = max(0, self.cursor_col - 1)
        elif k in (pygame.K_d, pygame.K_RIGHT):
            self.cursor_col = min(self.grid.cols - 1, self.cursor_col + 1)

        if k in (pygame.K_RETURN, pygame.K_SPACE):
            pc = self.game.player.col
            pr = self.game.player.row
            reachable = self.grid.get_reachable_cells(pc, pr, settings.PLAYER_MOVE_RANGE)

            if (self.cursor_col, self.cursor_row) == (pc, pr):
                self.turn_manager.player_moved = True
                self.state = "PLAYER_ACTION_SELECT"
                self.show_move_range = False
                self.show_action_range = True
                self.game.sfx.play("menu_select")
            elif (self.cursor_col, self.cursor_row) in reachable:
                self.pending_player_col = self.cursor_col
                self.pending_player_row = self.cursor_row
                self.state = "RESOLVE_MOVE"
                self.turn_manager.resolve_timer = 0
                self.turn_manager.resolve_duration = 0.3
                self.game.player.start_move_anim(
                    pc, pr, self.cursor_col, self.cursor_row, self.grid
                )
                self.game.sfx.play("menu_select")
            return

        if k == pygame.K_e and not self.turn_manager.player_moved:
            self.turn_manager.player_moved = True
            self.turn_manager.player_acted = True
            self.show_move_range = False
            self.show_action_range = False
            self.turn_log.append("Wait")
            self._start_enemy_turn()

    def _handle_action_input(self, event):
        k = event.key

        if k == pygame.K_TAB:
            self.game.scene_manager.push("skill_tree")
            return
        elif k == pygame.K_ESCAPE:
            self.game.scene_manager.push("pause")
            return

        if k in (pygame.K_w, pygame.K_UP):
            self.cursor_row = max(0, self.cursor_row - 1)
        elif k in (pygame.K_s, pygame.K_DOWN):
            self.cursor_row = min(self.grid.rows - 1, self.cursor_row + 1)
        elif k in (pygame.K_a, pygame.K_LEFT):
            self.cursor_col = max(0, self.cursor_col - 1)
        elif k in (pygame.K_d, pygame.K_RIGHT):
            self.cursor_col = min(self.grid.cols - 1, self.cursor_col + 1)

        if k == pygame.K_SPACE:
            self._execute_basic_attack()
        elif k == pygame.K_1:
            if self.game.skill_tree.is_unlocked("pitagoras"):
                self.selected_skill = "pitagoras"
                self.show_action_range = True
        elif k == pygame.K_2:
            if self.game.skill_tree.is_unlocked("reflexao"):
                self.selected_skill = "reflexao"
                self.show_action_range = True
        elif k == pygame.K_r:
            if self.game.skill_tree.is_unlocked("ctrlz"):
                self._try_rewind()
        elif k == pygame.K_RETURN:
            if self.selected_skill:
                self._execute_skill()
            else:
                self._execute_basic_attack()
        elif k == pygame.K_e:
            self.turn_manager.player_acted = True
            self.show_action_range = False
            self.selected_skill = None
            self.turn_log.append("Wait")
            self._start_enemy_turn()

    def _execute_basic_attack(self):
        pc = self.game.player.col
        pr = self.game.player.row
        hit_enemies = []
        for enemy in self.game.enemies:
            if enemy.dead:
                continue
            d = self.grid.grid_distance(pc, pr, enemy.col, enemy.row)
            if d <= settings.BASIC_ATTACK_RANGE and not self.grid.is_level_change(pc, pr, enemy.col, enemy.row):
                hit_enemies.append(enemy)

        if hit_enemies:
            is_crit = self.game.player.check_crit()
            for enemy in hit_enemies:
                base_dmg = settings.PLAYER_ATTACK_DAMAGE
                if is_crit:
                    dmg = int(base_dmg * settings.PLAYER_CRIT_MULTIPLIER)
                else:
                    dmg = base_dmg
                dx = abs(enemy.col - pc)
                dy = abs(enemy.row - pr)
                dist_formula = f"d={dx}+{dy}={dx+dy}" if dx + dy < 5 else f"|v|={dx+dy}"
                self.game.floating_text.add_formula(
                    enemy.x, enemy.y - 30,
                    dist_formula, settings.YELLOW if not is_crit else settings.GOLD
                )
                enemy.take_damage(dmg)
                self.game.floating_text.add_enemy_damage(enemy.x, enemy.y, dmg, is_crit)
                self.game.particles.emit_burst(enemy.x, enemy.y, settings.WHITE, 8, 60, 0.3)
                self.game.screen_shake = 0.1 if is_crit else 0.05
                self.game.shake_intensity = 6 if is_crit else 3
                self.game.sfx.play("hit")
                if enemy.dead:
                    self._on_enemy_death(enemy)
            self.turn_log.append(f"Attack{' (CRIT!)' if is_crit else ''}")
        else:
            self.game.floating_text.add_miss(self.game.player.x, self.game.player.y)
            self.turn_log.append("Miss")

        self.turn_manager.player_acted = True
        self.show_action_range = False
        self.selected_skill = None
        self._start_enemy_turn()

    def _execute_skill(self):
        pc = self.game.player.col
        pr = self.game.player.row
        skill = self.selected_skill

        if skill == "pitagoras":
            if not self.game.player.pitagoras_attack():
                return
            range_cells = self.grid.get_cells_in_radius(pc, pr, settings.PITAGORAS_RANGE)
            hit = False
            dx = abs(self.cursor_col - pc)
            dy = abs(self.cursor_row - pr)
            is_crit = self.game.player.check_crit()
            self.game.floating_text.add_formula(
                self.game.player.x, self.game.player.y - 30,
                f"a\u00b2+b\u00b2=c\u00b2  ({dx}\u00b2+{dy}\u00b2={dx*dx+dy*dy})",
                settings.GOLD if is_crit else settings.YELLOW
            )
            for enemy in self.game.enemies:
                if enemy.dead:
                    continue
                if (enemy.col, enemy.row) in range_cells:
                    if not self.grid.is_level_change(pc, pr, enemy.col, enemy.row):
                        dmg = int(settings.PITAGORAS_DAMAGE * settings.PLAYER_CRIT_MULTIPLIER) if is_crit else settings.PITAGORAS_DAMAGE
                        enemy.take_damage(dmg)
                        self.game.floating_text.add_enemy_damage(enemy.x, enemy.y, dmg, is_crit)
                        self.game.particles.emit_burst(enemy.x, enemy.y, settings.YELLOW, 12, 80, 0.4)
                        self.game.screen_shake = 0.12 if is_crit else 0.08
                        self.game.shake_intensity = 7 if is_crit else 5
                        self.game.sfx.play("enemy_hit")
                        hit = True
                        if enemy.dead:
                            self._on_enemy_death(enemy)
                    else:
                        self.game.floating_text.add_evasion(enemy.x, enemy.y)
            self.turn_log.append(f"Pitagoras{' (CRIT!)' if is_crit else ''}" if hit else "Pitagoras Miss")
            self.game.sfx.play("pitagoras")

        elif skill == "reflexao":
            if not self.game.player.reflexao_attack():
                return
            barrier_cells = self.grid.get_cells_in_radius(pc, pr, settings.REFLEXAO_RANGE)
            for col, row in barrier_cells:
                self.grid.mark_barrier(col, row, True)
            self.game.particles.emit_burst(
                self.game.player.x, self.game.player.y, settings.CYAN, 15, 70, 0.3
            )
            self.game.floating_text.add_formula(
                self.game.player.x, self.game.player.y - 30,
                "\u03b8\u1d62=\u03b8\u1d63 (reflection)", settings.CYAN
            )
            self.game.sfx.play("reflexao")
            self.turn_log.append("Reflexao")

        self.turn_manager.player_acted = True
        self.show_action_range = False
        self.selected_skill = None
        self._start_enemy_turn()

    def _try_rewind(self):
        if not self.turn_manager.can_undo():
            return
        gs = self._get_game_state()
        self.turn_manager.snapshot(gs)
        target = self.turn_manager.undo()
        if target is None:
            return

        p = target["player"]
        self.game.player.col = int(p["col"])
        self.game.player.row = int(p["row"])
        self.game.player.hp = p["hp"]
        self.game.player.max_hp = p["max_hp"]
        self.game.player.rigor = p["rigor"]
        self.game.player.set_grid_position(p["col"], p["row"], self.grid)

        self.game.enemies = []
        for e_data in target["enemies"]:
            enemy = Enemy(0, 0, e_data["type"])
            enemy.col = int(e_data["col"])
            enemy.row = int(e_data["row"])
            enemy.hp = e_data["hp"]
            enemy.max_hp = e_data["max_hp"]
            enemy.alive = e_data["alive"]
            enemy.dead = e_data["dead"]
            enemy.size = e_data["size"]
            enemy.color = e_data["color"]
            enemy.set_grid_position(e_data["col"], e_data["row"], self.grid)
            self.game.enemies.append(enemy)

        if "barrier_cells" in target:
            self.grid.barrier_cells = set(
                (int(c), int(r)) for c, r in target["barrier_cells"]
            )

        self.game.entropy = target["entropy"]
        self.game.particles.emit_burst(
            self.game.player.x, self.game.player.y, settings.CYAN, 30, 100, 0.6
        )
        self.game.sfx.play("rewind")
        self.state = "PLAYER_INPUT"
        self.turn_manager.start_turn()
        self.show_move_range = True
        self.show_action_range = False
        self.selected_skill = None
        self.cursor_col = int(p["col"])
        self.cursor_row = int(p["row"])

    def _on_enemy_death(self, enemy):
        self.game.floating_text.add_formula(
            enemy.x, enemy.y,
            "\u2203=0 (eliminated)", settings.GREEN
        )
        self.game.particles.emit_burst(enemy.x, enemy.y, enemy.color, 15, 80, 0.4)
        self.game.floating_text.add_info(enemy.x, enemy.y, "QED", settings.GREEN)
        self.game.screen_shake = 0.1
        self.game.shake_intensity = 4
        self.game.sfx.play("enemy_die")
        self.last_enemy_death_pos = (enemy.x, enemy.y)
        self._check_victory()

    def _check_victory(self):
        alive = [e for e in self.game.enemies if not e.dead]
        if len(alive) == 0 and self.state != "VICTORY_TRANSITION":
            self.state = "VICTORY_TRANSITION"
            self.victory_timer = 0
            pos = self.last_enemy_death_pos or (self.game.player.x, self.game.player.y)
            self.game.particles.emit_burst(pos[0], pos[1], settings.GOLD, 30, 100, 0.8)

    def _start_enemy_turn(self):
        if self.state == "VICTORY_TRANSITION":
            return
        self.state = "ENEMY_TURN"
        self.enemy_actions = []
        self.enemy_resolve_idx = 0

        pc = self.game.player.col
        pr = self.game.player.row
        alive_enemies = [e for e in self.game.enemies if not e.dead]

        for enemy in alive_enemies:
            action = enemy.decide_action(pc, pr, self.grid, self.game.enemies)
            if action:
                self.enemy_actions.append((enemy, action))

    def update(self, dt):
        self.cursor_timer += dt
        self.game.player.update_animation(dt, self.grid)
        self.game.player.update(dt, {})

        for enemy in self.game.enemies:
            enemy.update_animation(dt, self.grid)
            enemy.bob_phase += dt * 3
            enemy.spawn_timer = max(0, enemy.spawn_timer - dt)
            enemy.flash_timer = max(0, enemy.flash_timer - dt)
            if enemy.type == "boss":
                enemy.pulse_timer += dt * 2

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

        if self.state == "RESOLVE_MOVE":
            self.turn_manager.resolve_timer += dt
            if self.turn_manager.resolve_timer >= self.turn_manager.resolve_duration:
                if self.pending_player_col is not None:
                    self.game.player.col = self.pending_player_col
                    self.game.player.row = self.pending_player_row
                    self.game.player.x, self.game.player.y = self.grid.to_pixel(
                        self.pending_player_col, self.pending_player_row
                    )
                    self.pending_player_col = None
                    self.pending_player_row = None
                self.turn_manager.player_moved = True
                self.state = "PLAYER_ACTION_SELECT"
                self.show_move_range = False
                self.show_action_range = True

        elif self.state == "RESOLVE_ACTION":
            self.turn_manager.resolve_timer += dt
            if self.turn_manager.resolve_timer >= self.turn_manager.resolve_duration:
                self.state = "ENEMY_TURN"
                self._start_enemy_turn()

        elif self.state == "ENEMY_TURN":
            self._resolve_enemy_turn(dt)

        elif self.state == "TURN_END":
            self._end_turn()

        elif self.state == "VICTORY_TRANSITION":
            self.victory_timer += dt
            if self.victory_timer >= settings.VICTORY_TRANSITION_DURATION:
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
                    self.game.scene_manager.switch("victory")

        if self.state == "PLAYER_INPUT" or self.state == "PLAYER_ACTION_SELECT":
            self.game.entropy = min(settings.MAX_ENTROPY,
                                    self.game.entropy + settings.ENTROPY_PER_TURN * dt * 0.1)

    def _resolve_enemy_turn(self, dt):
        if self.enemy_resolve_idx >= len(self.enemy_actions):
            self.state = "TURN_END"
            return

        if self.game.player.hp <= 0:
            self.state = "TURN_END"
            return

        enemy, action = self.enemy_actions[self.enemy_resolve_idx]
        if enemy.dead:
            self.enemy_resolve_idx += 1
            return

        self.turn_manager.resolve_timer += dt
        if self.turn_manager.resolve_timer < 0.15:
            return

        self.turn_manager.resolve_timer = 0

        if action["type"] == "wait":
            self.turn_log.append(f"{enemy.type} waits")
        elif action["type"] == "move":
            tc, tr = action["target_col"], action["target_row"]
            if self.grid.is_valid(tc, tr) and not self.grid.is_blocked(tc, tr):
                if not self.grid.is_level_change(enemy.col, enemy.row, tc, tr):
                    old_col, old_row = enemy.col, enemy.row
                    enemy.start_move_anim(old_col, old_row, tc, tr, self.grid)
                    enemy.col = tc
                    enemy.row = tr
                    enemy.x, enemy.y = self.grid.to_pixel(tc, tr)
                    self.turn_log.append(f"{enemy.type} moved")
                else:
                    self.turn_log.append(f"{enemy.type} can't reach")
            else:
                self.turn_log.append(f"{enemy.type} blocked")

        elif action["type"] == "move_then_attack":
            tc, tr = action["target_col"], action["target_row"]
            if self.grid.is_valid(tc, tr) and not self.grid.is_blocked(tc, tr):
                if not self.grid.is_level_change(enemy.col, enemy.row, tc, tr):
                    enemy.start_move_anim(enemy.col, enemy.row, tc, tr, self.grid)
                    enemy.col = tc
                    enemy.row = tr
                    enemy.x, enemy.y = self.grid.to_pixel(tc, tr)
                    self._enemy_attack(enemy)
                else:
                    self._enemy_attack(enemy)

        elif action["type"] == "attack":
            self._enemy_attack(enemy)

        elif action["type"] == "line_attack":
            self._enemy_line_attack(enemy, action)

        elif action["type"] == "area_attack":
            self._enemy_area_attack(enemy, action)

        self.enemy_resolve_idx += 1

    def _enemy_attack(self, enemy):
        pc = self.game.player.col
        pr = self.game.player.row
        d = self.grid.grid_distance(enemy.col, enemy.row, pc, pr)

        if d <= enemy.attack_range and not self.grid.is_level_change(enemy.col, enemy.row, pc, pr):
            dmg = enemy.roll_damage()
            dx = abs(pc - enemy.col)
            dy = abs(pr - enemy.row)
            if self.game.player.take_damage(dmg):
                self.game.floating_text.add_damage(self.game.player.x, self.game.player.y, dmg, enemy.last_crit)
                self.game.particles.emit_burst(self.game.player.x, self.game.player.y, settings.RED, 10, 60, 0.3)
                self.game.screen_shake = 0.15 if enemy.last_crit else 0.1
                self.game.shake_intensity = 8 if enemy.last_crit else 6
                self.game.sfx.play("player_hit")
                if enemy.last_crit:
                    self.game.floating_text.add_formula(
                        self.game.player.x, self.game.player.y + 15,
                        f"CRITICAL! ({dx}+{dy}={dx+dy})", settings.ORANGE
                    )
                self.turn_log.append(f"{enemy.type} hit for {dmg}{' (CRIT!)' if enemy.last_crit else ''}")
            else:
                self.game.floating_text.add_blocked(self.game.player.x, self.game.player.y)
                self.turn_log.append(f"{enemy.type} attacked (blocked)")
        elif d <= enemy.attack_range:
            self.game.floating_text.add_evasion(enemy.x, enemy.y)
            self.turn_log.append(f"{enemy.type} can't reach (elevation)")
        else:
            self.turn_log.append(f"{enemy.type} attack missed")

    def _enemy_line_attack(self, enemy, action):
        tc, tr = action["target_col"], action["target_row"]
        dc = tc - enemy.col
        dr = tr - enemy.row
        if dc == 0 and dr == 0:
            return
        steps = max(abs(dc), abs(dr))
        step_dc = 1 if dc > 0 else (-1 if dc < 0 else 0)
        step_dr = 1 if dr > 0 else (-1 if dr < 0 else 0)

        phase = 1
        if enemy.hp < enemy.max_hp * 0.33:
            phase = 3
        elif enemy.hp < enemy.max_hp * 0.66:
            phase = 2

        count = 3 if phase >= 3 else 2 if phase >= 2 else 1
        dmg = enemy.roll_damage()
        self.game.floating_text.add_formula(
            enemy.x, enemy.y - 30,
            f"Phase {['I','II','III'][phase-1]} \u2192 ||v||={count}",
            settings.ORANGE
        )

        for i in range(count):
            offset = i - (count - 1) // 2
            c = enemy.col + step_dc * settings.BOSS_ATTACK_RANGE
            r = enemy.row + step_dr * settings.BOSS_ATTACK_RANGE + offset
            c = max(0, min(self.grid.cols - 1, c))
            r = max(0, min(self.grid.rows - 1, r))

            if c == self.game.player.col and r == self.game.player.row:
                if self.game.player.take_damage(dmg):
                    self.game.floating_text.add_damage(self.game.player.x, self.game.player.y, dmg, enemy.last_crit)
                    self.game.particles.emit_burst(self.game.player.x, self.game.player.y, settings.RED, 10, 60, 0.3)
                    self.game.screen_shake = 0.15
                    self.game.shake_intensity = 6
                    self.game.sfx.play("player_hit")
                    self.turn_log.append(f"Boss line attack hit for {dmg}!")

        self.game.particles.emit_burst(enemy.x, enemy.y, (255, 100, 100), 10, 50, 0.3)
        self.game.sfx.play("pitagoras")
        self.turn_log.append(f"Boss line attack")

    def _enemy_area_attack(self, enemy, action):
        tc, tr = action["target_col"], action["target_row"]
        radius = 2
        dmg = enemy.roll_damage()
        hit = False
        self.game.floating_text.add_formula(
            enemy.x, enemy.y - 30,
            f"\u222b dA  r={radius}", settings.RED
        )
        for col in range(tc - radius, tc + radius + 1):
            for row in range(tr - radius, tr + radius + 1):
                if col == self.game.player.col and row == self.game.player.row:
                    if self.game.player.take_damage(dmg):
                        self.game.floating_text.add_damage(self.game.player.x, self.game.player.y, dmg, enemy.last_crit)
                        self.game.particles.emit_burst(self.game.player.x, self.game.player.y, settings.RED, 10, 60, 0.3)
                        self.game.screen_shake = 0.15
                        self.game.shake_intensity = 6
                        self.game.sfx.play("player_hit")
                        hit = True
                        self.turn_log.append(f"Boss AoE hit for {dmg}!")

        cx, cy = self.grid.to_pixel(tc, tr)
        self.game.particles.emit_burst(cx, cy, settings.RED, 20, 80, 0.4)
        self.game.sfx.play("boss_phase")
        if not hit:
            self.turn_log.append(f"Boss AoE missed")

    def _end_turn(self):
        gs = self._get_game_state()
        self.turn_manager.end_turn(gs)

        self.game.player.rigor = min(
            self.game.player.max_rigor,
            self.game.player.rigor + settings.RIGOR_REGEN_RATE
        )
        self.game.floating_text.add_rigor(
            self.game.player.x, self.game.player.y - 20,
            settings.RIGOR_REGEN_RATE
        )
        self.grid.clear_barriers()

        alive = [e for e in self.game.enemies if not e.dead]
        if len(alive) == 0:
            self.state = "VICTORY_TRANSITION"
            self.victory_timer = 0
            self.game.particles.emit_burst(
                self.last_enemy_death_pos[0] if self.last_enemy_death_pos else self.game.player.x,
                self.last_enemy_death_pos[1] if self.last_enemy_death_pos else self.game.player.y,
                settings.GOLD, 30, 100, 0.8
            )
            return

        if self.game.player.hp <= 0:
            self.game.scene_manager.switch("game_over")
            return

        self.state = "PLAYER_INPUT"
        self.turn_manager.start_turn()
        self.show_move_range = True
        self.show_action_range = False
        self.selected_skill = None

    def _get_game_state(self):
        return {
            "player_col": self.game.player.col,
            "player_row": self.game.player.row,
            "player_hp": self.game.player.hp,
            "player_max_hp": self.game.player.max_hp,
            "player_rigor": self.game.player.rigor,
            "enemies": self.game.enemies,
            "entropy": self.game.entropy,
            "barrier_cells": self.grid.barrier_cells.copy(),
        }

    def draw(self, screen):
        temp = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
        temp.fill(settings.COLOR_BG)

        arena_rect = pygame.Rect(
            settings.ARENA_OFFSET_X, settings.ARENA_OFFSET_Y,
            settings.ARENA_WIDTH, settings.ARENA_HEIGHT
        )

        if self.tilemap:
            scale_x = self.grid.cell_w / self.tilemap.tile_size
            scale_y = self.grid.cell_h / self.tilemap.tile_size
            for row in range(self.tilemap.map_height):
                for col in range(len(self.tilemap.map_data[row])):
                    tile_id = self.tilemap.map_data[row][col]
                    if tile_id < 0:
                        continue
                    ts = self.tilemap.tile_size
                    sx = (tile_id % self.tilemap.tiles_per_row) * ts
                    sy = (tile_id // self.tilemap.tiles_per_row) * ts
                    tile_surf = self.tilemap.tileset.subsurface(sx, sy, ts, ts)
                    scaled_w = int(self.grid.cell_w)
                    scaled_h = int(self.grid.cell_h)
                    if scale_x != 1.0 or scale_y != 1.0:
                        tile_surf = pygame.transform.scale(tile_surf, (scaled_w, scaled_h))
                    dx = settings.ARENA_OFFSET_X + col * scaled_w
                    dy = settings.ARENA_OFFSET_Y + row * scaled_h
                    temp.blit(tile_surf, (dx, dy))
        else:
            pygame.draw.rect(temp, settings.COLOR_ARENA, arena_rect)

        pygame.draw.rect(temp, settings.COLOR_WALL, arena_rect, 2)

        for (col, row) in self.grid.blocked:
            rect = self.grid.cell_rect(col, row)
            obs_surf = pygame.Surface((int(rect.width), int(rect.height)))
            obs_surf.set_alpha(120)
            obs_surf.fill((20, 20, 40))
            temp.blit(obs_surf, rect)

        self.grid.draw(temp, show_grid=True, grid_color=(25, 25, 50))
        self.grid.draw_barriers(temp)

        self.game.math_bg.draw(temp)

        if self.state == "PLAYER_INPUT" and self.show_move_range:
            pc = self.game.player.col
            pr = self.game.player.row
            reachable = self.grid.get_reachable_cells(pc, pr, settings.PLAYER_MOVE_RANGE)
            self.grid.draw(temp, highlight_cells=reachable, highlight_color=settings.BLUE)

        if self.state == "PLAYER_ACTION_SELECT" and self.show_action_range:
            if self.selected_skill == "pitagoras":
                cells = self.grid.get_cells_in_radius(
                    self.game.player.col, self.game.player.row,
                    settings.PITAGORAS_RANGE
                )
                self.grid.draw(temp, highlight_cells=cells, highlight_color=settings.YELLOW)
                self.grid.draw_triangle(temp,
                    self.game.player.col, self.game.player.row,
                    self.cursor_col, self.game.player.row,
                    self.cursor_col, self.cursor_row,
                    settings.YELLOW, 1)
            elif self.selected_skill == "reflexao":
                cells = self.grid.get_cells_in_radius(
                    self.game.player.col, self.game.player.row,
                    settings.REFLEXAO_RANGE
                )
                self.grid.draw(temp, highlight_cells=cells, highlight_color=settings.CYAN)
            else:
                cells = self.grid.get_cells_in_range(
                    self.game.player.col, self.game.player.row,
                    settings.BASIC_ATTACK_RANGE
                )
                self.grid.draw(temp, highlight_cells=cells, highlight_color=settings.RED)

        if self.game.skill_tree.is_unlocked("derivada"):
            for enemy in self.game.enemies:
                if enemy.dead:
                    continue
                if enemy.type == "bayesian":
                    pred = enemy.get_predicted_grid_position(
                        self.game.player.col, self.game.player.row, self.grid
                    )
                    px, py = self.grid.to_pixel(pred[0], pred[1])
                    self.grid.draw_vector_arrow(temp, enemy.col, enemy.row,
                                               pred[0], pred[1], settings.GREEN, 2)
                else:
                    dc = self.game.player.col - enemy.col
                    dr = self.game.player.row - enemy.row
                    if dc != 0 or dr != 0:
                        length = math.sqrt(dc * dc + dr * dr)
                        ndc = dc / length
                        ndr = dr / length
                        end_c = enemy.col + ndc * 1.5
                        end_r = enemy.row + ndr * 1.5
                        self.grid.draw_vector_arrow(temp, enemy.col, enemy.row,
                                                   int(end_c), int(end_r), settings.GREEN, 1)

        if self.game.skill_tree.is_unlocked("bayes"):
            pc = self.game.player.col
            pr = self.game.player.row
            for enemy in self.game.enemies:
                if enemy.dead:
                    continue
                dist = self.grid.grid_distance(enemy.col, enemy.row, pc, pr)
                max_dist = enemy.attack_range
                if max_dist > 0 and dist <= max_dist:
                    proximity = 1.0 - (dist / max_dist)
                    intensity = int(40 + proximity * 60)
                    cells = self.grid.get_cells_in_radius(enemy.col, enemy.row, 2)
                    for col, row in cells:
                        rect = self.grid.cell_rect(col, row)
                        s = pygame.Surface((rect.width, rect.height))
                        s.set_alpha(intensity // 3)
                        s.fill(settings.PURPLE)
                        temp.blit(s, rect)

        if self.game.skill_tree.is_unlocked("teoria_jogos"):
            pc = self.game.player.col
            pr = self.game.player.row
            for enemy in self.game.enemies:
                if enemy.dead:
                    continue
                if self.grid.grid_distance(enemy.col, enemy.row, pc, pr) <= enemy.attack_range:
                    self.grid.draw_vector_arrow(temp, enemy.col, enemy.row,
                                               pc, pr, settings.GOLD, 1)

        for enemy in self.game.enemies:
            enemy.draw(temp)

        self.game.player.draw(temp)

        cursor_rect = self.grid.cell_rect(self.cursor_col, self.cursor_row)
        cursor_alpha = int(100 + 80 * math.sin(self.cursor_timer * 4))
        s = pygame.Surface((cursor_rect.width, cursor_rect.height))
        s.set_alpha(cursor_alpha)
        s.fill(settings.WHITE)
        temp.blit(s, cursor_rect)
        pygame.draw.rect(temp, settings.WHITE, cursor_rect, 2)

        self.game.particles.draw(temp)
        self.game.floating_text.draw(temp)

        self._draw_cursor_info(temp)
        self._draw_enemy_info(temp)

        self._draw_turn_hud(temp)

        if self.game.screen_shake > 0:
            sx = random.randint(-int(self.game.shake_intensity),
                                int(self.game.shake_intensity))
            sy = random.randint(-int(self.game.shake_intensity),
                                int(self.game.shake_intensity))
            screen.blit(temp, (sx, sy))
        else:
            screen.blit(temp, (0, 0))

        if self.state == "WAVE_INTRO":
            room = self.game.current_room
            if room:
                draw_text(screen, room.name,
                         (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 - 40),
                         settings.CYAN, 28)
                for i, line in enumerate(room.narrative.split("\n")):
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

        elif self.state == "NO_COMBAT":
            room = self.game.current_room
            if room:
                overlay = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
                overlay.set_alpha(180)
                overlay.fill(settings.BLACK)
                screen.blit(overlay, (0, 0))
                draw_text(screen, room.name,
                         (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 - 40),
                         settings.CYAN, 32)
                for i, line in enumerate(room.narrative.split("\n")):
                    draw_text(screen, line,
                             (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 + i * 24),
                             settings.LIGHT_GRAY, 18)
                draw_text(screen, "Press ENTER to continue",
                         (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 + 80),
                         settings.GREEN, 16)

    def _draw_cursor_info(self, screen):
        if self.state not in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT"):
            return

        pc = self.game.player.col
        pr = self.game.player.row
        cc = self.cursor_col
        cr = self.cursor_row
        dx = cc - pc
        dy = cr - pr
        dist = abs(dx) + abs(dy)
        eucl = math.sqrt(dx * dx + dy * dy)

        info_x = settings.ARENA_OFFSET_X + settings.ARENA_WIDTH + 5
        if info_x + 180 > settings.WINDOW_WIDTH:
            info_x = settings.WINDOW_WIDTH - 180

        font = pygame.font.Font(None, 16)
        info_y = settings.ARENA_OFFSET_Y + 5

        label_color = settings.CYAN
        value_color = settings.WHITE

        lines = [
            (f"v = ({dx:+d}, {dy:+d})", label_color),
            (f"|v| = {dist}", value_color),
        ]

        if dist > 0:
            lines.append((f"||v|| = {eucl:.2f}", settings.YELLOW))

        tile_type = self.grid.tile_types.get((cc, cr), 0)
        tile_name = "LOW"
        if tile_type == -1:
            tile_name = "HOLE"
        elif tile_type in (16, 61):
            tile_name = "HIGH"
        elif tile_type in (27, 11, 25, 24):
            tile_name = "STAIRS"
        lines.append((f"Tile: {tile_name}", settings.LIGHT_GRAY))

        reachable = self.grid.get_reachable_cells(pc, pr, settings.PLAYER_MOVE_RANGE)
        if (cc, cr) in reachable or (cc, cr) == (pc, pr):
            can_reach = True
        else:
            can_reach = False
        lines.append(("Reachable" if can_reach else "Blocked",
                       settings.GREEN if can_reach else settings.RED))

        for text, color in lines:
            img = font.render(text, True, color)
            screen.blit(img, (info_x, info_y))
            info_y += 16

        tilted_font = pygame.font.Font(None, 13)
        if self.state == "PLAYER_INPUT" and self.show_move_range and (cc, cr) in reachable:
            move_label = tilted_font.render(f"\u0394pos({dx:+d},{dy:+d}) d={dist}", True, settings.BLUE)
            screen.blit(move_label, (info_x, info_y + 4))

        if self.state == "PLAYER_ACTION_SELECT":
            if self.selected_skill == "pitagoras":
                eucl_dist = math.sqrt(dx * dx + dy * dy)
                skill_label = tilted_font.render(
                    f"a\u00b2+b\u00b2=c\u00b2  c={eucl_dist:.1f}", True, settings.YELLOW)
                screen.blit(skill_label, (info_x, info_y + 4))
            elif self.selected_skill == "reflexao":
                skill_label = tilted_font.render(
                    "\u03b8\u1d62=\u03b8\u1d63 (reflect)", True, settings.CYAN)
                screen.blit(skill_label, (info_x, info_y + 4))

    def _draw_enemy_info(self, screen):
        font = pygame.font.Font(None, 14)
        pc = self.game.player.col
        pr = self.game.player.row

        for enemy in self.game.enemies:
            if enemy.dead:
                continue
            d = self.grid.grid_distance(enemy.col, enemy.row, pc, pr)
            if d <= 6:
                ex, ey = self.grid.to_pixel(enemy.col, enemy.row)
                type_symbols = {
                    "censor": "\u00acP",
                    "strawman": "A\u2192?",
                    "bayesian": "P(B|A)",
                    "boss": "\u2203!",
                }
                symbol = type_symbols.get(enemy.type, "?")
                hp_text = f"{enemy.hp}/{enemy.max_hp}"
                label = font.render(symbol, True, settings.YELLOW)
                screen.blit(label, (int(ex) - label.get_width() // 2,
                                     int(ey) - enemy.size - 18))

    def _draw_combat_log(self, screen, log_y):
        if not self.turn_log:
            return

        font = pygame.font.Font(None, 14)
        max_lines = 4
        start_idx = max(0, len(self.turn_log) - max_lines)
        x = settings.UI_PADDING + 360

        for i, entry in enumerate(self.turn_log[start_idx:start_idx + max_lines]):
            alpha = int(180 + 75 * (i / max_lines))
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
            screen.blit(img, (x, log_y + i * 14))

    def _draw_turn_hud(self, screen):
        bar_y = settings.WINDOW_HEIGHT - settings.UI_BAR_HEIGHT
        pygame.draw.rect(screen, settings.DARK_GRAY,
                         (0, bar_y, settings.WINDOW_WIDTH, settings.UI_BAR_HEIGHT))
        pygame.draw.line(screen, settings.GRAY, (0, bar_y),
                         (settings.WINDOW_WIDTH, bar_y), 1)

        hp_pct = self.game.player.hp / self.game.player.max_hp
        rigor_pct = self.game.player.rigor / self.game.player.max_rigor
        entropy_pct = self.game.entropy / settings.MAX_ENTROPY

        hp_color = settings.RED if hp_pct > 0.5 else settings.ORANGE if hp_pct > 0.25 else settings.RED
        self._draw_bar(screen, settings.UI_PADDING, bar_y + 8, 160, 14,
                       hp_pct, hp_color, (60, 20, 20))
        hp_text = f"HP: {self.game.player.hp}/{self.game.player.max_hp}"
        draw_text(screen, hp_text,
                  (settings.UI_PADDING + 80, bar_y + 15),
                  settings.WHITE, 14)

        self._draw_bar(screen, settings.UI_PADDING, bar_y + 26, 160, 14,
                       rigor_pct, settings.BLUE, (20, 20, 60))
        draw_text(screen, f"Rigor: {self.game.player.rigor:.0f}/{self.game.player.max_rigor}",
                  (settings.UI_PADDING + 80, bar_y + 33),
                  settings.WHITE, 14)

        self._draw_bar(screen, settings.UI_PADDING + 180, bar_y + 8, 120, 14,
                       entropy_pct, settings.COLOR_ENTROPY_BAR, (40, 10, 40))
        draw_text(screen, f"S: {self.game.entropy:.0f}",
                  (settings.UI_PADDING + 240, bar_y + 15),
                  settings.WHITE, 14)

        crit_pct = int(settings.PLAYER_CRIT_CHANCE * 100)
        font_small = pygame.font.Font(None, 12)
        crit_label = font_small.render(f"CRIT: {crit_pct}%  \u00d7{settings.PLAYER_CRIT_MULTIPLIER:.0f}", True, settings.GOLD)
        screen.blit(crit_label, (settings.UI_PADDING + 180, bar_y + 28))

        phase_text = "YOUR MOVE"
        phase_symbol = "f(x)"
        if self.state == "PLAYER_ACTION_SELECT":
            phase_text = "YOUR ACTION"
            phase_symbol = "f'(x)"
        elif self.state == "ENEMY_TURN":
            phase_text = "ENEMY TURN"
            phase_symbol = "\u2200x"
        elif self.state == "RESOLVE_MOVE":
            phase_text = "MOVING..."
            phase_symbol = "\u0394x"
        elif self.state == "VICTORY_TRANSITION":
            phase_text = "Q.E.D."
            phase_symbol = "\u25a1"

        draw_text(screen, f"T{self.turn_manager.turn_number} {phase_symbol}",
                  (settings.WINDOW_WIDTH // 2 - 60, bar_y + 10),
                  settings.YELLOW if self.state in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT") else settings.RED,
                  12)
        draw_text(screen, phase_text,
                  (settings.WINDOW_WIDTH // 2, bar_y + 22),
                  settings.CYAN if self.state in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT") else settings.RED,
                  16)

        move_status = "\u2713" if self.turn_manager.player_moved else "\u25cb"
        act_status = "\u2713" if self.turn_manager.player_acted else "\u25cb"
        draw_text(screen, f"\u0394x: {move_status}  f(x): {act_status}",
                  (settings.WINDOW_WIDTH // 2, bar_y + 40),
                  settings.LIGHT_GRAY, 14)

        self._draw_combat_log(screen, bar_y + 5)

        controls = [
            "WASD: Cursor",
            "Enter: Confirm",
            "Space: Attack",
            "1/2: Skills",
            "R: Undo",
            "E: Wait",
            "Tab: Tree",
            "Esc: Pause",
        ]
        x = settings.WINDOW_WIDTH - 95
        y = bar_y + 2
        for c in controls:
            draw_text(screen, c, (x, y), settings.GRAY, 10, center=False)
            y += 11

    def _draw_bar(self, screen, x, y, w, h, pct, fill_color, bg_color):
        pygame.draw.rect(screen, bg_color, (x, y, w, h))
        if pct > 0:
            pygame.draw.rect(screen, fill_color, (x, y, int(w * pct), h))
        pygame.draw.rect(screen, settings.LIGHT_GRAY, (x, y, w, h), 1)
