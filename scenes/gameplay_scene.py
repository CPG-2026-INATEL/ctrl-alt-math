import pygame
import random
import math

import settings
from utils import draw_text, distance, angle_between
from i18n import t
from enemy import Enemy
from enemy_intent import EnemyIntent
from grid import Grid
from turn_manager import TurnManager
from tilemap import TileMap, MapGenerator
from tilemap import TILE_HOLE, TILE_LOW, TILE_HIGH, TILE_HIGH_EDGE
from tilemap import TILE_STAIRS_UP, TILE_STAIRS_DOWN, TILE_STAIRS_LEFT, TILE_STAIRS_RIGHT
from scenes.scene import Scene


class GameplayScene(Scene):
    TILESET_PATH = "assets/Tileset/tileset_arranged.png"
    TILE_SIZE = 16
    ENEMY_ATTACK_DELAY = 0.25

    def __init__(self, game):
        super().__init__(game)
        self.state = "WAVE_INTRO"
        self.grid = Grid()
        self.turn_manager = TurnManager()
        self.obstacles_data = settings.ARENA_OBSTACLES
        self.tilemap = None
        self.tile_offset_x = 0
        self.tile_offset_y = 0
        self.camera_x = 0
        self.camera_y = 0

        self.cursor_col = 8
        self.cursor_row = 6
        self.cursor_timer = 0

        self.show_move_range = False
        self.show_action_range = False
        self.selected_skill = None

        self.enemy_actions = []
        self.enemy_resolve_idx = 0
        self.enemy_phase = None
        self.enemy_pending_attack = None
        self.enemy_attack_delay_timer = 0

        self.victory_timer = 0
        self.qed_position = None
        self.game_over_timer = 0

        self.turn_log = []
        self.last_enemy_death_pos = None

        self.pending_player_col = None
        self.pending_player_row = None
        self.hovered_enemy = None
        self.hovered_intent_data = None
        
        self.lore_timer = 15.0 # Start after 15 seconds
        self.lore_toast = None
        self.player_took_damage_this_room = False
        self.crits_this_room = 0
        self.tiles_moved_this_turn = 0

    def enter(self, prev_scene=None):
        self.state = "WAVE_INTRO"
        self.turn_manager = TurnManager()
        self.enemy_actions = []
        self.enemy_resolve_idx = 0
        self.enemy_phase = None
        self.enemy_pending_attack = None
        self.enemy_attack_delay_timer = 0
        self.enemy_intents = []
        self.danger_locked = False
        self.lock_timer = 0
        self.victory_timer = 0
        self.show_move_range = False
        self.show_action_range = False
        self.selected_skill = None
        self.turn_log = []
        self.player_took_damage_this_room = False
        self.crits_this_room = 0

        if prev_scene and hasattr(prev_scene, "room"):
            room = prev_scene.room
            self.game.current_room = room
            
            # Randomize map size based on difficulty
            scaling = settings.DIFFICULTY_SCALING.get(settings.DIFFICULTY, settings.DIFFICULTY_SCALING[settings.DIFFICULTY_HARD])
            size_factor = random.uniform(scaling["arena_size_min"], scaling["arena_size_max"])
            new_cols = int(settings.GRID_COLS * size_factor)
            new_rows = int(settings.GRID_ROWS * size_factor)
            self.grid = Grid(new_cols, new_rows)
            
            self.obstacles_data = room.obstacles
            # For dynamic map, we might need to adjust obstacle positions or just use generated ones
            # For now, we'll use the generated obstacles from _generate_tilemap
            
            self.game.enemies = []
            # Increase amount of enemies proportional to area increase
            enemy_multiplier = (new_cols * new_rows) / (settings.GRID_COLS * settings.GRID_ROWS)
            # Give it a bit more punch
            enemy_multiplier *= 1.2
            
            for enemy_type, count in room.enemies:
                increased_count = max(1, int(count * enemy_multiplier))
                for _ in range(increased_count):
                    ex, ey = self._get_spawn_position()
                    enemy = Enemy(ex, ey, enemy_type)
                    if enemy_type == "boss":
                        enemy.max_hp = int(room.boss_hp * (1.0 + (size_factor - 1.0) * 0.5))
                        enemy.hp = enemy.max_hp
                    self.game.enemies.append(enemy)

            if len(self.game.enemies) == 0:
                self.state = "NO_COMBAT"
                self._check_victory()
            
            # Speak room narrative
            text = f"{t(room.name)}. {t(room.narrative)}"
            self.game.tts.speak(text, lang=settings.LANGUAGE)
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
        aw = int(self.grid.width)
        ah = int(self.grid.height)
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
        occupied = {(self.game.player.col, self.game.player.row)}
        occupied.update(
            (enemy.col, enemy.row)
            for enemy in self.game.enemies
            if not enemy.dead and self.grid.is_valid(enemy.col, enemy.row)
        )

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

        if self.grid.is_blocked(col, row) or (col, row) in occupied:
            for dc in range(-2, 3):
                for dr in range(-2, 3):
                    nc, nr = col + dc, row + dr
                    if self.grid.is_valid(nc, nr) and not self.grid.is_blocked(nc, nr) and (nc, nr) not in occupied:
                        return nc, nr

        for row_idx in range(self.grid.rows):
            for col_idx in range(self.grid.cols):
                if not self.grid.is_blocked(col_idx, row_idx) and (col_idx, row_idx) not in occupied:
                    return col_idx, row_idx

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
        map_data, obstacles = gen.generate()

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

    def _begin_room(self):
        self.state = "PLAYER_INPUT"
        self.turn_manager.start_turn()
        self.turn_manager.snapshot(self._get_game_state()) # Initial snapshot for Turn 1
        self.show_move_range = True
        self._generate_enemy_intents()
        self.danger_locked = False
        self._save_rewind_state()
        self.tiles_moved_this_turn = 0
        self.game.sfx.play("wave_start")
        self.game.tts.speak(t("wave_count", wave=self.turn_manager.turn_number), lang=settings.LANGUAGE)

    def _generate_enemy_intents(self):
        pc = self.game.player.col
        pr = self.game.player.row
        alive_enemies = [e for e in self.game.enemies if not e.dead]
        self.enemy_intents = []
        for enemy in alive_enemies:
            new_intents = enemy.decide_intent(pc, pr, self.grid, self.game.enemies)
            self.enemy_intents.extend(new_intents)
        player_skills = self._get_player_skill_ids()
        self.grid.set_danger_tiles(self.enemy_intents, player_skills)

    def _get_player_skill_ids(self):
        skills = []
        st = self.game.skill_tree
        for sid in ["derivada", "bayes", "teoria_jogos"]:
            if st.is_unlocked(sid):
                skills.append(sid)
        return skills

    def _leave_no_combat_room(self):
        if self.game.current_room:
            self.game.world_map.complete_room(
                (self.game.current_room.col, self.game.current_room.row)
            )
            if self.game.current_room.type == "victory" and self.game.world_map.all_required_rooms_completed():
                self.game.scene_manager.switch("victory")
                return
        self.game.scene_manager.switch("map")

    def _set_cursor_from_mouse(self, pos):
        arena_rect = pygame.Rect(
            settings.ARENA_OFFSET_X,
            settings.ARENA_OFFSET_Y,
            self.grid.width,
            self.grid.height,
        )
        if not arena_rect.collidepoint(pos):
            pass
        
        world_x = pos[0] + self.camera_x
        world_y = pos[1] + self.camera_y
        
        self.cursor_col, self.cursor_row = self.grid.to_grid(world_x, world_y)
        return True

    def _toggle_skill(self, skill_id):
        if self.selected_skill == skill_id:
            self.selected_skill = None
        else:
            self.selected_skill = skill_id
        self.show_action_range = True

    def _build_anim_path(self, from_col, from_row, to_col, to_row, include_barriers=False, extra_blocked=None):
        path = self.grid.pathfind(
            from_col,
            from_row,
            to_col,
            to_row,
            allow_diagonal=False,
            include_barriers=include_barriers,
            extra_blocked=extra_blocked,
        )
        if path:
            return path

        def try_axes(horizontal_first):
            path_cells = []
            cur_col = from_col
            cur_row = from_row
            axes = ("x", "y") if horizontal_first else ("y", "x")
            for axis in axes:
                if axis == "x":
                    while cur_col != to_col:
                        step_col = cur_col + (1 if to_col > cur_col else -1)
                        if self.grid.is_blocked(step_col, cur_row, include_barriers, extra_blocked):
                            return []
                        if self.grid.is_level_change(cur_col, cur_row, step_col, cur_row):
                            return []
                        cur_col = step_col
                        path_cells.append((cur_col, cur_row))
                else:
                    while cur_row != to_row:
                        step_row = cur_row + (1 if to_row > cur_row else -1)
                        if self.grid.is_blocked(cur_col, step_row, include_barriers, extra_blocked):
                            return []
                        if self.grid.is_level_change(cur_col, cur_row, cur_col, step_row):
                            return []
                        cur_row = step_row
                        path_cells.append((cur_col, cur_row))
            return path_cells

        return try_axes(True) or try_axes(False) or [(to_col, to_row)]

    def _enter_action_select(self):
        self.turn_manager.player_moved = True
        self.state = "PLAYER_ACTION_SELECT"
        self.show_move_range = False
        self.show_action_range = True

    def _confirm_player_cursor(self):
        pc = self.game.player.col
        pr = self.game.player.row
        reachable = self.grid.get_reachable_cells(pc, pr, self.game.player.move_range)

        if (self.cursor_col, self.cursor_row) == (pc, pr):
            self._enter_action_select()
            self.game.sfx.play("menu_select")
            return

        if (self.cursor_col, self.cursor_row) in reachable:
            self.pending_player_col = self.cursor_col
            self.pending_player_row = self.cursor_row
            self.state = "RESOLVE_MOVE"
            self.turn_manager.resolve_timer = 0
            anim_path = self._build_anim_path(pc, pr, self.cursor_col, self.cursor_row)
            self.tiles_moved_this_turn = len(anim_path)
            self.game.player.start_move_anim(
                pc, pr, self.cursor_col, self.cursor_row, self.grid, path=anim_path
            )
            self.game.sfx.play("menu_select")
        else:
            # Feedback for invalid move target
            self.game.floating_text.add_info(
                self.grid.to_pixel(self.cursor_col, self.cursor_row)[0],
                self.grid.to_pixel(self.cursor_col, self.cursor_row)[1] - 30,
                t("out_of_reach"),
                settings.GRAY
            )

    def _get_enemy_at_cursor(self):
        enemies = [
            e for e in self.game.enemies
            if not e.dead and (e.col, e.row) == (self.cursor_col, self.cursor_row)
        ]
        if not enemies:
            return None
        real = [e for e in enemies if not getattr(e, 'is_decoy', False)]
        if real:
            return real[0]
        return enemies[0]

    def _get_enemies_at_cursor(self):
        return [
            e for e in self.game.enemies
            if not e.dead and (e.col, e.row) == (self.cursor_col, self.cursor_row)
        ]

    def _get_action_cells(self):
        pc = self.game.player.col
        pr = self.game.player.row
        st = self.game.skill_tree
        if self.selected_skill == "pitagoras":
            radius = st.get_skill_value("pitagoras", "range", settings.PITAGORAS_RANGE)
            return self.grid.get_cells_in_radius(pc, pr, radius)
        if self.selected_skill == "reflexao":
            radius = st.get_skill_value("reflexao", "range", settings.REFLEXAO_RANGE)
            return self.grid.get_cells_in_radius(pc, pr, radius)
        return [
            cell for cell in self.grid.get_cells_in_range(pc, pr, settings.BASIC_ATTACK_RANGE)
            if cell != (pc, pr)
        ]

    def _can_execute_cursor_action(self):
        action_cells = self._get_action_cells()
        if (self.cursor_col, self.cursor_row) not in action_cells:
            return False

        if self.selected_skill == "reflexao":
            return True

        return self._get_enemy_at_cursor() is not None

    def _confirm_action_cursor(self):
        is_self = (self.cursor_col, self.cursor_row) == (self.game.player.col, self.game.player.row)
        target_enemies = self._get_enemies_at_cursor()
        
        if is_self or (not target_enemies and self.selected_skill is None):
            self.turn_manager.player_acted = True
            self.show_action_range = False
            self.tiles_moved_this_turn = 0
            self.turn_log.append("Wait")
            self._start_enemy_turn()
            self.game.sfx.play("menu_select")
            self.game.floating_text.add_info(self.game.player.x, self.game.player.y - 40, t("wait"), settings.LIGHT_GRAY)
            return

        if not self._can_execute_cursor_action():
            self.game.floating_text.add_info(
                self.game.player.x,
                self.game.player.y - 30,
                t("out_of_range"),
                settings.GRAY,
            )
            return

        if self.selected_skill:
            success = self._execute_skill()
            if not success:
                self.game.floating_text.add_info(self.game.player.x, self.game.player.y - 40, t("not_enough_rigor"), settings.RED)
                self.game.sfx.play("error")
        else:
            self._execute_basic_attack(target_enemies=target_enemies)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            if self.state in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT"):
                self._set_cursor_from_mouse(event.pos)
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.state == "WAVE_INTRO" and event.button == 1:
                self._begin_room()
                return

            if self.state == "NO_COMBAT" and event.button == 1:
                self._leave_no_combat_room()
                return

            if event.button == 1 and self.state in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT"):
                if self._set_cursor_from_mouse(event.pos):
                    if self.state == "PLAYER_INPUT":
                        self._confirm_player_cursor()
                    else:
                        self._confirm_action_cursor()
                return

            if event.button == 3 and self.state == "PLAYER_ACTION_SELECT":
                self.selected_skill = None
                self.show_action_range = True
                return

        if event.type != pygame.KEYDOWN:
            return

        mods = pygame.key.get_mods()
        if (mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_ALT):
            self.game.player.toggle_skin()
            skin_name = self.game.player.skin_names[self.game.player.skin_index]
            self.game.floating_text.add_info(self.game.player.x, self.game.player.y - 40,
                                            t("class_label", name=skin_name), settings.CYAN)
            return

        if (mods & pygame.KMOD_CTRL):
            theme_idx = None
            if event.key == pygame.K_0: theme_idx = 0
            elif event.key == pygame.K_1: theme_idx = 1
            elif event.key == pygame.K_2: theme_idx = 2
            elif event.key == pygame.K_3: theme_idx = 3
            elif event.key == pygame.K_4: theme_idx = 4
            elif event.key == pygame.K_5: theme_idx = 5
            elif event.key == pygame.K_6: theme_idx = 6
            elif event.key == pygame.K_7: theme_idx = 7
            elif event.key == pygame.K_8: theme_idx = 8
            elif event.key == pygame.K_9: theme_idx = 9
            
            if theme_idx is not None:
                theme_name = self.game.math_bg.set_theme(theme_idx)
                if theme_name:
                    self.game.floating_text.add_info(self.game.player.x, self.game.player.y - 40,
                                                    t("theme_label", name=theme_name), settings.GOLD)
                    self.game.sfx.play("menu_select")
                    
                    # Add extra feedback: particle burst and shake
                    self.game.particles.emit_burst(self.game.player.x, self.game.player.y, settings.WHITE, 20, 120, 0.5)
                    self.game.screen_shake = 0.2
                    self.game.shake_intensity = 5
                return

        if self.state == "WAVE_INTRO":
            self._begin_room()
            return

        if self.state == "NO_COMBAT":
            if event.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                self._leave_no_combat_room()
            return

        if event.key == pygame.K_ESCAPE:
            self.game.scene_manager.push("pause")
            return

        if event.key == pygame.K_TAB and self.state in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT"):
            self.game.scene_manager.push("skill_tree")
            return

        if event.key == pygame.K_r and self.state in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT"):
            self._try_rewind()
            return

        if self.state == "PLAYER_INPUT":
            self._handle_player_input(event)
        elif self.state == "PLAYER_ACTION_SELECT":
            self._handle_action_input(event)
        elif self.state == "VICTORY_TRANSITION":
            pass
        elif self.state == "GAME_OVER_TRANSITION":
            if event.type == pygame.KEYDOWN:
                self.game.scene_manager.switch("game_over")

    def _handle_player_input(self, event):
        k = event.key

        if k in (pygame.K_w, pygame.K_UP):
            self.cursor_row = max(0, self.cursor_row - 1)
        elif k in (pygame.K_s, pygame.K_DOWN):
            self.cursor_row = min(self.grid.rows - 1, self.cursor_row + 1)
        elif k in (pygame.K_a, pygame.K_LEFT):
            self.cursor_col = max(0, self.cursor_col - 1)
        elif k in (pygame.K_d, pygame.K_RIGHT):
            self.cursor_col = min(self.grid.cols - 1, self.cursor_col + 1)

        if k in (pygame.K_RETURN, pygame.K_SPACE):
            self._confirm_player_cursor()
            return

        if k == pygame.K_r:
            self._rewind_turn()
            return

    def _handle_action_input(self, event):
        k = event.key

        if k in (pygame.K_w, pygame.K_UP):
            self.cursor_row = max(0, self.cursor_row - 1)
        elif k in (pygame.K_s, pygame.K_DOWN):
            self.cursor_row = min(self.grid.rows - 1, self.cursor_row + 1)
        elif k in (pygame.K_a, pygame.K_LEFT):
            self.cursor_col = max(0, self.cursor_col - 1)
        elif k in (pygame.K_d, pygame.K_RIGHT):
            self.cursor_col = min(self.grid.cols - 1, self.cursor_col + 1)

        if k in (pygame.K_SPACE, pygame.K_RETURN):
            self._confirm_action_cursor()
        elif k == pygame.K_x:
            # Dedicated Wait key
            self.cursor_col, self.cursor_row = self.game.player.col, self.game.player.row
            self._confirm_action_cursor()
        elif k == pygame.K_1:
            if self.game.skill_tree.is_unlocked("pitagoras"):
                self._toggle_skill("pitagoras")
        elif k == pygame.K_2:
            if self.game.skill_tree.is_unlocked("reflexao"):
                self._toggle_skill("reflexao")
        elif k == pygame.K_r:
            self._rewind_turn()

    def _execute_basic_attack(self, target_enemies=None):
        pc = self.game.player.col
        pr = self.game.player.row
        hit_enemies = []

        if target_enemies is not None:
            for enemy in target_enemies:
                d = self.grid.grid_distance(pc, pr, enemy.col, enemy.row)
                if d <= settings.BASIC_ATTACK_RANGE and not self.grid.is_level_change(pc, pr, enemy.col, enemy.row):
                    hit_enemies.append(enemy)
        else:
            for enemy in self.game.enemies:
                if enemy.dead:
                    continue
                d = self.grid.grid_distance(pc, pr, enemy.col, enemy.row)
                if d <= settings.BASIC_ATTACK_RANGE and not self.grid.is_level_change(pc, pr, enemy.col, enemy.row):
                    hit_enemies.append(enemy)

        if hit_enemies:
            is_crit = self.game.player.check_crit()
            st = self.game.skill_tree
            axioma_bonus = st.get_skill_value("axioma", "damage_bonus", 0)
            derivada_mult = st.get_skill_value("derivada", "move_damage_mult", 1.0)
            move_bonus = 1.0 + (derivada_mult - 1.0) * self.tiles_moved_this_turn

            for enemy in hit_enemies:
                base_dmg = (self.game.player.base_damage + axioma_bonus) * move_bonus
                if is_crit:
                    dmg = int(base_dmg * settings.PLAYER_CRIT_MULTIPLIER)
                else:
                    dmg = int(base_dmg)
                
                dx = abs(enemy.col - pc)
                dy = abs(enemy.row - pr)
                dist_formula = f"d={dx}+{dy}={dx+dy}" if dx + dy < 5 else f"|v|={dx+dy}"
                if self.tiles_moved_this_turn > 0:
                    dist_formula = f"f'={self.tiles_moved_this_turn} -> " + dist_formula
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
            
            if is_crit:
                self.crits_this_room += 1
                if self.crits_this_room >= 3:
                    from achievement_manager import AchievementManager
                    AchievementManager().unlock("crit_thinking", settings.DIFFICULTY)
            
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
            target_enemy = self._get_enemy_at_cursor()
            if target_enemy is None:
                return False
            if not self.game.player.pitagoras_attack():
                return False
            hit = False
            dx = abs(self.cursor_col - pc)
            dy = abs(self.cursor_row - pr)
            is_crit = self.game.player.check_crit()
            st = self.game.skill_tree
            dmg_base = st.get_skill_value("pitagoras", "damage", settings.PITAGORAS_DAMAGE)
            derivada_mult = st.get_skill_value("derivada", "move_damage_mult", 1.0)
            move_bonus = 1.0 + (derivada_mult - 1.0) * self.tiles_moved_this_turn
            
            self.game.floating_text.add_formula(
                self.game.player.x, self.game.player.y - 30,
                f"a^2+b^2=c^2  ({dx}^2+{dy}^2={dx*dx+dy*dy})",
                settings.GOLD if is_crit else settings.YELLOW
            )
            if not self.grid.is_level_change(pc, pr, target_enemy.col, target_enemy.row):
                dmg = int(dmg_base * move_bonus)
                if is_crit: dmg = int(dmg * settings.PLAYER_CRIT_MULTIPLIER)
                target_enemy.take_damage(dmg)
                self.game.floating_text.add_enemy_damage(target_enemy.x, target_enemy.y, dmg, is_crit)
                self.game.particles.emit_burst(target_enemy.x, target_enemy.y, settings.YELLOW, 12, 80, 0.4)
                self.game.screen_shake = 0.12 if is_crit else 0.08
                self.game.shake_intensity = 7 if is_crit else 5
                self.game.sfx.play("enemy_hit")
                hit = True
                if target_enemy.dead:
                    self._on_enemy_death(target_enemy)
            else:
                self.game.floating_text.add_evasion(target_enemy.x, target_enemy.y)
            
            if is_crit:
                self.crits_this_room += 1
                if self.crits_this_room >= 3:
                    from achievement_manager import AchievementManager
                    AchievementManager().unlock("crit_thinking", settings.DIFFICULTY)

            self.turn_log.append(f"Pitagoras{' (CRIT!)' if is_crit else ''}" if hit else "Pitagoras Miss")
            self.game.sfx.play("pitagoras")

        elif skill == "reflexao":
            if not self.game.player.reflexao_attack():
                return False
            
            # Area damage
            st = self.game.skill_tree
            radius = st.get_skill_value("reflexao", "range", settings.REFLEXAO_RANGE)
            target_cells = self.grid.get_cells_in_radius(pc, pr, radius)
            hit_count = 0
            dmg_base = st.get_skill_value("reflexao", "damage", settings.REFLEXAO_DAMAGE)
            derivada_mult = st.get_skill_value("derivada", "move_damage_mult", 1.0)
            move_bonus = 1.0 + (derivada_mult - 1.0) * self.tiles_moved_this_turn
            
            is_crit = self.game.player.check_crit()
            dmg = int(dmg_base * move_bonus)
            if is_crit: 
                dmg = int(dmg * settings.PLAYER_CRIT_MULTIPLIER)
            
            for enemy in self.game.enemies:
                if not enemy.dead and (enemy.col, enemy.row) in target_cells:
                    enemy.take_damage(dmg)
                    self.game.floating_text.add_formula(enemy.x, enemy.y - 30, "theta_i=theta_r", settings.CYAN)
                    self.game.floating_text.add_enemy_damage(enemy.x, enemy.y, dmg, is_crit)
                    self.game.particles.emit_burst(enemy.x, enemy.y, settings.CYAN, 8, 60, 0.3)
                    hit_count += 1
                    if enemy.dead:
                        self._on_enemy_death(enemy)
            
            if is_crit:
                self.crits_this_room += 1
                if self.crits_this_room >= 3:
                    from achievement_manager import AchievementManager
                    AchievementManager().unlock("crit_thinking", settings.DIFFICULTY)

            # Effects
            self.game.particles.emit_burst(
                self.game.player.x, self.game.player.y, settings.CYAN, 30, 120, 0.5
            )
            self.game.screen_shake = 0.15
            self.game.shake_intensity = 6
            self.game.floating_text.add_formula(
                self.game.player.x, self.game.player.y - 30,
                "Pulse: sum(E) in area", settings.CYAN
            )
            self.game.sfx.play("reflexao")
            self.turn_log.append(f"Reflexao hit {hit_count} enemies")

        self.turn_manager.player_acted = True
        self.show_action_range = False
        self.selected_skill = None
        self._start_enemy_turn()
        return True

    def _rewind_turn(self):
        if not self.game.skill_tree.is_unlocked("ctrlz"):
            self.game.floating_text.add_info(self.game.player.x, self.game.player.y - 40, "SKILL LOCKED", settings.GRAY)
            return
        
        if not self.turn_manager.can_undo():
            self.game.floating_text.add_info(self.game.player.x, self.game.player.y - 40, "CAN'T UNDO", settings.RED)
            return

        st = self.game.skill_tree
        steps = st.get_skill_value("ctrlz", "undo_turns", settings.REWIND_UNDO_TURNS)
        
        snapshot = self.turn_manager.undo(steps=steps)
        if snapshot:
            # Restore Player
            self.game.player.col = snapshot["player"]["col"]
            self.game.player.row = snapshot["player"]["row"]
            self.game.player.hp = snapshot["player"]["hp"]
            self.game.player.rigor = snapshot["player"]["rigor"]
            self.game.player.x, self.game.player.y = self.grid.to_pixel(self.game.player.col, self.game.player.row)
            
            # Restore Enemies
            # Note: TurnManager stores a copy of enemy state. 
            # We match them by index for consistency.
            for i, enemy_data in enumerate(snapshot["enemies"]):
                if i < len(self.game.enemies):
                    e = self.game.enemies[i]
                    e.col = enemy_data["col"]
                    e.row = enemy_data["row"]
                    e.hp = enemy_data["hp"]
                    e.max_hp = enemy_data["max_hp"]
                    e.alive = enemy_data["alive"]
                    e.dead = enemy_data["dead"]
                    e.x, e.y = self.grid.to_pixel(e.col, e.row)
                    e.current_anim = "idle"
                    e.anim_timer = 0
            
            # Restore Entropy and other state
            self.game.entropy = snapshot["entropy"]
            self.grid.clear_barriers()
            for bc in snapshot["barrier_cells"]:
                self.grid.mark_barrier(bc[0], bc[1], True)

            # Apply penalty: Increase entropy
            st = self.game.skill_tree
            reduction = st.get_skill_value("entropia", "reduction", 0)
            penalty = int(settings.REWIND_ENTROPY_INCREASE * (1.0 - reduction))
            
            self.game.entropy = min(settings.MAX_ENTROPY, self.game.entropy + penalty)
            self.turn_manager.rewind_cooldown_turns = settings.REWIND_COOLDOWN_TURNS
            
            # Bonus HP Regeneration
            heal_bonus = st.get_skill_value("ctrlz", "heal", settings.REWIND_HEAL_AMOUNT)
            old_hp = self.game.player.hp
            self.game.player.hp = min(self.game.player.max_hp, self.game.player.hp + heal_bonus)
            actual_heal = self.game.player.hp - old_hp
            
            # Visuals and feedback
            self.game.sfx.play("reflexao") # Glitchy sound
            self.game.screen_shake = 0.2
            self.game.shake_intensity = 8
            self.game.floating_text.add_formula(
                self.game.player.x, self.game.player.y - 40,
                f"S = S_0 + {penalty}", settings.PURPLE
            )
            self.turn_log.append("Rewind")
            self.game.floating_text.add_info(self.game.player.x, self.game.player.y - 60, "CTRL+Z REWIND", settings.CYAN)
            if actual_heal > 0:
                self.game.floating_text.add_info(self.game.player.x, self.game.player.y - 80, f"+{actual_heal} HP", settings.GREEN)
            
            self.game.particles.emit_burst(self.game.player.x, self.game.player.y, settings.CYAN, 20, 100, 0.5)
            self.game.screen_shake = 0.2
            self.game.shake_intensity = 8
            
            # Reset UI state
            self.state = "PLAYER_INPUT"
            self.turn_manager.start_turn()
            self.show_move_range = True
            self.show_action_range = False
            self.selected_skill = None
            self.cursor_col, self.cursor_row = self.game.player.col, self.game.player.row
            self._generate_enemy_intents()
            
            # Special: log it
            self.turn_log.append(f"REWIND to Turn {self.turn_manager.turn_number}")

    def _on_enemy_death(self, enemy):
        self.game.floating_text.add_formula(
            enemy.x, enemy.y,
            t("eliminated"), settings.GREEN
        )
        self.game.particles.emit_burst(enemy.x, enemy.y, enemy.color, 15, 80, 0.4)
        self.game.floating_text.add_info(enemy.x, enemy.y, t("qed"), settings.GREEN)
        self.game.screen_shake = 0.1
        self.game.shake_intensity = 4
        self.game.sfx.play("enemy_die")
        self.last_enemy_death_pos = (enemy.x, enemy.y)
        
        # Award EXP
        exp_reward = 0
        if enemy.type == "censor": exp_reward = settings.ENEMY_EXP_CENSOR
        elif enemy.type == "strawman": exp_reward = settings.ENEMY_EXP_STRAWMAN
        elif enemy.type == "bayesian": exp_reward = settings.ENEMY_EXP_BAYESIAN
        elif enemy.type == "boss": exp_reward = settings.ENEMY_EXP_BOSS

        if self.game.player.add_exp(exp_reward):
            self.game.floating_text.add_info(self.game.player.x, self.game.player.y - 60,
                                            f"LEVEL UP! ({self.game.player.level})", settings.GOLD)
            self.game.sfx.play("victory")
            self.game.particles.emit_burst(self.game.player.x, self.game.player.y, settings.GOLD, 20, 100, 0.5)

        self._check_victory()

    def _check_victory(self):
        alive = [e for e in self.game.enemies if not e.dead]
        if len(alive) == 0 and self.state != "VICTORY_TRANSITION":
            self.state = "VICTORY_TRANSITION"
            self.victory_timer = 0
            pos = self.last_enemy_death_pos or (self.game.player.x, self.game.player.y)
            self.game.particles.emit_burst(pos[0], pos[1], settings.GOLD, 30, 100, 0.8)
            
            self.game.floating_text.add_info(pos[0], pos[1] - 40, 
                                            t("earned_skill_point"), settings.GOLD)
            self.game.tts.speak(t("earned_skill_point"), lang=settings.LANGUAGE)
            self.game.skill_tree.add_points(1)

            from achievement_manager import AchievementManager
            mgr = AchievementManager()
            mgr.unlock("first_room", settings.DIFFICULTY)
            
            if not self.player_took_damage_this_room:
                mgr.unlock("no_damage", settings.DIFFICULTY)
            
            if self.turn_manager.turn_number < 10:
                mgr.unlock("fast_win", settings.DIFFICULTY)
                
            if self.game.current_room and (self.game.current_room.type == "victory" or getattr(self.game.current_room, "is_final_gate", False)):
                mgr.unlock("math_god", settings.DIFFICULTY)

    def _start_enemy_turn(self):
        if self.state == "VICTORY_TRANSITION":
            return

        self.grid.lock_danger_indicators(self.enemy_intents)
        self.danger_locked = True
        self.lock_timer = 0
        self.state = "LOCK_INDICATORS"

    def update(self, dt):
        self.cursor_timer += dt

        if self.game.rewind_fx_timer > 0:
            self.game.rewind_fx_timer -= dt
        
        # Update Camera to follow player first, so hover checks use current frame's camera
        target_cam_x = self.game.player.x - settings.WINDOW_WIDTH / 2
        target_cam_y = self.game.player.y - (settings.WINDOW_HEIGHT - settings.UI_BAR_HEIGHT) / 2
        
        max_cam_x = max(0, self.grid.width + settings.ARENA_OFFSET_X * 2 - settings.WINDOW_WIDTH)
        max_cam_y = max(0, self.grid.height + settings.ARENA_OFFSET_Y * 2 - (settings.WINDOW_HEIGHT - settings.UI_BAR_HEIGHT))
        
        self.camera_x = max(0, min(max_cam_x, target_cam_x))
        self.camera_y = max(0, min(max_cam_y, target_cam_y))

        self.game.player.update_animation(dt, self.grid)
        self.game.player.update(dt, {})

        for enemy in self.game.enemies:
            enemy.update_animation(dt, self.grid)
            enemy.snap_to_grid(self.grid)
            enemy.bob_phase += dt * 3
            enemy.spawn_timer = max(0, enemy.spawn_timer - dt)
            enemy.flash_timer = max(0, enemy.flash_timer - dt)
            if enemy.type == "boss":
                enemy.pulse_timer += dt * 2
        # ────────────────────────────────────────────────────────────────



        self.game.particles.update(dt)
        self.game.floating_text.update(dt)

        # Mouse hover detection for enemies
        # mouse_pos is screen-space; enemy hitboxes are world-space,
        # so we must offset by the camera to compare correctly.
        old_hovered = getattr(self, 'hovered_enemy', None)
        screen_mouse = pygame.mouse.get_pos()
        world_mouse = (screen_mouse[0] + self.camera_x,
                       screen_mouse[1] + self.camera_y)
        self.hovered_enemy = None
        for enemy in self.game.enemies:
            if enemy.dead:
                continue
            hitbox = enemy.get_hitbox()
            if hitbox.collidepoint(world_mouse):
                self.hovered_enemy = enemy
                break

        
        if self.hovered_enemy and self.hovered_enemy != old_hovered:
            text = f"{t(self.hovered_enemy.info_title)}. {t(self.hovered_enemy.lore)}"
            self.game.tts.speak(text, lang=settings.LANGUAGE)

        # Lore Toast Management
        if self.lore_toast:
            self.lore_toast.update(dt)
            if self.lore_toast.is_dead():
                self.lore_toast = None
        elif settings.SHOW_LORE_TOASTS:
            self.lore_timer -= dt
            if self.lore_timer <= 0:
                from lore_data import SHORT_LORE_SNIPPETS
                snippet = random.choice(SHORT_LORE_SNIPPETS)
                # Get localized text
                text = snippet["text"].get(settings.LANGUAGE, snippet["text"].get("en", "Lore error"))
                from ui import LoreToast
                self.lore_toast = LoreToast(text, snippet["title"])
                self.lore_timer = random.uniform(40, 90) # Next one in 40-90 seconds
                
                # TTS for lore toast
                self.game.tts.speak(text, lang=settings.LANGUAGE)

        # Hover detection for enemies and intents
        mx, my = pygame.mouse.get_pos()
        world_mx = mx + self.camera_x
        world_my = my + self.camera_y
        grid_mx, grid_my = self.grid.to_grid(world_mx, world_my)
        
        arena_rect = pygame.Rect(
            settings.ARENA_OFFSET_X, settings.ARENA_OFFSET_Y,
            self.grid.width, self.grid.height
        )
        self.game.math_bg.update(dt, arena_rect)

        self.game.screen_shake = max(0, self.game.screen_shake - dt)
        if self.game.screen_shake > 0:
            self.game.shake_intensity = max(1, self.game.shake_intensity * 0.9)

        self.hovered_enemy = None
        for enemy in self.game.enemies:
            if not enemy.dead and enemy.get_hitbox().collidepoint(world_mx, world_my):
                self.hovered_enemy = enemy
                break
        
        self.hovered_intent_data = None
        if self.state in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT"):
            # Check danger tiles
            for col, row, ttype, is_fake, lmode in self.grid.danger_tiles:
                if (col, row) == (grid_mx, grid_my):
                    self.hovered_intent_data = ("attack", is_fake)
                    break
            
            # Check movement arrows
            if not self.hovered_intent_data:
                for intent in self.enemy_intents:
                    if intent and not intent.enemy.dead and intent.move_target:
                        tx, ty = self.grid.to_pixel(intent.move_target[0], intent.move_target[1])
                        if math.hypot(world_mx - tx, world_my - ty) < 15:
                            self.hovered_intent_data = ("move", False)
                            break
            
            # Check player reachable/targetable tiles
            if not self.hovered_intent_data:
                pc, pr = self.game.player.col, self.game.player.row
                if self.state == "PLAYER_INPUT":
                    reachable = self.grid.get_reachable_cells(pc, pr, self.game.player.move_range)
                    if (grid_mx, grid_my) in reachable:
                        self.hovered_intent_data = ("player_move", False)
                elif self.state == "PLAYER_ACTION_SELECT":
                    # Determine range based on selected skill or basic attack
                    range_val = settings.BASIC_ATTACK_RANGE
                    if self.selected_skill == "pitagoras": range_val = settings.PITAGORAS_RANGE
                    elif self.selected_skill == "reflexao": range_val = settings.REFLEXAO_RANGE
                    
                    targetable = self.grid.get_cells_in_range(pc, pr, range_val)
                    if (grid_mx, grid_my) in targetable:
                        self.hovered_intent_data = ("player_attack", False)

        if self.state == "RESOLVE_MOVE":
            if self.pending_player_col is not None and not self.game.player.is_animating():
                if self.pending_player_col is not None:
                    self.game.player.col = self.pending_player_col
                    self.game.player.row = self.pending_player_row
                    self.game.player.x, self.game.player.y = self.grid.to_pixel(
                        self.pending_player_col, self.pending_player_row
                    )
                    self.pending_player_col = None
                    self.pending_player_row = None
                self._enter_action_select()
                self._generate_enemy_intents()

        elif self.state == "LOCK_INDICATORS":
            self.lock_timer += dt
            if self.lock_timer >= settings.INDICATOR_LOCK_DURATION:
                self.grid.clear_danger_tiles()
                self.danger_locked = False
                self.state = "ENEMY_TURN"
                self.enemy_actions = []
                self.enemy_resolve_idx = 0
                self.enemy_phase = "MOVE"
                self.enemy_pending_attack = None
                self.enemy_attack_delay_timer = 0

                for intent in self.enemy_intents:
                    if intent is None or intent.enemy.dead:
                        continue
                    action = intent.to_action()
                    if action:
                        self.enemy_actions.append((intent.enemy, action))

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
                    # If victory room (and all requirements met) OR final boss gate completed, go to victory screen
                    if (self.game.current_room.type == "victory" and self.game.world_map.all_required_rooms_completed()) or \
                       getattr(self.game.current_room, "is_final_gate", False):
                        self.game.scene_manager.switch("victory")
                    else:
                        self.game.scene_manager.switch("map")
                else:
                    self.game.scene_manager.switch("victory")

        elif self.state == "GAME_OVER_TRANSITION":
            self.game_over_timer += dt
            self.game.player.flash_timer = max(0, self.game.player.flash_timer - dt)
            if self.game_over_timer >= settings.GAME_OVER_TRANSITION_DURATION:
                self.game.scene_manager.switch("game_over")

        if self.state == "PLAYER_INPUT" or self.state == "PLAYER_ACTION_SELECT":
            self.game.entropy = min(settings.MAX_ENTROPY,
                                    self.game.entropy + settings.ENTROPY_PER_TURN * dt * 0.1)

    def _resolve_enemy_turn(self, dt):
        if self.enemy_resolve_idx >= len(self.enemy_actions):
            self.enemy_phase = None
            self.state = "TURN_END"
            return

        if self.game.player.hp <= 0:
            self.enemy_phase = None
            self.state = "TURN_END"
            return

        if self.enemy_pending_attack is not None:
            self.enemy_phase = "ATTACK"
            enemy, attack_type, action = self.enemy_pending_attack
            if enemy.is_animating():
                return
            self.enemy_attack_delay_timer += dt
            if self.enemy_attack_delay_timer < self.ENEMY_ATTACK_DELAY:
                return
            self.enemy_pending_attack = None
            self.enemy_attack_delay_timer = 0
            if attack_type == "attack":
                self._enemy_attack(enemy)
            elif attack_type == "line_attack":
                self._enemy_line_attack(enemy, action)
            elif attack_type == "area_attack":
                self._enemy_area_attack(enemy, action)
            elif attack_type == "cross_attack":
                self._enemy_cross_attack(enemy)
            elif attack_type == "ranged_line_attack":
                self._enemy_ranged_line_attack(enemy)
            self.enemy_resolve_idx += 1
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
            self.enemy_phase = "MOVE"
            self.turn_log.append(f"{enemy.type} waits")
        elif action["type"] == "move":
            self.enemy_phase = "MOVE"
            tc, tr = action["target_col"], action["target_row"]
            if self.grid.is_valid(tc, tr) and not self.grid.is_blocked(tc, tr, include_barriers=True):
                if not self.grid.is_level_change(enemy.col, enemy.row, tc, tr):
                    old_col, old_row = enemy.col, enemy.row
                    anim_path = self._build_anim_path(old_col, old_row, tc, tr, include_barriers=True)
                    enemy.start_move_anim(old_col, old_row, tc, tr, self.grid, path=anim_path)
                    enemy.col = tc
                    enemy.row = tr
                    self.turn_log.append(f"{enemy.type} moved")
                else:
                    self.turn_log.append(f"{enemy.type} can't reach")
            else:
                self.turn_log.append(f"{enemy.type} blocked")

        elif action["type"] == "move_then_attack":
            self.enemy_phase = "MOVE"
            tc, tr = action["target_col"], action["target_row"]
            moved = False
            if self.grid.is_valid(tc, tr) and not self.grid.is_blocked(tc, tr, include_barriers=True):
                if not self.grid.is_level_change(enemy.col, enemy.row, tc, tr):
                    old_col, old_row = enemy.col, enemy.row
                    anim_path = self._build_anim_path(old_col, old_row, tc, tr, include_barriers=True)
                    enemy.start_move_anim(old_col, old_row, tc, tr, self.grid, path=anim_path)
                    enemy.col = tc
                    enemy.row = tr
                    self.turn_log.append(f"{enemy.type} moved")
                    moved = True
                else:
                    self.turn_log.append(f"{enemy.type} can't reach")
            else:
                self.turn_log.append(f"{enemy.type} blocked")
            if moved:
                attack_type = "attack"
                if enemy.type == "ortogonal":
                    attack_type = "cross_attack"
                elif enemy.type == "atirador":
                    attack_type = "ranged_line_attack"
                elif enemy.type == "granadeiro":
                    attack_type = "area_attack"
                self.enemy_pending_attack = (enemy, attack_type, action)
                self.enemy_attack_delay_timer = 0
                self.enemy_phase = "ATTACK"
                return

        elif action["type"] == "attack":
            self.enemy_phase = "ATTACK"
            if enemy.type == "ortogonal":
                self._enemy_cross_attack(enemy)
            elif enemy.type == "atirador":
                self._enemy_ranged_line_attack(enemy)
            else:
                self._enemy_attack(enemy)

        elif action["type"] == "line_attack":
            self.enemy_phase = "ATTACK"
            if enemy.type == "boss":
                self._enemy_line_attack(enemy, action)
            else:
                self._enemy_ranged_line_attack(enemy)

        elif action["type"] == "area_attack":
            self.enemy_phase = "ATTACK"
            self._enemy_area_attack(enemy, action)

        elif action["type"] == "cross_attack":
            self.enemy_phase = "ATTACK"
            self._enemy_cross_attack(enemy)

        self.enemy_resolve_idx += 1

    def _enemy_attack(self, enemy):
        pc = self.game.player.col
        pr = self.game.player.row
        d = self.grid.grid_distance(enemy.col, enemy.row, pc, pr)

        if d <= enemy.attack_range and not self.grid.is_level_change(enemy.col, enemy.row, pc, pr):
            dmg = enemy.roll_damage(self.game.entropy)
            dx = abs(pc - enemy.col)
            dy = abs(pr - enemy.row)
            if self.game.player.take_damage(dmg):
                self.player_took_damage_this_room = True
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

    def _enemy_cross_attack(self, enemy):
        pc = self.game.player.col
        pr = self.game.player.row
        ec, er = enemy.col, enemy.row
        hit_cells = [(ec, er - 1), (ec, er + 1), (ec - 1, er), (ec + 1, er)]
        player_hit = (pc, pr) in hit_cells and not self.grid.is_level_change(ec, er, pc, pr)
        if player_hit:
            dmg = enemy.roll_damage()
            if self.game.player.take_damage(dmg):
                self.player_took_damage_this_room = True
                self.game.floating_text.add_damage(self.game.player.x, self.game.player.y, dmg, enemy.last_crit)
                self.game.particles.emit_burst(self.game.player.x, self.game.player.y, settings.RED, 10, 60, 0.3)
                self.game.screen_shake = 0.15 if enemy.last_crit else 0.1
                self.game.shake_intensity = 8 if enemy.last_crit else 6
                self.game.sfx.play("player_hit")
                self.turn_log.append(f"Ortogonal cross hit for {dmg}{' (CRIT!)' if enemy.last_crit else ''}")
        for cx, cy in hit_cells:
            if self.grid.is_valid(cx, cy):
                px, py = self.grid.to_pixel(cx, cy)
                self.game.particles.emit_burst(px, py, settings.ORANGE, 5, 40, 0.3)
        self.game.sfx.play("hit")

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
        dmg = enemy.roll_damage(self.game.entropy)
        self.game.floating_text.add_formula(
            enemy.x, enemy.y - 30,
            f"Phase {['I','II','III'][phase-1]} -> |v|={count}",
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
                    self.player_took_damage_this_room = True
                    self.game.floating_text.add_damage(self.game.player.x, self.game.player.y, dmg, enemy.last_crit)
                    self.game.particles.emit_burst(self.game.player.x, self.game.player.y, settings.RED, 10, 60, 0.3)
                    self.game.screen_shake = 0.15
                    self.game.shake_intensity = 6
                    self.game.sfx.play("player_hit")
                    self.turn_log.append(f"Boss line attack hit for {dmg}!")

        self.game.particles.emit_burst(enemy.x, enemy.y, (255, 100, 100), 10, 50, 0.3)
        self.game.sfx.play("pitagoras")
        self.turn_log.append(f"Boss line attack")

    def _enemy_ranged_line_attack(self, enemy):
        pc = self.game.player.col
        pr = self.game.player.row
        ec, er = enemy.col, enemy.row
        dc = pc - ec
        dr = pr - er
        if dc == 0 and dr == 0:
            return
        step_dc = 1 if dc > 0 else (-1 if dc < 0 else 0)
        step_dr = 1 if dr > 0 else (-1 if dr < 0 else 0)
        range_val = enemy.attack_range
        dmg = enemy.roll_damage()
        hit = False

        self.game.floating_text.add_formula(
            enemy.x, enemy.y - 30,
            f"|v|={range_val}", settings.YELLOW
        )

        for i in range(1, range_val + 1):
            c = ec + step_dc * i
            r = er + step_dr * i
            if not self.grid.is_valid(c, r):
                break
            if self.grid.is_blocked(c, r):
                break
            px, py = self.grid.to_pixel(c, r)
            self.game.particles.emit_burst(px, py, settings.ORANGE, 3, 30, 0.2)
            if c == pc and r == pr:
                if not self.grid.is_level_change(ec, er, c, r):
                    if self.game.player.take_damage(dmg):
                        self.player_took_damage_this_room = True
                        self.game.floating_text.add_damage(self.game.player.x, self.game.player.y, dmg, enemy.last_crit)
                        self.game.particles.emit_burst(self.game.player.x, self.game.player.y, settings.RED, 8, 50, 0.3)
                        self.game.screen_shake = 0.12
                        self.game.shake_intensity = 5
                        self.game.sfx.play("player_hit")
                        hit = True

        self.game.sfx.play("hit")
        self.turn_log.append(f"Atirador line attack{' hit!' if hit else ' missed'}")

    def _enemy_area_attack(self, enemy, action):
        tc, tr = action["target_col"], action["target_row"]
        radius = 2
        dmg = enemy.roll_damage(self.game.entropy)
        hit = False
        self.game.floating_text.add_formula(
            enemy.x, enemy.y - 30,
            f"int dA  r={radius}", settings.RED
        )
        for col in range(tc - radius, tc + radius + 1):
            for row in range(tr - radius, tr + radius + 1):
                if col == self.game.player.col and row == self.game.player.row:
                    if self.game.player.take_damage(dmg):
                        self.player_took_damage_this_room = True
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
        # Apply regeneration first
        self.game.player.rigor = min(
            self.game.player.max_rigor,
            self.game.player.rigor + settings.RIGOR_REGEN_RATE
        )
        self.game.floating_text.add_rigor(
            self.game.player.x, self.game.player.y - 20,
            settings.RIGOR_REGEN_RATE
        )
        self.grid.clear_barriers()

        # Check for room completion or death before taking snapshot for next turn
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
            self.state = "GAME_OVER_TRANSITION"
            self.game_over_timer = 0
            self.game.particles.emit_burst(
                self.game.player.x, self.game.player.y, settings.RED, 20, 80, 0.5
            )
            self.game.screen_shake = 0.3
            self.game.shake_intensity = 10
            self.game.sfx.play("player_hit")
            return

        # Prepare for next turn and take snapshot
        self.state = "PLAYER_INPUT"
        self.turn_manager.start_turn()
        self.show_move_range = True
        self.show_action_range = False
        self.selected_skill = None
        self._generate_enemy_intents()
        self.danger_locked = False
        
        # Snapshot the state at the START of the new turn
        gs = self._get_game_state()
        self.turn_manager.end_turn(gs) # This handles turn increment and history

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
            "player_obj": self.game.player,
        }

    def _save_rewind_state(self):
        gs = self._get_game_state()
        self.turn_manager.snapshot(gs)

    def _try_rewind(self):
        if not self.game.skill_tree.is_unlocked("ctrlz"):
            self.game.floating_text.add_info(
                self.game.player.x, self.game.player.y - 40,
                t("rewind_locked"), settings.RED
            )
            self.game.sfx.play("error")
            return
        if not self.turn_manager.can_undo():
            self.game.floating_text.add_info(
                self.game.player.x, self.game.player.y - 40,
                t("no_rewind_available"), settings.GRAY
            )
            self.game.sfx.play("error")
            return

        steps = 2 if len(self.turn_manager.history) >= 2 else 1
        snapshot = self.turn_manager.undo(steps)
        if snapshot is None:
            return

        self.game.player.col = snapshot["player"]["col"]
        self.game.player.row = snapshot["player"]["row"]
        self.game.player.hp = snapshot["player"]["hp"]
        self.game.player.max_hp = snapshot["player"]["max_hp"]
        self.game.player.hp = min(self.game.player.hp + 10, self.game.player.max_hp)
        self.game.player.rigor = snapshot["player"]["rigor"]
        self.game.player.x, self.game.player.y = self.grid.to_pixel(
            self.game.player.col, self.game.player.row
        )

        for i, e_snap in enumerate(snapshot["enemies"]):
            if i < len(self.game.enemies):
                enemy = self.game.enemies[i]
                enemy.col = e_snap["col"]
                enemy.row = e_snap["row"]
                enemy.hp = e_snap["hp"]
                enemy.max_hp = e_snap["max_hp"]
                enemy.alive = e_snap["alive"]
                enemy.dead = e_snap["dead"]
                enemy.x, enemy.y = self.grid.to_pixel(enemy.col, enemy.row)

        self.game.entropy = snapshot["entropy"]

        self.grid.clear_barriers()
        for col, row in snapshot.get("barrier_cells", []):
            self.grid.mark_barrier(col, row, True)

        self.game.entropy = min(
            self.game.entropy + settings.REWIND_ENTROPY_INCREASE,
            settings.MAX_ENTROPY
        )
        self.turn_manager.rewind_cooldown_turns = settings.REWIND_COOLDOWN_TURNS

        self.game.rewind_fx_timer = 1.0
        self.game.sfx.play("rewind")

        self.state = "PLAYER_INPUT"
        self.turn_manager.start_turn()
        self.show_move_range = True
        self.show_action_range = False
        self.selected_skill = None
        self._generate_enemy_intents()
        self.danger_locked = False

        self.game.floating_text.add_info(self.game.player.x, self.game.player.y - 40, "<< REWIND >>", settings.GREEN)
        self.game.floating_text.add_info(self.game.player.x, self.game.player.y - 60, "+10 HP", settings.GREEN)

    def _draw_derivada_preview(self, screen):
        pc = self.game.player.col
        pr = self.game.player.row

        for enemy in self.game.enemies:
            if enemy.dead:
                continue

            if enemy.type == "boss":
                self.grid.draw_vector_arrow(screen, enemy.col, enemy.row, pc, pr, settings.GREEN, 1)
                continue

            action = enemy.decide_action(pc, pr, self.grid, self.game.enemies)
            if not action:
                continue

            action_type = action.get("type")
            if action_type in ("move", "move_then_attack"):
                tc = action["target_col"]
                tr = action["target_row"]
                color = settings.YELLOW if action_type == "move_then_attack" else settings.GREEN
                self.grid.draw_vector_arrow(screen, enemy.col, enemy.row, tc, tr, color, 2)
                self.grid.draw(screen, highlight_cells=[(tc, tr)], highlight_color=color, highlight_outline=True)
                if action_type == "move_then_attack":
                    self.grid.draw(screen, highlight_cells=[(pc, pr)], highlight_color=settings.GREEN, highlight_outline=True)
            elif action_type in ("attack", "line_attack", "area_attack"):
                self.grid.draw_vector_arrow(screen, enemy.col, enemy.row, pc, pr, settings.GREEN, 1)
                self.grid.draw(screen, highlight_cells=[(pc, pr)], highlight_color=settings.GREEN, highlight_outline=True)

    def draw(self, screen):
        # Everything will be drawn to this large surface if needed, but 
        # actually we just draw to a window-sized surface with an offset.
        temp = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
        temp.fill(self.game.math_bg.get_bg_color())
        
        # Offset for all world objects
        world_offset = (-self.camera_x, -self.camera_y)

        arena_rect = pygame.Rect(
            settings.ARENA_OFFSET_X + world_offset[0], 
            settings.ARENA_OFFSET_Y + world_offset[1],
            self.grid.width, 
            self.grid.height
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
                    rect = self.grid.cell_rect(col, row)
                    rect.x += world_offset[0]
                    rect.y += world_offset[1]
                    scaled_w = rect.width
                    scaled_h = rect.height
                    if scale_x != 1.0 or scale_y != 1.0:
                        tile_surf = pygame.transform.scale(tile_surf, (scaled_w, scaled_h))
                    temp.blit(tile_surf, rect)
        else:
            pygame.draw.rect(temp, self.game.math_bg.get_arena_color(), arena_rect)

        pygame.draw.rect(temp, settings.COLOR_WALL, arena_rect, 2)

        for (col, row) in self.grid.blocked:
            rect = self.grid.cell_rect(col, row)
            rect.x += world_offset[0]
            rect.y += world_offset[1]
            obs_surf = pygame.Surface((int(rect.width), int(rect.height)))
            obs_surf.set_alpha(120)
            obs_surf.fill((20, 20, 40))
            temp.blit(obs_surf, rect)

        self.grid.draw_barriers(temp, offset=world_offset)

        self.game.math_bg.draw(temp, offset=world_offset)

        if self.state == "PLAYER_INPUT" and self.show_move_range:
            pc = self.game.player.col
            pr = self.game.player.row
            reachable = self.grid.get_reachable_cells(pc, pr, self.game.player.move_range)
            self.grid.draw(temp, highlight_cells=reachable, highlight_color=settings.BLUE, offset=world_offset)

        if self.state == "PLAYER_ACTION_SELECT" and self.show_action_range:
            if self.selected_skill == "pitagoras":
                cells = self.grid.get_cells_in_radius(
                    self.game.player.col, self.game.player.row,
                    settings.PITAGORAS_RANGE
                )
                self.grid.draw(temp, highlight_cells=cells, highlight_color=settings.YELLOW, offset=world_offset)
                self.grid.draw_triangle(temp,
                    self.game.player.col, self.game.player.row,
                    self.cursor_col, self.game.player.row,
                    self.cursor_col, self.cursor_row,
                    settings.YELLOW, 1, offset=world_offset)
            elif self.selected_skill == "reflexao":
                cells = self.grid.get_cells_in_radius(
                    self.game.player.col, self.game.player.row,
                    settings.REFLEXAO_RANGE
                )
                self.grid.draw(temp, highlight_cells=cells, highlight_color=settings.CYAN, offset=world_offset)
            else:
                cells = self.grid.get_cells_in_range(
                    self.game.player.col, self.game.player.row,
                    settings.BASIC_ATTACK_RANGE
                )
                self.grid.draw(temp, highlight_cells=cells, highlight_color=settings.RED, offset=world_offset)

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
                                               pred[0], pred[1], settings.GREEN, 2, offset=world_offset)
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
                                                   int(end_c), int(end_r), settings.GREEN, 1, offset=world_offset)

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
                                               pc, pr, settings.GOLD, 1, offset=world_offset)

        if self.state in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT", "LOCK_INDICATORS", "ENEMY_TURN"):
            self.grid.draw_danger_indicators(temp, pulse_timer=self.cursor_timer, offset=world_offset)
            self.grid.draw_intent_arrows(temp, self.enemy_intents, 
                                        player_skills=self._get_player_skill_ids() if self.state in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT") else None,
                                        offset=world_offset)

        for enemy in self.game.enemies:
            enemy.draw(temp, offset=world_offset)

        self.game.player.draw(temp, offset=world_offset)

        cursor_rect = self.grid.cell_rect(self.cursor_col, self.cursor_row)
        cursor_rect.x += world_offset[0]
        cursor_rect.y += world_offset[1]
        cursor_alpha = int(100 + 80 * math.sin(self.cursor_timer * 4))
        s = pygame.Surface((cursor_rect.width, cursor_rect.height))
        s.set_alpha(cursor_alpha)
        s.fill(settings.WHITE)
        temp.blit(s, cursor_rect)
        pygame.draw.rect(temp, settings.WHITE, cursor_rect, 2)

        self.game.particles.draw(temp, offset=world_offset)
        self.game.floating_text.draw(temp, offset=world_offset)

        self._draw_cursor_info(temp)
        self._draw_turn_hud(temp)

        if self.hovered_enemy:
            self.game.ui.draw_enemy_tooltip(temp, self.hovered_enemy, pygame.mouse.get_pos())
        elif self.hovered_intent_data:
            itype, is_fake = self.hovered_intent_data
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

        if self.lore_toast:
            self.game.ui.draw_lore_toast(screen, self.lore_toast)

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

        if self.state == "GAME_OVER_TRANSITION":
            progress = min(1.0, self.game_over_timer / settings.GAME_OVER_TRANSITION_DURATION)
            fade = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
            fade.set_alpha(int(200 * progress))
            fade.fill(settings.BLACK)
            screen.blit(fade, (0, 0))

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

        # Position info box at the top right of the screen
        info_x = settings.WINDOW_WIDTH - 180
        if info_x < 0:
            info_x = 10

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

        reachable = self.grid.get_reachable_cells(pc, pr, self.game.player.move_range)
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
            move_label = tilted_font.render(f"dpos({dx:+d},{dy:+d}) d={dist}", True, settings.BLUE)
            screen.blit(move_label, (info_x, info_y + 4))

        if self.state == "PLAYER_ACTION_SELECT":
            if self.selected_skill == "pitagoras":
                eucl_dist = math.sqrt(dx * dx + dy * dy)
                skill_label = tilted_font.render(
                    f"a^2+b^2=c^2  c={eucl_dist:.1f}", True, settings.YELLOW)
                screen.blit(skill_label, (info_x, info_y + 4))
            elif self.selected_skill == "reflexao":
                skill_label = tilted_font.render(
                    "theta_i=theta_r (reflect)", True, settings.CYAN)
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
                ex += self.camera_x * -1 # Apply offset
                ey += self.camera_y * -1
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
        if not self.turn_log:
            return

        font = pygame.font.Font(None, 13)
        max_lines = 3
        start_idx = max(0, len(self.turn_log) - max_lines)

        for i, entry in enumerate(self.turn_log[start_idx:start_idx + max_lines]):
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

    def _draw_turn_hud(self, screen):
        bar_y = settings.WINDOW_HEIGHT - settings.UI_BAR_HEIGHT
        pygame.draw.rect(screen, settings.DARK_GRAY,
                         (0, bar_y, settings.WINDOW_WIDTH, settings.UI_BAR_HEIGHT))
        pygame.draw.line(screen, settings.GRAY, (0, bar_y),
                         (settings.WINDOW_WIDTH, bar_y), 1)

        hp_pct = self.game.player.hp / self.game.player.max_hp
        rigor_pct = self.game.player.rigor / self.game.player.max_rigor
        entropy_pct = self.game.entropy / settings.MAX_ENTROPY

        hp_color = settings.GREEN if hp_pct > 0.5 else settings.ORANGE if hp_pct > 0.25 else settings.RED
        self._draw_bar(screen, settings.UI_PADDING, bar_y + 10, 160, 14,
                       hp_pct, hp_color, (60, 20, 20))
        draw_text(screen, f"HP: {self.game.player.hp}/{self.game.player.max_hp}",
                  (settings.UI_PADDING + 80, bar_y + 17),
                  settings.WHITE, 14)

        self._draw_bar(screen, settings.UI_PADDING, bar_y + 31, 160, 14,
                       rigor_pct, settings.BLUE, (20, 20, 60))
        draw_text(screen, f"{t('rigor')}: {self.game.player.rigor:.0f}/{self.game.player.max_rigor}",
                  (settings.UI_PADDING + 80, bar_y + 38),
                  settings.WHITE, 14)

        # EXP Bar
        exp_pct = self.game.player.exp / self.game.player.next_level_exp
        self._draw_bar(screen, settings.UI_PADDING + 180, bar_y + 10, 120, 14,
                       exp_pct, settings.GOLD, (40, 40, 10))
        draw_text(screen, f"LVL {self.game.player.level} ({int(exp_pct*100)}%)",
                  (settings.UI_PADDING + 240, bar_y + 17),
                  settings.WHITE, 13)

        self._draw_bar(screen, settings.UI_PADDING + 180, bar_y + 31, 120, 14,
                       entropy_pct, settings.COLOR_ENTROPY_BAR, (40, 10, 40))
        draw_text(screen, f"Entropy: {self.game.entropy:.0f}",
                  (settings.UI_PADDING + 240, bar_y + 38),
                  settings.WHITE, 13)

        # Crit display moved
        draw_text(screen, f"Crit: {int(settings.PLAYER_CRIT_CHANCE * 100)}% x{settings.PLAYER_CRIT_MULTIPLIER:.0f}",
                  (settings.UI_PADDING + 340, bar_y + 17),
                  settings.GOLD, 12)
        draw_text(screen, f"Dmg: {self.game.player.base_damage}",
                  (settings.UI_PADDING + 340, bar_y + 38),
                  settings.CYAN, 12)

        phase_text = "PLAYER MOVE"
        phase_symbol = "dx"
        phase_color = settings.CYAN
        if self.state in ("PLAYER_ACTION_SELECT", "RESOLVE_ACTION"):
            phase_text = "PLAYER ATTACK"
            phase_symbol = "f'(x)"
        elif self.state == "RESOLVE_MOVE":
            phase_text = "PLAYER MOVE"
            phase_symbol = "\u0394x"
        elif self.state == "LOCK_INDICATORS":
            phase_text = "LOCK AIM"
            phase_symbol = "!"
            phase_color = settings.ORANGE
        elif self.state == "ENEMY_TURN":
            phase_color = settings.RED
            if self.enemy_phase == "ATTACK":
                phase_text = "ENEMY ATTACK"
                phase_symbol = "!x"
            else:
                phase_text = "ENEMY MOVE"
                phase_symbol = "Ax"
        elif self.state == "TURN_END":
            phase_text = "TURN END"
            phase_symbol = "="
            phase_color = settings.ORANGE
        elif self.state == "VICTORY_TRANSITION":
            phase_text = "Q.E.D."
            phase_symbol = "[QED]"
            phase_color = settings.GOLD
        elif self.state == "GAME_OVER_TRANSITION":
            phase_text = "FATAL ERROR"
            phase_symbol = "0/0"
            phase_color = settings.RED

        center_x = settings.WINDOW_WIDTH // 2
        draw_text(screen, f"Turn {self.turn_manager.turn_number} {phase_symbol}",
                  (center_x, bar_y + 13),
                  phase_color,
                  12)
        draw_text(screen, phase_text,
                  (center_x, bar_y + 31),
                  phase_color,
                  16)

        move_status = "[x]" if self.turn_manager.player_moved else "[ ]"
        act_status = "[x]" if self.turn_manager.player_acted else "[ ]"
        draw_text(screen, f"Move {move_status}   Action {act_status}",
                  (center_x, bar_y + 50),
                  settings.LIGHT_GRAY, 14)

        log_x = settings.WINDOW_WIDTH - 190
        log_title = pygame.font.Font(None, 12).render("Recent", True, settings.LIGHT_GRAY)
        screen.blit(log_title, (log_x, bar_y + 10))
        self._draw_combat_log(screen, log_x, bar_y + 22)

        controls = "WASD/click move + confirm  1/2 skills  R rewind  Esc pause"
        controls_img = pygame.font.Font(None, 11).render(controls, True, settings.GRAY)
        screen.blit(controls_img, (settings.UI_PADDING, settings.WINDOW_HEIGHT - 14))

    def _draw_bar(self, screen, x, y, w, h, pct, fill_color, bg_color):
        pygame.draw.rect(screen, bg_color, (x, y, w, h))
        if pct > 0:
            pygame.draw.rect(screen, fill_color, (x, y, int(w * pct), h))
        pygame.draw.rect(screen, settings.LIGHT_GRAY, (x, y, w, h), 1)
        pygame.draw.rect(screen, settings.LIGHT_GRAY, (x, y, w, h), 1)
