import pygame
import math
import random

import settings
from utils import distance, angle_between, clamp, resource_path
from enemy_intent import EnemyIntent


class Enemy:
    def get_current_sprite(self):
        if not self.spritesheet:
            return None

        row = self.anim_map.get(self.current_anim, 0)
        col = int(self.anim_frame) % self.anim_frames.get(self.current_anim, 1)

        rect = pygame.Rect(col * self.sprite_size, row * self.sprite_size,
                           self.sprite_size, self.sprite_size)
        try:
            return self.spritesheet.subsurface(rect)
        except:
            return None

    def load_spritesheet(self):
        try:
            path = resource_path(f"assets/Robots/{self.robot_type}.png")
            self.spritesheet = pygame.image.load(path).convert_alpha()
        except Exception as e:
            print(f"Error loading robot {self.robot_type}: {e}")

    def __init__(self, x, y, enemy_type):
        self.x = x
        self.y = y
        self.col = 0
        self.row = 0
        self.type = enemy_type
        self.alive = True
        self.size = settings.ENEMY_SIZE
        self.flash_timer = 0
        self.dead = False
        self.status_effects = []

        self.robot_type = {
            "censor": "Spider",
            "strawman": "Scarab",
            "bayesian": "Hornet",
            "boss": "Centipede",
            "ortogonal": "Spider",
            "atirador": "Hornet",
            "granadeiro": "Scarab",
        }.get(enemy_type, "Spider")

        self.spritesheet = None
        self.load_spritesheet()

        self.current_anim = "idle"
        self.anim_frame = 0
        self.anim_timer = 0
        self.anim_speed = 0.2
        self.sprite_size = 16 if self.robot_type != "Hornet" else 24
        self.display_size = self.size * 2.5

        self.anim_map = {
            "Spider": {"idle": 0, "walk": 1, "fire": 2, "melee": 3, "destroyed": 4},
            "Scarab": {"idle": 0, "walk": 1, "fire": 2, "melee": 3, "destroyed": 4},
            "Hornet": {"idle": 0, "walk": 0, "fire": 1},
            "Centipede": {"idle": 0, "walk": 1, "fire": 2, "melee": 3}
        }.get(self.robot_type, {"idle": 0})

        self.anim_frames = {
            "Spider": {"idle": 2, "walk": 4, "fire": 2, "melee": 5, "destroyed": 1},
            "Scarab": {"idle": 2, "walk": 4, "fire": 2, "melee": 5, "destroyed": 1},
            "Hornet": {"idle": 8, "walk": 8, "fire": 8},
            "Centipede": {"idle": 4, "walk": 4, "fire": 4, "melee": 4}
        }.get(self.robot_type, {"idle": 1})

        self.spawn_timer = 0.5
        self.spawn_duration = 0.5
        self.bob_phase = random.random() * math.pi * 2
        self.bob_amplitude = 2

        self.anim_progress = 1.0
        self.anim_from_col = 0
        self.anim_from_row = 0
        self.anim_to_col = 0
        self.anim_to_row = 0
        self.anim_from_px = 0
        self.anim_from_py = 0
        self.anim_to_px = 0
        self.anim_to_py = 0
        self.anim_cells = []
        self.anim_step_idx = 0

        if enemy_type == "censor":
            self.hp = settings.CENSOR_HP
            self.max_hp = settings.CENSOR_HP
            self.damage = settings.CENSOR_DAMAGE
            self.move_range = settings.CENSOR_MOVE_RANGE
            self.attack_range = settings.CENSOR_ATTACK_RANGE
            self.color = settings.COLOR_CENSOR
        elif enemy_type == "strawman":
            self.hp = settings.STRAWMAN_HP
            self.max_hp = settings.STRAWMAN_HP
            self.damage = settings.STRAWMAN_DAMAGE
            self.move_range = settings.STRAWMAN_MOVE_RANGE
            self.attack_range = settings.STRAWMAN_ATTACK_RANGE
            self.color = settings.COLOR_STRAWMAN
            self.decoy_timer = 0
            self.decoy = False
        elif enemy_type == "bayesian":
            self.hp = settings.BAYESIAN_HP
            self.max_hp = settings.BAYESIAN_HP
            self.damage = settings.BAYESIAN_DAMAGE
            self.move_range = settings.BAYESIAN_MOVE_RANGE
            self.attack_range = settings.BAYESIAN_ATTACK_RANGE
            self.color = settings.COLOR_BAYESIAN
        elif enemy_type == "boss":
            self.hp = settings.BOSS_HP
            self.max_hp = settings.BOSS_HP
            self.damage = settings.BOSS_DAMAGE
            self.move_range = settings.BOSS_MOVE_RANGE
            self.attack_range = settings.BOSS_ATTACK_RANGE
            self.color = settings.COLOR_BOSS
            self.size = settings.BOSS_SIZE
            self.phase = 1
            self.last_phase = 1
            self.pulse_timer = 0
            self.area_attack_telegraph = 0
        elif enemy_type == "ortogonal":
            self.hp = settings.ORTOGONAL_HP
            self.max_hp = settings.ORTOGONAL_HP
            self.damage = settings.ORTOGONAL_DAMAGE
            self.move_range = settings.ORTOGONAL_MOVE_RANGE
            self.attack_range = settings.ORTOGONAL_ATTACK_RANGE
            self.color = settings.COLOR_ORTOGONAL
        elif enemy_type == "atirador":
            self.hp = settings.ATIRADOR_HP
            self.max_hp = settings.ATIRADOR_HP
            self.damage = settings.ATIRADOR_DAMAGE
            self.move_range = settings.ATIRADOR_MOVE_RANGE
            self.attack_range = settings.ATIRADOR_ATTACK_RANGE
            self.color = settings.COLOR_ATIRADOR
        elif enemy_type == "granadeiro":
            self.hp = settings.GRANADEIRO_HP
            self.max_hp = settings.GRANADEIRO_HP
            self.damage = settings.GRANADEIRO_DAMAGE
            self.move_range = settings.GRANADEIRO_MOVE_RANGE
            self.attack_range = settings.GRANADEIRO_ATTACK_RANGE
            self.color = settings.COLOR_GRANADEIRO

        self.info_title = {
            "censor": "enemy_censor",
            "strawman": "enemy_strawman",
            "bayesian": "enemy_bayesian",
            "boss": "enemy_boss",
            "ortogonal": "enemy_ortogonal",
            "atirador": "enemy_atirador",
            "granadeiro": "enemy_granadeiro",
        }.get(enemy_type, "enemy_unknown")

        self.lore = {
            "censor": "lore_censor",
            "strawman": "lore_strawman",
            "bayesian": "lore_bayesian",
            "boss": "lore_boss",
            "ortogonal": "lore_ortogonal",
            "atirador": "lore_atirador",
            "granadeiro": "lore_granadeiro",
        }.get(enemy_type, "lore_unknown")

        diff = settings.DIFFICULTY_SCALING[settings.DIFFICULTY]
        if enemy_type == "boss":
            self.hp = int(self.hp * diff["boss_hp_mult"])
            self.max_hp = self.hp
        else:
            self.hp = int(self.hp * diff["enemy_hp_mult"])
            self.max_hp = int(self.max_hp * diff["enemy_hp_mult"])
        self.damage = int(self.damage * diff["enemy_dmg_mult"])

        self.decoy_lifetime = 0
        self.is_decoy = False
        self.intended_action = None
        self.telegraph_timer = 0
        self.last_crit = False

    def roll_damage(self, entropy=0):
        diff = settings.DIFFICULTY_SCALING[settings.DIFFICULTY]
        base_crit = diff["enemy_crit_chance"]
        crit_mult = diff["enemy_crit_multiplier"]

        entropy_ratio = max(0.0, min(1.0, entropy / settings.MAX_ENTROPY))
        effective_crit_chance = base_crit + entropy_ratio * (1.0 - base_crit)
        self.last_crit = random.random() < effective_crit_chance

        base = self.damage
        variance = max(1, int(base * settings.ENEMY_DAMAGE_VARIANCE))
        amount = base + random.randint(-variance, variance)

        amount = int(amount * (1.0 + entropy_ratio))

        if self.last_crit:
            amount = int(amount * crit_mult)

        return max(1, amount)


    def set_grid_position(self, col, row, grid):
        self.col = int(col)
        self.row = int(row)
        px, py = grid.to_pixel(self.col, self.row)
        self.x, self.y = int(px), int(py)

    def _begin_anim_step(self, grid):
        from_col, from_row = self.anim_cells[self.anim_step_idx]
        to_col, to_row = self.anim_cells[self.anim_step_idx + 1]
        self.anim_from_col = from_col
        self.anim_from_row = from_row
        self.anim_to_col = to_col
        self.anim_to_row = to_row
        px_from, py_from = grid.to_pixel(from_col, from_row)
        px_to, py_to = grid.to_pixel(to_col, to_row)
        self.anim_from_px, self.anim_from_py = int(px_from), int(py_from)
        self.anim_to_px, self.anim_to_py = int(px_to), int(py_to)
        self.anim_progress = 0.0
        self.current_anim = "walk"

    def is_animating(self):
        return len(self.anim_cells) > 1

    def update_animation(self, dt, grid=None):
        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % self.anim_frames.get(self.current_anim, 1)

        if self.is_animating():
            self.current_anim = "walk"
            self.anim_progress = min(1.0, self.anim_progress + dt * 8)
            frac = self.anim_progress
            frac = frac * frac * (3 - 2 * frac)
            self.x = int(self.anim_from_px + (self.anim_to_px - self.anim_from_px) * frac)
            self.y = int(self.anim_from_py + (self.anim_to_py - self.anim_from_py) * frac)
            if self.anim_progress >= 1.0:
                self.anim_step_idx += 1
                self.col = int(self.anim_to_col)
                self.row = int(self.anim_to_row)
                if self.anim_step_idx >= len(self.anim_cells) - 1:
                    self.anim_cells = []
                    self.anim_step_idx = 0
                    self.anim_progress = 1.0
                    self.current_anim = "idle"
                if grid is not None:
                    px, py = grid.to_pixel(self.col, self.row)
                    self.x, self.y = int(px), int(py)
                    if self.anim_step_idx < len(self.anim_cells):
                        self._begin_anim_step(grid)
        else:
            if grid is not None:
                self.current_anim = "idle"
                px, py = grid.to_pixel(self.col, self.row)
                self.x, self.y = int(px), int(py)

    def snap_to_grid(self, grid):
        if not self.is_animating() and grid is not None:
            px, py = grid.to_pixel(self.col, self.row)
            self.x, self.y = int(px), int(py)

    def start_move_anim(self, from_col, from_row, to_col, to_row, grid, path=None):
        if path is None:
            path = [(to_col, to_row)]
        self.anim_cells = [(from_col, from_row)] + [(int(col), int(row)) for col, row in path]
        self.anim_step_idx = 0
        self._begin_anim_step(grid)

    def get_hitbox(self):
        # Use display_size for a more accurate hitbox that matches the visual
        return pygame.Rect(self.x - self.display_size // 2, self.y - self.display_size // 2,
                           self.display_size, self.display_size)

    def take_damage(self, amount):
        self.hp -= amount
        self.flash_timer = 0.15
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            self.dead = True
            return True
        return False

    def get_predicted_grid_position(self, player_col, player_row, grid):
        if self.type != "bayesian":
            return (self.col, self.row)
        dc = player_col - self.col
        dr = player_row - self.row
        steps = min(2, max(abs(dc), abs(dr)))
        sign_dc = 1 if dc > 0 else (-1 if dc < 0 else 0)
        sign_dr = 1 if dr > 0 else (-1 if dr < 0 else 0)
        pred_col = player_col + sign_dc * steps
        pred_row = player_row + sign_dr * steps
        pred_col = max(0, min(grid.cols - 1, pred_col))
        pred_row = max(0, min(grid.rows - 1, pred_row))
        return (pred_col, pred_row)

    def decide_intent(self, player_col, player_row, grid, all_enemies):
        if self.dead:
            return None

        dist = grid.grid_distance(self.col, self.row, player_col, player_row)
        action = self.decide_action(player_col, player_row, grid, all_enemies)
        if action is None:
            return None

        move_target = None
        attack_origin = (self.col, self.row)

        if action["type"] in ("move", "move_then_attack"):
            tc, tr = action["target_col"], action["target_row"]
            if grid.is_valid(tc, tr) and not grid.is_blocked(tc, tr):
                if not grid.is_level_change(self.col, self.row, tc, tr):
                    move_target = (tc, tr)
                    attack_origin = (tc, tr)

        intent = EnemyIntent(
            enemy=self,
            move_target=move_target,
            attack_type=action["type"],
            attack_origin=attack_origin,
            target_tile=(player_col, player_row),
            danger_tiles=set(),
            damage=self.damage,
        )

        if self.type == "censor":
            self._censor_intent(intent, player_col, player_row, grid)
        elif self.type == "strawman":
            self._strawman_intent(intent, player_col, player_row, grid)
        elif self.type == "bayesian":
            self._bayesian_intent(intent, player_col, player_row, grid)
        elif self.type == "boss":
            self._boss_intent(intent, action, player_col, player_row, grid)
        elif self.type == "ortogonal":
            self._ortogonal_intent(intent, player_col, player_row, grid)
        elif self.type == "atirador":
            self._atirador_intent(intent, player_col, player_row, grid)
        elif self.type == "granadeiro":
            self._granadeiro_intent(intent, player_col, player_row, grid)

        intents = [intent]
        
        # Strawman decoy logic: 40% chance to create a false indicator
        if self.type == "strawman" and random.random() < 0.4:
            fake_origin = (self.col + random.randint(-2, 2), self.row + random.randint(-2, 2))
            fake_intent = EnemyIntent(
                enemy=self,
                move_target=None,
                attack_type="attack",
                attack_origin=fake_origin,
                target_tile=(player_col, player_row),
                danger_tiles=self._get_cross_cells(fake_origin[0], fake_origin[1], distance=1),
                damage=0,
                is_fake=True,
                telegraph_type="cross"
            )
            intents.append(fake_intent)

        return intents

    def _get_line_cells(self, from_col, from_row, to_col, to_row, max_range=8, grid=None):
        cells = set()
        dc = to_col - from_col
        dr = to_row - from_row
        if dc == 0 and dr == 0:
            return cells
        steps = max(abs(dc), abs(dr))
        step_dc = (1 if dc > 0 else -1) if dc != 0 else 0
        step_dr = (1 if dr > 0 else -1) if dr != 0 else 0
        for i in range(1, min(steps, max_range) + 1):
            c = from_col + step_dc * i
            r = from_row + step_dr * i
            if grid and not grid.is_valid(c, r):
                break
            if grid and grid.is_blocked(c, r):
                break
            cells.add((c, r))
        return cells

    def _get_cross_cells(self, col, row, distance=1):
        cells = set()
        for dc, dr in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            for i in range(1, distance + 1):
                cells.add((col + dc * i, row + dr * i))
        return cells

    def _censor_intent(self, intent, player_col, player_row, grid):
        origin = intent.attack_origin
        dist = grid.grid_distance(origin[0], origin[1], player_col, player_row)
        if dist <= self.attack_range:
            danger = self._get_line_cells(
                origin[0], origin[1], player_col, player_row,
                max_range=self.attack_range, grid=grid
            )
            intent.danger_tiles = danger
            intent.telegraph_type = "line"
            intent.lock_mode = "fixed"
        elif intent.move_target:
            tc, tr = intent.move_target
            dist2 = grid.grid_distance(tc, tr, player_col, player_row)
            if dist2 <= self.attack_range:
                danger = self._get_line_cells(
                    tc, tr, player_col, player_row,
                    max_range=self.attack_range, grid=grid
                )
                intent.danger_tiles = danger
                intent.telegraph_type = "line"
                intent.lock_mode = "fixed"
            else:
                intent.danger_tiles = set()
                intent.telegraph_type = "none"
        else:
            intent.danger_tiles = set()
            intent.telegraph_type = "none"

    def _strawman_intent(self, intent, player_col, player_row, grid):
        origin = intent.attack_origin
        dist = grid.grid_distance(origin[0], origin[1], player_col, player_row)
        if dist <= self.attack_range:
            intent.danger_tiles = self._get_cross_cells(origin[0], origin[1], distance=1)
            intent.telegraph_type = "cross"
            intent.lock_mode = "fixed"
        elif intent.move_target:
            tc, tr = intent.move_target
            dist2 = grid.grid_distance(tc, tr, player_col, player_row)
            if dist2 <= self.attack_range:
                intent.danger_tiles = self._get_cross_cells(tc, tr, distance=1)
                intent.telegraph_type = "cross"
                intent.lock_mode = "fixed"
        else:
            intent.danger_tiles = set()
            intent.telegraph_type = "none"

    def _bayesian_intent(self, intent, player_col, player_row, grid):
        origin = intent.attack_origin
        dist = grid.grid_distance(origin[0], origin[1], player_col, player_row)
        if dist <= self.attack_range:
            danger = self._get_line_cells(
                origin[0], origin[1], player_col, player_row,
                max_range=self.attack_range, grid=grid
            )
            intent.danger_tiles = danger
            intent.telegraph_type = "line"
            intent.lock_mode = "post_move"
        elif intent.move_target:
            tc, tr = intent.move_target
            dist2 = grid.grid_distance(tc, tr, player_col, player_row)
            if dist2 <= self.attack_range:
                danger = self._get_line_cells(
                    tc, tr, player_col, player_row,
                    max_range=self.attack_range, grid=grid
                )
                intent.danger_tiles = danger
                intent.telegraph_type = "line"
                intent.lock_mode = "post_move"
        else:
            intent.danger_tiles = set()
            intent.telegraph_type = "none"

    def _boss_intent(self, intent, action, player_col, player_row, grid):
        origin = intent.attack_origin
        if action["type"] == "line_attack":
            danger = self._get_line_cells(
                origin[0], origin[1], player_col, player_row,
                max_range=self.attack_range, grid=grid
            )
            intent.danger_tiles = danger
            intent.telegraph_type = "line"
            intent.lock_mode = "fixed"
        elif action["type"] == "area_attack":
            cells = grid.get_cells_in_radius(player_col, player_row, 2)
            intent.danger_tiles = set(cells)
            intent.telegraph_type = "area"
            intent.lock_mode = "fixed"
        else:
            intent.danger_tiles = set()
            intent.telegraph_type = "none"

    def _ortogonal_intent(self, intent, player_col, player_row, grid):
        origin = intent.attack_origin
        dist = grid.grid_distance(origin[0], origin[1], player_col, player_row)
        if dist <= self.attack_range:
            intent.danger_tiles = self._get_cross_cells(origin[0], origin[1], distance=1)
            intent.telegraph_type = "cross"
            intent.lock_mode = "fixed"
        elif intent.move_target:
            tc, tr = intent.move_target
            dist2 = grid.grid_distance(tc, tr, player_col, player_row)
            if dist2 <= self.attack_range:
                intent.danger_tiles = self._get_cross_cells(tc, tr, distance=1)
                intent.telegraph_type = "cross"
                intent.lock_mode = "fixed"
        else:
            intent.danger_tiles = set()
            intent.telegraph_type = "none"

    def _atirador_intent(self, intent, player_col, player_row, grid):
        origin = intent.attack_origin
        dist = grid.grid_distance(origin[0], origin[1], player_col, player_row)
        if dist <= self.attack_range:
            danger = self._get_line_cells(
                origin[0], origin[1], player_col, player_row,
                max_range=self.attack_range, grid=grid
            )
            intent.danger_tiles = danger
            intent.telegraph_type = "line"
            intent.lock_mode = "post_move"
        elif intent.move_target:
            tc, tr = intent.move_target
            dist2 = grid.grid_distance(tc, tr, player_col, player_row)
            if dist2 <= self.attack_range:
                danger = self._get_line_cells(
                    tc, tr, player_col, player_row,
                    max_range=self.attack_range, grid=grid
                )
                intent.danger_tiles = danger
                intent.telegraph_type = "line"
                intent.lock_mode = "post_move"
        else:
            intent.danger_tiles = set()
            intent.telegraph_type = "none"

    def _granadeiro_intent(self, intent, player_col, player_row, grid):
        origin = intent.attack_origin
        dist = grid.grid_distance(origin[0], origin[1], player_col, player_row)
        cells = grid.get_cells_in_radius(player_col, player_row, 1)
        target_tiles = set((c, r) for c, r in cells if grid.is_valid(c, r))
        if dist <= self.attack_range:
            intent.danger_tiles = target_tiles
            intent.telegraph_type = "area"
            intent.lock_mode = "fixed"
        elif intent.move_target:
            tc, tr = intent.move_target
            dist2 = grid.grid_distance(tc, tr, player_col, player_row)
            if dist2 <= self.attack_range:
                intent.danger_tiles = target_tiles
                intent.telegraph_type = "area"
                intent.lock_mode = "fixed"
        else:
            intent.danger_tiles = set()
            intent.telegraph_type = "none"

    def decide_action(self, player_col, player_row, grid, all_enemies):
        if self.dead:
            return None

        occupied = {
            (int(enemy.col), int(enemy.row))
            for enemy in all_enemies
            if enemy is not self and not enemy.dead
        }
        dist = grid.grid_distance(self.col, self.row, player_col, player_row)

        if self.type == "boss":
            return self._boss_decide(dist, player_col, player_row, grid, occupied)

        if self.type == "ortogonal":
            return self._ortogonal_decide(dist, player_col, player_row, grid)
        elif self.type == "atirador":
            return self._atirador_decide(dist, player_col, player_row, grid)
        elif self.type == "granadeiro":
            return self._granadeiro_decide(dist, player_col, player_row, grid)

        if dist <= self.attack_range and not grid.is_level_change(self.col, self.row, player_col, player_row):
            return {"type": "attack", "target_col": player_col, "target_row": player_row}

        reachable = grid.get_reachable_cells(
            self.col,
            self.row,
            self.move_range,
            include_barriers=True,
            extra_blocked=occupied,
        )

        if dist <= self.attack_range + 2:
            path = grid.pathfind(
                self.col,
                self.row,
                player_col,
                player_row,
                include_barriers=True,
                extra_blocked=occupied,
            )
            if path:
                for step in path[:self.move_range]:
                    if step in occupied:
                        break
                    if step == (player_col, player_row):
                        break
                    if grid.grid_distance(step[0], step[1], player_col, player_row) <= self.attack_range:
                        if not grid.is_level_change(step[0], step[1], player_col, player_row):
                            return {
                                "type": "move_then_attack",
                                "target_col": step[0],
                                "target_row": step[1],
                                "attack_after": True,
                            }

        path = grid.pathfind(
            self.col,
            self.row,
            player_col,
            player_row,
            include_barriers=True,
            extra_blocked=occupied,
        )
        if path:
            last_step = None
            reachable_set = set(reachable)
            for step in path[:self.move_range]:
                if step in occupied:
                    break
                if step == (player_col, player_row):
                    break
                if step in reachable_set:
                    last_step = step
            if last_step is not None:
                return {"type": "move", "target_col": last_step[0], "target_row": last_step[1]}

        closest_reachable = None
        closest_dist = float('inf')
        player_tile = grid.tile_types.get((player_col, player_row), 0)
        for cell in reachable:
            cd = grid.grid_distance(cell[0], cell[1], player_col, player_row)
            if cd < closest_dist:
                closest_dist = cd
                closest_reachable = cell

        if closest_reachable:
            return {"type": "move", "target_col": closest_reachable[0], "target_row": closest_reachable[1]}

        return {"type": "wait"}

    def _boss_decide(self, dist, player_col, player_row, grid, occupied):
        phase = 1
        if self.hp < self.max_hp * 0.33:
            phase = 3
        elif self.hp < self.max_hp * 0.66:
            phase = 2
        self.phase = phase

        choices = []
        if phase == 1:
            choices = ["line_attack", "move"]
        elif phase == 2:
            choices = ["line_attack", "area_attack", "move"]
        else:
            choices = ["line_attack", "area_attack", "line_attack", "move"]

        if dist <= self.attack_range:
            choices.append("line_attack")
            choices.append("line_attack")

        action = random.choice(choices)

        if action == "move":
            path = grid.pathfind(
                self.col,
                self.row,
                player_col,
                player_row,
                include_barriers=True,
                extra_blocked=occupied,
            )
            if path:
                last_step = None
                for step in path[:self.move_range]:
                    if step in occupied:
                        break
                    if step == (player_col, player_row):
                        break
                    last_step = step
                if last_step is not None:
                    return {"type": "move", "target_col": last_step[0], "target_row": last_step[1]}
            return {"type": "wait"}
        elif action == "line_attack":
            return {"type": "line_attack", "target_col": player_col, "target_row": player_row}
        elif action == "area_attack":
            return {"type": "area_attack", "target_col": player_col, "target_row": player_row}
        return {"type": "wait"}

    def _ortogonal_decide(self, dist, player_col, player_row, grid):
        if dist <= self.attack_range and not grid.is_level_change(self.col, self.row, player_col, player_row):
            return {"type": "attack", "target_col": player_col, "target_row": player_row}

        reachable = grid.get_reachable_cells(self.col, self.row, self.move_range)
        path = grid.pathfind(self.col, self.row, player_col, player_row)
        if path:
            reachable_set = set(reachable)
            for i, step in enumerate(path):
                if step in reachable_set:
                    td = grid.grid_distance(step[0], step[1], player_col, player_row)
                    if td <= self.attack_range:
                        return {"type": "move_then_attack",
                                "target_col": step[0], "target_row": step[1],
                                "attack_after": True}
            for i, step in enumerate(path):
                if step in reachable_set:
                    return {"type": "move", "target_col": step[0], "target_row": step[1]}

        if reachable:
            best = min(reachable, key=lambda c: grid.grid_distance(c[0], c[1], player_col, player_row))
            return {"type": "move", "target_col": best[0], "target_row": best[1]}
        return {"type": "wait"}

    def _atirador_decide(self, dist, player_col, player_row, grid):
        if dist <= self.attack_range and not grid.is_level_change(self.col, self.row, player_col, player_row):
            if dist <= 2:
                path = grid.pathfind(self.col, self.row, player_col, player_row)
                if path and len(path) > 0:
                    retreat_dir = (-1 if path[0][0] > self.col else (1 if path[0][0] < self.col else 0),
                                    -1 if path[0][1] > self.row else (1 if path[0][1] < self.row else 0))
                    retreat_col = self.col + retreat_dir[0] * 2
                    retreat_row = self.row + retreat_dir[1] * 2
                    retreat_col = max(0, min(grid.cols - 1, retreat_col))
                    retreat_row = max(0, min(grid.rows - 1, retreat_row))
                    reachable = grid.get_reachable_cells(self.col, self.row, self.move_range)
                    best = None
                    best_dist = 0
                    for cell in reachable:
                        cd = grid.grid_distance(cell[0], cell[1], player_col, player_row)
                        if cd >= 3 and cd <= self.attack_range and cd > best_dist:
                            if not grid.is_level_change(self.col, self.row, cell[0], cell[1]):
                                best = cell
                                best_dist = cd
                    if best:
                        return {"type": "move", "target_col": best[0], "target_row": best[1]}
            return {"type": "attack", "target_col": player_col, "target_row": player_row}

        reachable = grid.get_reachable_cells(self.col, self.row, self.move_range)
        best = None
        best_score = -999
        for cell in reachable:
            cd = grid.grid_distance(cell[0], cell[1], player_col, player_row)
            if cd >= 3 and cd <= self.attack_range:
                score = cd
                if score > best_score:
                    best = cell
                    best_score = score
        if best:
            return {"type": "move_then_attack",
                    "target_col": best[0], "target_row": best[1],
                    "attack_after": True}

        path = grid.pathfind(self.col, self.row, player_col, player_row)
        if path:
            reachable_set = set(reachable)
            for i, step in enumerate(path):
                if step in reachable_set:
                    return {"type": "move", "target_col": step[0], "target_row": step[1]}
        return {"type": "wait"}

    def _granadeiro_decide(self, dist, player_col, player_row, grid):
        if dist <= self.attack_range:
            return {"type": "area_attack", "target_col": player_col, "target_row": player_row}

        reachable = grid.get_reachable_cells(self.col, self.row, self.move_range)
        best_attack = None
        best_attack_dist = 999
        best_retreat = None
        best_retreat_score = -999

        for cell in reachable:
            cd = grid.grid_distance(cell[0], cell[1], player_col, player_row)
            if 2 <= cd <= self.attack_range:
                if cd < best_attack_dist:
                    best_attack = cell
                    best_attack_dist = cd
            if cd > dist and cd <= self.attack_range + 2:
                score = cd - dist
                if score > best_retreat_score:
                    best_retreat = cell
                    best_retreat_score = score

        if best_attack:
            return {"type": "move_then_attack",
                    "target_col": best_attack[0], "target_row": best_attack[1],
                    "attack_after": True}

        path = grid.pathfind(self.col, self.row, player_col, player_row)
        if path:
            reachable_set = set(reachable)
            for i, step in enumerate(path):
                if step in reachable_set:
                    return {"type": "move", "target_col": step[0], "target_row": step[1]}

        if best_retreat:
            return {"type": "move", "target_col": best_retreat[0], "target_row": best_retreat[1]}
        return {"type": "wait"}

    def draw(self, screen, offset=(0, 0)):
        if self.dead:
            return

        ox, oy = offset
        vx, vy = self.x + ox, self.y + oy

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
        draw_y = vy + bob_y

        size = int(self.size * spawn_scale)
        if size < 1:
            size = 1

        sprite = self.get_current_sprite()
        if sprite:
            sprite = pygame.transform.scale(sprite, (int(self.display_size * spawn_scale),
                                                     int(self.display_size * spawn_scale)))
            if self.flash_timer > 0:
                flash_surf = sprite.copy()
                flash_surf.fill((255, 255, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
                screen.blit(flash_surf, (vx - self.display_size // 2, draw_y - self.display_size // 2))
            else:
                screen.blit(sprite, (vx - self.display_size // 2, draw_y - self.display_size // 2))
        else:
            if self.type == "censor":
                self._draw_censor(screen, vx, draw_y, size, color, spawn_alpha)
            elif self.type == "strawman":
                self._draw_strawman(screen, vx, draw_y, size, color, spawn_alpha)
            elif self.type == "bayesian":
                self._draw_bayesian(screen, vx, draw_y, size, color, spawn_alpha)
            elif self.type == "boss":
                self._draw_boss(screen, vx, draw_y, size, color, spawn_alpha)
            elif self.type == "ortogonal":
                self._draw_ortogonal(screen, vx, draw_y, size, color, spawn_alpha)
            elif self.type == "atirador":
                self._draw_atirador(screen, vx, draw_y, size, color, spawn_alpha)
            elif self.type == "granadeiro":
                self._draw_granadeiro(screen, vx, draw_y, size, color, spawn_alpha)

        if self.type != "boss" and self.hp < self.max_hp:
            self._draw_hp_bar(screen, vx, draw_y - size - 6, size)

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
        font = pygame.font.Font(None, 12)
        label = font.render("NOT", True, settings.WHITE)
        label.set_alpha(alpha)
        screen.blit(label, (x - label.get_width() // 2, y - size - 14))

    def _draw_strawman(self, screen, x, y, size, color, alpha):
        s = pygame.Surface((size * 2, size * 2))
        s.set_alpha(alpha)
        s.fill(color)
        screen.blit(s, (x - size, y - size))
        pygame.draw.rect(screen, (255, 255, 255), (x - size, y - size, size * 2, size * 2), 1)
        eye_size = max(2, size // 3)
        pygame.draw.circle(screen, settings.WHITE, (x - size // 2, y - size // 3), eye_size)
        pygame.draw.circle(screen, settings.WHITE, (x + size // 2, y - size // 3), eye_size)
        font = pygame.font.Font(None, 12)
        label = font.render("ARG", True, settings.WHITE)
        label.set_alpha(alpha)
        screen.blit(label, (x - label.get_width() // 2, y - size - 14))

    def _draw_bayesian(self, screen, x, y, size, color, alpha):
        s = pygame.Surface((size * 2, size * 2))
        s.set_alpha(alpha)
        s.fill(color)
        screen.blit(s, (x - size, y - size))
        pygame.draw.rect(screen, (255, 255, 255), (x - size, y - size, size * 2, size * 2), 1)
        eye_size = max(2, size // 3)
        pygame.draw.circle(screen, settings.YELLOW, (x, y - size // 3), eye_size + 1)
        pygame.draw.circle(screen, settings.WHITE, (x, y - size // 3), eye_size - 1)
        font = pygame.font.Font(None, 12)
        label = font.render("P(A|B)", True, settings.YELLOW)
        label.set_alpha(alpha)
        screen.blit(label, (x - label.get_width() // 2, y - size - 14))

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

    def _draw_ortogonal(self, screen, x, y, size, color, alpha):
        rect = pygame.Rect(x - size, y - size, size * 2, size * 2)
        s = pygame.Surface((size * 2, size * 2))
        s.set_alpha(alpha)
        s.fill(color)
        screen.blit(s, rect)
        pygame.draw.rect(screen, settings.WHITE, rect, 2)
        cross_len = size - 2
        pygame.draw.line(screen, settings.WHITE, (x - cross_len, y), (x + cross_len, y), 3)
        pygame.draw.line(screen, settings.WHITE, (x, y - cross_len), (x, y + cross_len), 3)
        font = pygame.font.Font(None, 12)
        label = font.render("+", True, settings.WHITE)
        label.set_alpha(alpha)
        screen.blit(label, (x - label.get_width() // 2, y - size - 14))

    def _draw_atirador(self, screen, x, y, size, color, alpha):
        rect = pygame.Rect(x - size, y - size, size * 2, size * 2)
        s = pygame.Surface((size * 2, size * 2))
        s.set_alpha(alpha)
        s.fill(color)
        screen.blit(s, rect)
        pygame.draw.rect(screen, settings.WHITE, rect, 1)
        pts = [(x, y - size), (x + size, y), (x, y + size), (x - size, y)]
        pygame.draw.polygon(screen, settings.WHITE, pts, 1)
        pygame.draw.line(screen, settings.WHITE, (x, y - size + 2), (x, y + size - 2), 2)
        pygame.draw.line(screen, settings.WHITE, (x, y - size + 5), (x + 3, y - size + 8), 1)
        font = pygame.font.Font(None, 12)
        label = font.render("AIM", True, settings.YELLOW)
        label.set_alpha(alpha)
        screen.blit(label, (x - label.get_width() // 2, y - size - 14))

    def _draw_granadeiro(self, screen, x, y, size, color, alpha):
        rect = pygame.Rect(x - size, y - size, size * 2, size * 2)
        s = pygame.Surface((size * 2, size * 2))
        s.set_alpha(alpha)
        s.fill(color)
        screen.blit(s, rect)
        pygame.draw.rect(screen, settings.WHITE, rect, 2)
        inner_size = size // 2
        pygame.draw.rect(screen, settings.WHITE,
                        (x - inner_size, y - inner_size, inner_size * 2, inner_size * 2), 1)
        pygame.draw.circle(screen, settings.ORANGE, (x, y), inner_size - 1)
        font = pygame.font.Font(None, 12)
        label = font.render("3x3", True, settings.ORANGE)
        label.set_alpha(alpha)
        screen.blit(label, (x - label.get_width() // 2, y - size - 14))

    def _draw_hp_bar(self, screen, x, y, size):
        bar_w = size * 2
        bar_h = 3
        bar_x = x - bar_w // 2
        bar_y = y
        hp_ratio = self.hp / self.max_hp
        pygame.draw.rect(screen, (60, 20, 20), (bar_x, bar_y, bar_w, bar_h))
        if hp_ratio > 0.5:
            bar_color = settings.GREEN
        elif hp_ratio > 0.25:
            bar_color = settings.ORANGE
        else:
            bar_color = settings.RED
        pygame.draw.rect(screen, bar_color, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))
        pygame.draw.rect(screen, settings.LIGHT_GRAY, (bar_x, bar_y, bar_w, bar_h), 1)
