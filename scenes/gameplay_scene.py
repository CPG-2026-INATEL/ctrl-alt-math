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
        self.mp_sync_timer = 0

        self.pending_player_col = None
        self.pending_player_row = None
        self.hovered_enemy = None
        self.hovered_intent_data = None
        
        self.lore_timer = 15.0 # Start after 15 seconds
        self.lore_toast = None
        self.players = []
        self.active_player_idx = 0
        self.player_took_damage_this_room = False
        self.crits_this_room = 0
        self.tiles_moved_this_turn = 0
        self.mp_local_move_target = None
        self.mp_pending_remote_turn = None

    def _is_true_coop(self):
        return bool(self.game.mp_is_multiplayer)

    def _refresh_players(self):
        if not self._is_true_coop():
            self.players = [self.game.player]
            self.game.players = self.players
            self.game.player2 = self.game.player
            return

        self.players = getattr(self.game, "players", [self.game.player])
        if not self.players:
            self.players = [self.game.player]
        self.game.players = self.players
        self.game.player2 = self.players[1] if len(self.players) > 1 else self.players[0]

    def _living_players(self):
        return [player for player in self.players if player.hp > 0]

    def _player_label(self, idx):
        if not self._is_true_coop():
            return "Player"
        return "HOST" if idx == 0 else "P2"

    def _restore_primary_player(self):
        if self.players:
            self.game.player = self.players[0]

    def _current_player_owner(self):
        if not self._is_true_coop():
            return "local"
        return "host" if self.active_player_idx == 0 else "client"

    def _is_local_turn(self):
        owner = self._current_player_owner()
        if owner == "local":
            return True
        if owner == "host":
            return bool(self.game.mp_host)
        return False

    def _is_remote_turn(self):
        return self._is_true_coop() and self._current_player_owner() == "client" and bool(self.game.mp_host)

    def _is_client_control_turn(self):
        return self._is_true_coop() and bool(self.game.mp_client) and self.game.mp_player_index == 2 and self.active_player_idx == 1

    def _set_active_player(self, idx, reset_ui=True):
        self._refresh_players()
        idx = max(0, min(idx, len(self.players) - 1))
        if self.players[idx].hp <= 0:
            alt_idx = self._next_living_player_idx(-1)
            if alt_idx is not None:
                idx = alt_idx
        self.active_player_idx = idx
        self.game.player = self.players[idx]
        self.mp_local_move_target = None
        if reset_ui:
            self.cursor_col = self.game.player.col
            self.cursor_row = self.game.player.row
            self.show_move_range = True
            self.show_action_range = False
            self.selected_skill = None

    def _get_local_turn_move_target(self):
        return self.mp_local_move_target or (self.game.player.col, self.game.player.row)

    def _next_living_player_idx(self, start_idx):
        self._refresh_players()
        for idx in range(start_idx + 1, len(self.players)):
            if self.players[idx].hp > 0:
                return idx
        return None

    def _first_living_player_idx(self):
        return self._next_living_player_idx(-1)

    def _target_player_for_enemy(self, enemy):
        living = self._living_players()
        if not living:
            return None
        return min(
            living,
            key=lambda player: (
                self.grid.grid_distance(enemy.col, enemy.row, player.col, player.row),
                player.hp,
            ),
        )

    def _target_player_for_cell(self, col, row):
        living = self._living_players()
        for player in living:
            if (player.col, player.row) == (col, row):
                return player
        return None

    def _other_player_occupied_cells(self, current_player=None):
        if current_player is None:
            current_player = self.game.player
        return {
            (player.col, player.row)
            for player in self.players
            if player is not current_player and player.hp > 0
        }

    def _apply_enemy_damage_to_player(self, enemy, player, dmg, reason):
        if not player:
            return False
        defense = player.get_defense()
        actual_dmg = max(1, dmg - defense)
        if player.take_damage(actual_dmg):
            self.player_took_damage_this_room = True
            self.game.floating_text.add_damage(player.x, player.y, actual_dmg, enemy.last_crit)
            self.game.particles.emit_burst(player.x, player.y, settings.RED, 10, 60, 0.3)
            self.game.screen_shake = 0.15 if enemy.last_crit else 0.1
            self.game.shake_intensity = 8 if enemy.last_crit else 6
            self.game.sfx.play("player_hit")
            self.turn_log.append(reason)
            shield_data = settings.EQUIPMENT_DATA["shields"].get(player.equipment.get("shield"), {})
            if shield_data.get("effect") == "reflect" and not enemy.dead:
                reflect_dmg = max(1, int(actual_dmg * 0.25))
                enemy.take_damage(reflect_dmg)
                self.game.floating_text.add_enemy_damage(enemy.x, enemy.y, reflect_dmg, False)
                self.game.particles.emit_burst(enemy.x, enemy.y, settings.YELLOW, 5, 40, 0.2)
                if enemy.dead:
                    self._on_enemy_death(enemy)
            return True
        self.game.floating_text.add_blocked(player.x, player.y)
        self.turn_log.append(f"{reason} (blocked)")
        return False

    def _advance_after_player_turn(self):
        if self._is_client_control_turn():
            self.state = "WAIT_REMOTE_SYNC"
            return
        # If there are no enemies, trigger victory
        alive_enemies = [e for e in self.game.enemies if not e.dead and not getattr(e, 'is_decoy', False)]
        if len(alive_enemies) == 0:
            self._check_victory()
            return
        next_idx = self._next_living_player_idx(self.active_player_idx)
        if next_idx is not None:
            self.turn_manager.start_turn()
            self.state = "PLAYER_INPUT"
            self._set_active_player(next_idx)
            self._generate_enemy_intents()
            return
        self._start_enemy_turn()

    def enter(self, prev_scene=None):
        self.state = "WAVE_INTRO"
        self.turn_manager = TurnManager()
        self._refresh_players()
        self.active_player_idx = 0
        self.game.player = self.players[0]
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
        self.mp_sync_timer = 0
        self.player_took_damage_this_room = False
        self.crits_this_room = 0
        self.tiles_moved_this_turn = 0
        self.mp_local_move_target = None
        self.mp_pending_remote_turn = None

        if prev_scene and hasattr(prev_scene, "room"):
            room = prev_scene.room
            self.game.current_room = room

            if room.type == "boss":
                self.game.music.play("boss")
            else:
                self.game.music.play("gameplay")
            
            # Deterministic random for room generation
            room_seed = getattr(self.game, "seed", 0) ^ hash((room.col, room.row))
            random.seed(room_seed)
            
            # Randomize map size based on difficulty
            scaling = settings.DIFFICULTY_SCALING.get(settings.DIFFICULTY, settings.DIFFICULTY_SCALING[settings.DIFFICULTY_HARD])
            new_cols = getattr(room, 'arena_cols', settings.GRID_COLS)
            new_rows = getattr(room, 'arena_rows', settings.GRID_ROWS)
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
                        size_factor = enemy_multiplier
                        enemy.max_hp = int(room.boss_hp * (1.0 + (size_factor - 1.0) * 0.5))
                        enemy.hp = enemy.max_hp
                    self.game.enemies.append(enemy)

            if len(self.game.enemies) == 0:
                self.state = "NO_COMBAT"
            
            # Speak room narrative
            text = f"{t(room.name)}. {t(room.narrative)}"
            self.game.tts.speak(text, lang=settings.LANGUAGE)
        else:
            self.obstacles_data = settings.ARENA_OBSTACLES
            self.game.obstacles = self.grid.obstacle_rects(settings.ARENA_OBSTACLES)

        self.grid.load_obstacles(self.obstacles_data)

        self._generate_tilemap()

        pcol, prow = self.grid.cols // 2, self.grid.rows - 2
        spawn_cells = [(pcol, prow)]
        if len(self.players) > 1:
            candidate_cells = [
                (pcol - 1, prow),
                (pcol + 1, prow),
                (pcol, prow - 1),
                (pcol - 1, prow - 1),
                (pcol + 1, prow - 1),
            ]
            for cell in candidate_cells:
                if self.grid.is_valid(cell[0], cell[1]) and not self.grid.is_blocked(cell[0], cell[1]):
                    spawn_cells.append(cell)
                    break
        while len(spawn_cells) < len(self.players):
            spawn_cells.append((pcol, prow))

        for player, (col, row) in zip(self.players, spawn_cells):
            player.set_grid_position(col, row, self.grid)

        self._set_active_player(0)

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
        occupied = {
            (player.col, player.row)
            for player in self.players
            if self.grid.is_valid(player.col, player.row)
        }
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
        self._set_active_player(0)
        self.turn_manager.snapshot(self._get_game_state()) # Initial snapshot for Turn 1
        self._generate_enemy_intents()
        self.danger_locked = False
        self._save_rewind_state()
        self.tiles_moved_this_turn = 0
        self.game.sfx.play("wave_start")
        self.game.tts.speak(t("wave_count", wave=self.turn_manager.turn_number), lang=settings.LANGUAGE)

    def _generate_enemy_intents(self):
        alive_enemies = [e for e in self.game.enemies if not e.dead]
        self.enemy_intents = []
        clones = [e for e in alive_enemies if getattr(e, 'is_decoy', False) and not e.dead]
        for enemy in alive_enemies:
            if any(se["effect"] == "stun" for se in enemy.status_effects):
                continue
            if getattr(enemy, 'is_decoy', False):
                continue
            target_player = self._target_player_for_enemy(enemy)
            if target_player is None:
                continue
            target_col, target_row = target_player.col, target_player.row
            if clones and random.random() < 0.5:
                clone = random.choice(clones)
                target_col, target_row = clone.col, clone.row
            new_intents = enemy.decide_intent(target_col, target_row, self.grid, self.game.enemies)
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
                self.game.current_room.id
            )
            if hasattr(self.game, "save_progress"):
                self.game.save_progress()
            if self.game.current_room.type == "victory" and self.game.world_map.all_required_rooms_completed():
                self._broadcast_scene_switch("victory")
                self._restore_primary_player()
                self.game.scene_manager.switch("victory")
                return
        self._broadcast_scene_switch("map")
        self._restore_primary_player()
        self.game.player.clear_room_buffs()
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
        occupied = self._other_player_occupied_cells(self.game.player)
        reachable = self.grid.get_reachable_cells(pc, pr, self.game.player.move_range, extra_blocked=occupied)

        if (self.cursor_col, self.cursor_row) == (pc, pr):
            self.mp_local_move_target = (pc, pr)
            self._enter_action_select()
            self.game.sfx.play("menu_select")
            return

        if (self.cursor_col, self.cursor_row) in reachable:
            self.mp_local_move_target = (self.cursor_col, self.cursor_row)
            self.pending_player_col = self.cursor_col
            self.pending_player_row = self.cursor_row
            self.state = "RESOLVE_MOVE"
            self.turn_manager.resolve_timer = 0
            anim_path = self._build_anim_path(pc, pr, self.cursor_col, self.cursor_row, extra_blocked=occupied)
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
        if self.selected_skill == "integral":
            radius = st.get_skill_value("integral", "range", settings.INTEGRAL_RANGE)
            return self.grid.get_cells_in_radius(pc, pr, radius)
        if self.selected_skill == "fractal":
            radius = st.get_skill_value("fractal", "range", settings.FRACTAL_RANGE)
            cells = self.grid.get_cells_in_radius(pc, pr, radius)
            return [c for c in cells if c != (pc, pr) and not self.grid.is_blocked(c[0], c[1])]
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

        if self.selected_skill == "fractal":
            return not self.grid.is_blocked(self.cursor_col, self.cursor_row)

        if self.selected_skill == "integral":
            return True

        return self._get_enemy_at_cursor() is not None

    def _confirm_action_cursor(self):
        is_self = (self.cursor_col, self.cursor_row) == (self.game.player.col, self.game.player.row)
        target_enemies = self._get_enemies_at_cursor()
        skill_id = self.selected_skill
        move_target = self._get_local_turn_move_target()
        
        if is_self or (not target_enemies and self.selected_skill is None):
            if self._is_client_control_turn():
                self._send_mp_command("submit_turn", move=list(move_target), action="wait")
            self.turn_manager.player_acted = True
            self.show_action_range = False
            self.tiles_moved_this_turn = 0
            self.turn_log.append("Wait")
            self._advance_after_player_turn()
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
            elif self._is_client_control_turn():
                self._send_mp_command(
                    "submit_turn",
                    move=list(move_target),
                    action="skill",
                    skill_id=skill_id,
                    target=[self.cursor_col, self.cursor_row],
                )
        else:
            self._execute_basic_attack(target_enemies=target_enemies)
            if self._is_client_control_turn():
                self._send_mp_command(
                    "submit_turn",
                    move=list(move_target),
                    action="basic_attack",
                    target=[self.cursor_col, self.cursor_row],
                )

    def handle_event(self, event):
        if self.game.mp_is_multiplayer and self.game.mp_client:
            if not self._is_client_control_turn() and self.state not in ("WAVE_INTRO", "NO_COMBAT"):
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.game.scene_manager.push("pause")
                return
            if self.state == "WAIT_REMOTE_SYNC":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.game.scene_manager.push("pause")
                return

            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == "WAVE_INTRO" and event.button == 1:
                    self._send_mp_command("begin_room")
                    return
                if self.state == "NO_COMBAT" and event.button == 1:
                    self._send_mp_command("leave_no_combat")
                    return

            if event.type == pygame.KEYDOWN:
                if self.state == "WAVE_INTRO":
                    self._send_mp_command("begin_room")
                    return

            if event.type != pygame.KEYDOWN:
                return

            if self.state == "WAVE_INTRO":
                self._send_mp_command("begin_room")
                return

            if self.state == "NO_COMBAT":
                if event.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                    self._send_mp_command("leave_no_combat")
                return

            if event.key == pygame.K_ESCAPE:
                self.game.scene_manager.push("pause")
                return

            if event.key == pygame.K_s and self.state not in ("VICTORY_TRANSITION", "GAME_OVER_TRANSITION"):
                self.game.scene_manager.push("skill_tree")
                return

            if event.key == pygame.K_u and self.state not in ("VICTORY_TRANSITION", "GAME_OVER_TRANSITION"):
                self.game.scene_manager.push("upgrades")
                return

            if event.key == pygame.K_i and self.state in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT"):
                self.game.scene_manager.push("inventory_dock")
                return

            if event.key == pygame.K_e and self.state not in ("VICTORY_TRANSITION", "GAME_OVER_TRANSITION"):
                self.game.scene_manager.push("equip_dock")
                return

            if event.key == pygame.K_r and self.state in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT"):
                self._send_mp_command("rewind")
                return

            if self.state in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT"):
                if event.key in (pygame.K_w, pygame.K_UP, pygame.K_s, pygame.K_DOWN, pygame.K_a, pygame.K_LEFT, pygame.K_d, pygame.K_RIGHT):
                    col, row = self.cursor_col, self.cursor_row
                    if event.key in (pygame.K_w, pygame.K_UP):
                        row -= 1
                    elif event.key in (pygame.K_s, pygame.K_DOWN):
                        row += 1
                    elif event.key in (pygame.K_a, pygame.K_LEFT):
                        col -= 1
                    elif event.key in (pygame.K_d, pygame.K_RIGHT):
                        col += 1
                    self._send_mp_command("cursor_abs", col=col, row=row)
                    return
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._send_mp_command("confirm")
                    return
                if self.state == "PLAYER_ACTION_SELECT":
                    if event.key == pygame.K_x:
                        self._send_mp_command("cursor_abs", col=self.game.player.col, row=self.game.player.row)
                        self._send_mp_command("confirm")
                    elif event.key == pygame.K_1:
                        self._send_mp_command("select_skill", skill_id="pitagoras")
                    elif event.key == pygame.K_2:
                        self._send_mp_command("select_skill", skill_id="reflexao")
                    elif event.key == pygame.K_3:
                        self._send_mp_command("select_skill", skill_id="integral")
                    elif event.key == pygame.K_4:
                        self._send_mp_command("select_skill", skill_id="fractal")
                return

        if self.game.mp_is_multiplayer and self._is_remote_turn():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.game.scene_manager.push("pause")
            return

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

        if (mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_SHIFT) and event.key == pygame.K_d:
            st = self.game.skill_tree
            for sid in st.skills:
                if st.skills[sid]["level"] == 0:
                    st.skills[sid]["level"] = 1
            st.skill_points = 99
            self.game.player.gold = 999
            self.game.gold = 999
            self.game.floating_text.add_info(self.game.player.x, self.game.player.y - 40,
                                            "DEBUG: All skills | 99 SP | 999 gold", settings.GOLD)
            self.game.sfx.play("skill_unlock")
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

        if event.key == pygame.K_s and self.state not in ("VICTORY_TRANSITION", "GAME_OVER_TRANSITION"):
            self.game.scene_manager.push("skill_tree")
            return

        if event.key == pygame.K_u and self.state not in ("VICTORY_TRANSITION", "GAME_OVER_TRANSITION"):
            self.game.scene_manager.push("upgrades")
            return

        if event.key == pygame.K_i and self.state in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT"):
            self.game.scene_manager.push("inventory_dock")
            return

        if event.key == pygame.K_e and self.state not in ("VICTORY_TRANSITION", "GAME_OVER_TRANSITION"):
            self.game.scene_manager.push("equip_dock")
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
        elif k == pygame.K_3:
            if self.game.skill_tree.is_unlocked("integral"):
                self._toggle_skill("integral")
        elif k == pygame.K_4:
            if self.game.skill_tree.is_unlocked("fractal"):
                self._toggle_skill("fractal")

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
                if enemy.dead or getattr(enemy, 'is_decoy', False):
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
                base_dmg = (self.game.player.get_attack_damage() + axioma_bonus) * move_bonus
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
                self._apply_weapon_effect(enemy)
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
        if not self.game.mp_client or self.game.mp_host:
            self._check_victory()
            if self.state == "VICTORY_TRANSITION":
                return
        self._advance_after_player_turn()

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

        elif skill == "integral":
            if not self.game.player.integral_attack():
                return False
            st = self.game.skill_tree
            radius = st.get_skill_value("integral", "range", settings.INTEGRAL_RANGE)
            target_cells = self.grid.get_cells_in_radius(pc, pr, radius)
            dmg_base = st.get_skill_value("integral", "damage", settings.INTEGRAL_DAMAGE)
            lifesteal = st.get_skill_value("integral", "lifesteal", settings.INTEGRAL_LIFESTEAL)
            total_dmg = 0
            hit_count = 0
            for enemy in self.game.enemies:
                if not enemy.dead and (enemy.col, enemy.row) in target_cells:
                    enemy.take_damage(dmg_base)
                    self.game.floating_text.add_enemy_damage(enemy.x, enemy.y, dmg_base, False)
                    self.game.particles.emit_burst(enemy.x, enemy.y, (100, 255, 100), 6, 40, 0.2)
                    total_dmg += dmg_base
                    hit_count += 1
                    if enemy.dead:
                        self._on_enemy_death(enemy)
            if total_dmg > 0:
                heal = int(total_dmg * lifesteal)
                self.game.player.hp = min(self.game.player.hp + heal, self.game.player.get_max_hp())
                self.game.floating_text.add_heal(self.game.player.x, self.game.player.y, heal)
                self.game.particles.emit_burst(self.game.player.x, self.game.player.y, (100, 255, 100), 15, 80, 0.4)
            self.game.sfx.play("menu_select")
            self.turn_log.append(f"Integral hit {hit_count} for {total_dmg} dmg, healed {int(total_dmg * lifesteal)}")

        elif skill == "fractal":
            target_cell = (self.cursor_col, self.cursor_row)
            if target_cell == (pc, pr):
                return False
            if self.grid.is_blocked(self.cursor_col, self.cursor_row) or self.grid.is_level_change(pc, pr, self.cursor_col, self.cursor_row):
                return False
            if not self.game.player.fractal_attack():
                return False
            from enemy import Enemy
            st = self.game.skill_tree
            clone_hp = st.get_skill_value("fractal", "hp", settings.FRACTAL_HP_PER_LEVEL)
            level = st.get_level("fractal")
            clone = Enemy(0, 0, "strawman")
            clone.col = self.cursor_col
            clone.row = self.cursor_row
            clone.x, clone.y = self.grid.to_pixel(self.cursor_col, self.cursor_row)
            clone.hp = clone_hp
            clone.max_hp = clone_hp
            clone.color = (100, 255, 180)
            clone.is_decoy = True
            clone.is_ally = True
            clone.decoy_lifetime = level * 2 + 2
            clone.robot_type = "Clone"
            clone.size = settings.ENEMY_SIZE * 0.8
            self.game.enemies.append(clone)
            self.game.floating_text.add_info(clone.x, clone.y - 20, "CLONE", (100, 255, 180))
            self.game.particles.emit_burst(clone.x, clone.y, (100, 255, 180), 20, 100, 0.5)
            self.game.sfx.play("menu_select")
            self.turn_log.append(f"Fractal clone spawned with {clone_hp} HP")

        self.turn_manager.player_acted = True
        self.show_action_range = False
        self.selected_skill = None
        if not self.game.mp_client or self.game.mp_host:
            self._check_victory()
            if self.state == "VICTORY_TRANSITION":
                return True
        self._advance_after_player_turn()
        return True

    def _on_enemy_death(self, enemy):
        if getattr(enemy, "death_processed", False):
            return
        enemy.death_processed = True
        self.last_enemy_death_pos = (enemy.x, enemy.y)

        self.game.floating_text.add_formula(
            enemy.x, enemy.y,
            t("eliminated"), settings.GREEN
        )
        self.game.particles.emit_burst(enemy.x, enemy.y, enemy.color, 15, 80, 0.4)
        self.game.floating_text.add_info(enemy.x, enemy.y, t("qed"), settings.GREEN)
        self.game.screen_shake = 0.1
        self.game.shake_intensity = 4
        self.game.sfx.play("enemy_die")

        # Award EXP
        exp_reward = 0
        if enemy.type == "censor": exp_reward = settings.ENEMY_EXP_CENSOR
        elif enemy.type == "strawman": exp_reward = settings.ENEMY_EXP_STRAWMAN
        elif enemy.type == "bayesian": exp_reward = settings.ENEMY_EXP_BAYESIAN
        elif enemy.type == "boss": exp_reward = settings.ENEMY_EXP_BOSS
        elif enemy.type == "ortogonal": exp_reward = settings.ENEMY_EXP_ORTOGONAL
        elif enemy.type == "atirador": exp_reward = settings.ENEMY_EXP_ATIRADOR
        elif enemy.type == "granadeiro": exp_reward = settings.ENEMY_EXP_GRANADEIRO

        if exp_reward > 0:
            if self.game.player.add_exp(exp_reward):
                self.game.floating_text.add_info(self.game.player.x, self.game.player.y - 60,
                                                f"LEVEL UP! ({self.game.player.level})", settings.GOLD)
                self.game.sfx.play("victory")
                self.game.particles.emit_burst(self.game.player.x, self.game.player.y, settings.GOLD, 20, 100, 0.5)

    def _apply_weapon_effect(self, enemy):
        if enemy.dead:
            return
        weapon_effect = self.game.player.get_weapon_effect()
        if not weapon_effect:
            return
        if weapon_effect == "burn":
            enemy.status_effects.append({"effect": "burn", "damage": 3, "turns": 2})
            self.game.floating_text.add_info(enemy.x, enemy.y - 20, "BURN", settings.ORANGE)
        elif weapon_effect == "poison":
            enemy.status_effects.append({"effect": "poison", "damage": 2, "turns": 3})
            self.game.floating_text.add_info(enemy.x, enemy.y - 20, "POISON", (100, 200, 50))
        elif weapon_effect == "slow":
            enemy.status_effects.append({"effect": "slow", "turns": 1})
            self.game.floating_text.add_info(enemy.x, enemy.y - 20, "SLOW", settings.CYAN)
        elif weapon_effect == "stun":
            if random.random() < 0.35:
                enemy.status_effects.append({"effect": "stun", "turns": 1})
                self.game.floating_text.add_info(enemy.x, enemy.y - 20, "STUN", settings.GOLD)
        elif weapon_effect == "aoe":
            pc = self.game.player.col
            pr = self.game.player.row
            for other in self.game.enemies:
                if other is enemy or other.dead:
                    continue
                dx = abs(other.col - enemy.col)
                dy = abs(other.row - enemy.row)
                if dx + dy <= 1:
                    aoe_dmg = max(1, int(self.game.player.get_attack_damage() * 0.5))
                    other.take_damage(aoe_dmg)
                    self.game.floating_text.add_enemy_damage(other.x, other.y, aoe_dmg, False)
                    self.game.particles.emit_burst(other.x, other.y, settings.YELLOW, 5, 40, 0.2)
                    if other.dead:
                        self._on_enemy_death(other)

    def _tick_enemy_status_effects(self):
        for enemy in self.game.enemies:
            if enemy.dead:
                continue
            expired = []
            for i, se in enumerate(enemy.status_effects):
                if se["effect"] == "burn":
                    enemy.take_damage(se["damage"])
                    self.game.floating_text.add_enemy_damage(enemy.x, enemy.y, se["damage"], False)
                    self.game.particles.emit_burst(enemy.x, enemy.y, settings.ORANGE, 4, 30, 0.2)
                    se["turns"] -= 1
                    if se["turns"] <= 0:
                        expired.append(i)
                elif se["effect"] == "poison":
                    enemy.take_damage(se["damage"])
                    self.game.floating_text.add_enemy_damage(enemy.x, enemy.y, se["damage"], False)
                    self.game.particles.emit_burst(enemy.x, enemy.y, (100, 200, 50), 4, 30, 0.2)
                    se["turns"] -= 1
                    if se["turns"] <= 0:
                        expired.append(i)
                elif se["effect"] == "slow":
                    se["turns"] -= 1
                    if se["turns"] <= 0:
                        expired.append(i)
                elif se["effect"] == "stun":
                    se["turns"] -= 1
                    if se["turns"] <= 0:
                        expired.append(i)
            for i in reversed(expired):
                enemy.status_effects.pop(i)
            if enemy.dead:
                self._on_enemy_death(enemy)

    def _tick_decoy_clones(self):
        self._perform_decoy_actions()
        for i in range(len(self.game.enemies) - 1, -1, -1):
            enemy = self.game.enemies[i]
            if getattr(enemy, 'is_decoy', False) and not enemy.dead:
                enemy.decoy_lifetime -= 1
                if enemy.decoy_lifetime <= 0:
                    self.game.particles.emit_burst(enemy.x, enemy.y, (100, 255, 180), 10, 50, 0.3)
                    self.game.enemies.pop(i)

        self._check_victory()

    def _perform_decoy_actions(self):
        real_enemies = [e for e in self.game.enemies if not e.dead and not getattr(e, 'is_decoy', False)]
        if not real_enemies:
            return
        clones = [e for e in self.game.enemies if getattr(e, 'is_decoy', False) and not e.dead]
        occupied = {(e.col, e.row) for e in self.game.enemies if not e.dead}
        for p in self.players:
            if p.hp > 0:
                occupied.add((p.col, p.row))

        for clone in clones:
            if not real_enemies:
                break
            nearest = min(real_enemies, key=lambda e: self.grid.grid_distance(clone.col, clone.row, e.col, e.row))
            dist = self.grid.grid_distance(clone.col, clone.row, nearest.col, nearest.row)
            if dist <= 1:
                dmg = max(1, int(self.game.player.get_attack_damage() * 0.4))
                nearest.take_damage(dmg)
                self.game.floating_text.add_enemy_damage(nearest.x, nearest.y, dmg, False)
                self.game.particles.emit_burst(nearest.x, nearest.y, (100, 255, 180), 4, 30, 0.2)
                self.game.sfx.play("hit")
                self.turn_log.append(f"Clone attacks {nearest.type} for {dmg}")
                if nearest.dead:
                    self._on_enemy_death(nearest)
                    real_enemies = [e for e in real_enemies if not e.dead]
            else:
                dc = 1 if nearest.col > clone.col else (-1 if nearest.col < clone.col else 0)
                dr = 1 if nearest.row > clone.row else (-1 if nearest.row < clone.row else 0)
                new_col = clone.col + dc
                new_row = clone.row + dr
                if self.grid.is_valid(new_col, new_row) and not self.grid.is_blocked(new_col, new_row):
                    if (new_col, new_row) not in occupied:
                        occupied.discard((clone.col, clone.row))
                        clone.col = new_col
                        clone.row = new_row
                        clone.x, clone.y = self.grid.to_pixel(new_col, new_row)
                        occupied.add((new_col, new_row))
                        self.turn_log.append("Clone moved")

    def _check_victory(self):
        alive = [e for e in self.game.enemies if not e.dead and not getattr(e, 'is_decoy', False)]
        if len(alive) == 0 and self.state != "VICTORY_TRANSITION":
            self.state = "VICTORY_TRANSITION"
            self.victory_timer = 0
            pos = self.last_enemy_death_pos or (self.game.player.x, self.game.player.y)
            self.game.particles.emit_burst(pos[0], pos[1], settings.GOLD, 30, 100, 0.8)
            
            if self.game.skill_tree:
                self.game.skill_tree.add_points(1)
            self.game.floating_text.add_info(pos[0], pos[1] - 40, 
                                            t("earned_skill_point"), settings.GOLD)
            self.game.tts.speak(t("earned_skill_point"), lang=settings.LANGUAGE)

            if self.game.current_room:
                gold_reward = getattr(self.game.current_room, 'gold_reward', 20)
                self.game.player.gold += gold_reward
                self.game.gold = self.game.player.gold
                self.game.floating_text.add_info(
                    self.game.player.x, self.game.player.y - 60,
                    f"+{gold_reward} gold", settings.GOLD)

                if hasattr(self.game, "save_progress"):
                    self.game.save_progress()

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

        self.game.sfx.play("enemy_turn")
        self.grid.lock_danger_indicators(self.enemy_intents)
        self.danger_locked = True
        self.lock_timer = 0
        self.state = "LOCK_INDICATORS"

    def update(self, dt):
        if self.game.mp_is_multiplayer and self.game.mp_client:
            if self.game.mp_client:
                for msg in self.game.mp_client.poll():
                    if msg.get("type") == "gp_state":
                        self._apply_mp_state(msg)
                    elif msg.get("type") == "scene_switch":
                        self.game.scene_manager.switch(msg.get("scene", "map"))
                        return
            if not self._is_client_control_turn() and self.state not in ("WAVE_INTRO", "NO_COMBAT"):
                return

        if self.game.mp_is_multiplayer and self.game.mp_host:
            for msg in self.game.mp_host.poll():
                if msg.get("type") == "gp_cmd":
                    self._apply_remote_gameplay_command(msg)

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
                    reachable = self.grid.get_reachable_cells(
                        pc,
                        pr,
                        self.game.player.move_range,
                        extra_blocked=self._other_player_occupied_cells(self.game.player),
                    )
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
                if self.mp_pending_remote_turn is not None:
                    self.mp_pending_remote_turn["move_done"] = True
                self._enter_action_select()
                self._generate_enemy_intents()
                self._process_pending_remote_turn()

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
                        self.game.current_room.id
                    )
                    if hasattr(self.game, "save_progress"):
                        self.game.save_progress()
                    if (self.game.current_room.type == "victory" or
                        self.game.current_room.is_final or
                        getattr(self.game.current_room, 'is_final_gate', False)):
                        self._broadcast_scene_switch("victory")
                        self._restore_primary_player()
                        self.game.scene_manager.switch("victory")
                    else:
                        self._broadcast_scene_switch("map")
                        self._restore_primary_player()
                        self.game.player.clear_room_buffs()
                        self.game.scene_manager.switch("map")
                else:
                    self._broadcast_scene_switch("victory")
                    self._restore_primary_player()
                    self.game.scene_manager.switch("victory")

        elif self.state == "GAME_OVER_TRANSITION":
            self.game_over_timer += dt
            self.game.player.flash_timer = max(0, self.game.player.flash_timer - dt)
            if self.game_over_timer >= settings.GAME_OVER_TRANSITION_DURATION:
                self._broadcast_scene_switch("game_over")
                self._restore_primary_player()
                self.game.scene_manager.switch("game_over")

        if self.state == "PLAYER_INPUT" or self.state == "PLAYER_ACTION_SELECT":
            entropy_rate = settings.DIFFICULTY_SCALING[settings.DIFFICULTY]["entropy_per_turn"]
            self.game.entropy = min(settings.MAX_ENTROPY,
                                    self.game.entropy + entropy_rate * dt * 0.1)

        if self.game.mp_is_multiplayer and self.game.mp_host:
            self.mp_sync_timer += dt
            if self.mp_sync_timer >= 1.0 / settings.LAN_TICK_RATE:
                self.mp_sync_timer = 0
                self.game.mp_host.broadcast(self._serialize_mp_state())

            # Host: process commands from clients
            msgs = self.game.mp_host.poll()
            for msg in msgs:
                if msg.get("type") == "gp_cmd":
                    self._apply_remote_gameplay_command(msg)
            self._process_pending_remote_turn()

        if self.game.mp_is_multiplayer and self.game.mp_client:
            # Client: apply state updates from host
            msgs = self.game.mp_client.poll()
            for msg in msgs:
                if msg.get("type") == "gp_state":
                    self._apply_mp_state(msg)
                elif msg.get("type") == "scene_switch":
                    target = msg.get("scene")
                    self._restore_primary_player()
                    self.game.scene_manager.switch(target)

    def _resolve_enemy_turn(self, dt):
        if self.enemy_resolve_idx >= len(self.enemy_actions):
            self.enemy_phase = None
            self.state = "TURN_END"
            return

        if not self._living_players():
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
        target = self._target_player_for_enemy(enemy)
        if target is None:
            self.turn_log.append(f"{enemy.type} attack missed")
            return

        d = self.grid.grid_distance(enemy.col, enemy.row, target.col, target.row)
        if d <= enemy.attack_range and not self.grid.is_level_change(enemy.col, enemy.row, target.col, target.row):
            dmg = enemy.roll_damage(self.game.entropy)
            dx = abs(target.col - enemy.col)
            dy = abs(target.row - enemy.row)
            if self._apply_enemy_damage_to_player(enemy, target, dmg, f"{enemy.type} hit {self._player_label(self.players.index(target))} for {dmg}{' (CRIT!)' if enemy.last_crit else ''}"):
                if enemy.last_crit:
                    self.game.floating_text.add_formula(
                        target.x, target.y + 15,
                        f"CRITICAL! ({dx}+{dy}={dx+dy})", settings.ORANGE
                    )
        elif d <= enemy.attack_range:
            self.game.floating_text.add_evasion(enemy.x, enemy.y)
            self.turn_log.append(f"{enemy.type} can't reach (elevation)")
        else:
            self.turn_log.append(f"{enemy.type} attack missed")

    def _enemy_cross_attack(self, enemy):
        ec, er = enemy.col, enemy.row
        hit_cells = [(ec, er - 1), (ec, er + 1), (ec - 1, er), (ec + 1, er)]
        dmg = enemy.roll_damage()
        for player in self._living_players():
            if (player.col, player.row) in hit_cells and not self.grid.is_level_change(ec, er, player.col, player.row):
                label = self._player_label(self.players.index(player))
                self._apply_enemy_damage_to_player(enemy, player, dmg, f"Ortogonal cross hit {label} for {dmg}{' (CRIT!)' if enemy.last_crit else ''}")
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

            for player in self._living_players():
                if c == player.col and r == player.row:
                    label = self._player_label(self.players.index(player))
                    self._apply_enemy_damage_to_player(enemy, player, dmg, f"Boss line attack hit {label} for {dmg}!")

        self.game.particles.emit_burst(enemy.x, enemy.y, (255, 100, 100), 10, 50, 0.3)
        self.game.sfx.play("pitagoras")
        self.turn_log.append(f"Boss line attack")

    def _enemy_ranged_line_attack(self, enemy):
        target = self._target_player_for_enemy(enemy)
        if target is None:
            return
        pc = target.col
        pr = target.row
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
            for player in self._living_players():
                if c == player.col and r == player.row and not self.grid.is_level_change(ec, er, c, r):
                    label = self._player_label(self.players.index(player))
                    if self._apply_enemy_damage_to_player(enemy, player, dmg, f"Atirador line attack hit {label} for {dmg}{' (CRIT!)' if enemy.last_crit else ''}"):
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
                for player in self._living_players():
                    if col == player.col and row == player.row:
                        label = self._player_label(self.players.index(player))
                        if self._apply_enemy_damage_to_player(enemy, player, dmg, f"Boss AoE hit {label} for {dmg}!"):
                            hit = True

        cx, cy = self.grid.to_pixel(tc, tr)
        self.game.particles.emit_burst(cx, cy, settings.RED, 20, 80, 0.4)
        self.game.sfx.play("boss_phase")
        if not hit:
            self.turn_log.append(f"Boss AoE missed")

    def _end_turn(self):
        # Apply regeneration first
        for player in self._living_players():
            player.rigor = min(
                player.max_rigor,
                player.rigor + settings.RIGOR_REGEN_RATE
            )
            self.game.floating_text.add_rigor(
                player.x, player.y - 20,
                settings.RIGOR_REGEN_RATE
            )
        self.grid.clear_barriers()

        self.game.player.tick_buffs()
        self._tick_enemy_status_effects()
        self._tick_decoy_clones()

        # Check for room completion or death before taking snapshot for next turn
        alive = [e for e in self.game.enemies if not e.dead and not getattr(e, 'is_decoy', False)]
        if len(alive) == 0:
            self.state = "VICTORY_TRANSITION"
            self.victory_timer = 0
            self.game.particles.emit_burst(
                self.last_enemy_death_pos[0] if self.last_enemy_death_pos else self.game.player.x,
                self.last_enemy_death_pos[1] if self.last_enemy_death_pos else self.game.player.y,
                settings.GOLD, 30, 100, 0.8
            )
            return

        if not self._living_players():
            self.state = "GAME_OVER_TRANSITION"
            self.game_over_timer = 0
            self.game.particles.emit_burst(
                self.players[0].x, self.players[0].y, settings.RED, 20, 80, 0.5
            )
            self.game.screen_shake = 0.3
            self.game.shake_intensity = 10
            self.game.sfx.play("player_hit")
            return

        # Prepare for next turn and take snapshot
        self.game.sfx.play("your_turn")
        self.state = "PLAYER_INPUT"
        self.turn_manager.start_turn()
        self._set_active_player(0)
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
            "players": [
                {
                    "col": player.col,
                    "row": player.row,
                    "hp": player.hp,
                    "max_hp": player.max_hp,
                    "rigor": player.rigor,
                    "pitagoras_cooldown": getattr(player, 'pitagoras_cooldown', 0),
                    "reflexao_cooldown": getattr(player, 'reflexao_cooldown', 0),
                    "integral_cooldown": getattr(player, 'integral_cooldown', 0),
                    "fractal_cooldown": getattr(player, 'fractal_cooldown', 0),
                }
                for player in self.players
            ],
            "enemies": self.game.enemies,
            "entropy": self.game.entropy,
            "barrier_cells": self.grid.barrier_cells.copy(),
            "player_obj": self.game.player,
        }

    def _save_rewind_state(self):
        gs = self._get_game_state()
        self.turn_manager.snapshot(gs)

    def _serialize_mp_state(self):
        room = None
        if self.game.current_room:
            room = [self.game.current_room.col, self.game.current_room.row]

        enemy_intents = []
        for intent in self.enemy_intents:
            if intent is None or intent.enemy.dead:
                continue
            try:
                enemy_index = self.game.enemies.index(intent.enemy)
            except ValueError:
                continue
            enemy_intents.append({
                "enemy_index": enemy_index,
                "move_target": list(intent.move_target) if intent.move_target else None,
                "attack_origin": list(intent.attack_origin) if intent.attack_origin else None,
                "target_tile": list(intent.target_tile) if intent.target_tile else None,
                "danger_tiles": [list(tile) for tile in intent.danger_tiles],
                "attack_type": intent.attack_type,
                "is_fake": intent.is_fake,
                "telegraph_type": intent.telegraph_type,
                "lock_mode": intent.lock_mode,
            })

        return {
            "type": "gp_state",
            "room": room,
            "state": self.state,
            "grid_cols": self.grid.cols,
            "grid_rows": self.grid.rows,
            "blocked": [list(cell) for cell in self.grid.blocked],
            "barriers": [list(cell) for cell in self.grid.barrier_cells],
            "tile_types": [[c, r, tval] for (c, r), tval in self.grid.tile_types.items()],
            "tilemap": self.tilemap.map_data if self.tilemap else None,
            "player": {
                "col": self.game.player.col,
                "row": self.game.player.row,
                "x": self.game.player.x,
                "y": self.game.player.y,
                "hp": self.game.player.hp,
                "max_hp": self.game.player.max_hp,
                "rigor": self.game.player.rigor,
            },
            "players": [
                {
                    "col": player.col,
                    "row": player.row,
                    "x": player.x,
                    "y": player.y,
                    "hp": player.hp,
                    "max_hp": player.max_hp,
                    "rigor": player.rigor,
                    "player_id": getattr(player, "player_id", idx + 1),
                }
                for idx, player in enumerate(self.players)
            ],
            "enemies": [
                {
                    "type": enemy.type,
                    "col": enemy.col,
                    "row": enemy.row,
                    "x": enemy.x,
                    "y": enemy.y,
                    "hp": enemy.hp,
                    "max_hp": enemy.max_hp,
                    "alive": enemy.alive,
                    "dead": enemy.dead,
                }
                for enemy in self.game.enemies
            ],
            "cursor": [self.cursor_col, self.cursor_row],
            "active_player_idx": self.active_player_idx,
            "show_move_range": self.show_move_range,
            "show_action_range": self.show_action_range,
            "selected_skill": self.selected_skill,
            "turn": self.turn_manager.turn_number,
            "player_moved": self.turn_manager.player_moved,
            "player_acted": self.turn_manager.player_acted,
            "danger_locked": self.danger_locked,
            "danger_tiles": [list(entry) for entry in self.grid.danger_tiles],
            "enemy_intents": enemy_intents,
            "camera": [self.camera_x, self.camera_y],
            "entropy": self.game.entropy,
        }

    def _apply_mp_state(self, msg):
        incoming_state = msg.get("state", self.state)
        incoming_active_idx = msg.get("active_player_idx", self.active_player_idx)
        preserve_local_turn = self._is_client_control_turn() and self.state != "WAIT_REMOTE_SYNC"
        if self.state == "WAIT_REMOTE_SYNC" and incoming_active_idx == self.active_player_idx and incoming_state in (
            "PLAYER_INPUT",
            "PLAYER_ACTION_SELECT",
            "RESOLVE_MOVE",
        ):
            preserve_local_turn = True
        local_player_idx = max(0, self.game.mp_player_index - 1)

        room = msg.get("room")
        if room:
            self.game.current_room = self.game.world_map.rooms.get((room[0], room[1]))

        cols = msg.get("grid_cols", self.grid.cols)
        rows = msg.get("grid_rows", self.grid.rows)
        if self.grid.cols != cols or self.grid.rows != rows:
            self.grid = Grid(cols, rows)

        self.grid.blocked = {tuple(cell) for cell in msg.get("blocked", [])}
        self.grid.barrier_cells = {tuple(cell) for cell in msg.get("barriers", [])}
        self.grid.tile_types = {(c, r): tval for c, r, tval in msg.get("tile_types", [])}
        self.grid.danger_tiles = {tuple(entry) for entry in msg.get("danger_tiles", [])}
        self.danger_locked = msg.get("danger_locked", False)
        self.grid.danger_locked = self.danger_locked

        tilemap_data = msg.get("tilemap")
        if tilemap_data is not None:
            try:
                self.tilemap = TileMap(self.TILESET_PATH, tile_size=self.TILE_SIZE)
                self.tilemap.load_from_list(tilemap_data)
            except Exception:
                pass

        players_data = msg.get("players")
        if players_data and len(self.players) != len(players_data):
            self.players = [Player() for _ in players_data]
            for idx, player in enumerate(self.players):
                player.player_id = idx + 1
                if idx == 1:
                    player.skin_index = 1
            self.game.players = self.players
            self.game.player2 = self.players[1] if len(self.players) > 1 else self.players[0]

        if players_data:
            for idx, data in enumerate(players_data):
                if idx >= len(self.players):
                    break
                if preserve_local_turn and idx == local_player_idx:
                    continue
                player = self.players[idx]
                player.col = data.get("col", player.col)
                player.row = data.get("row", player.row)
                player.x = data.get("x", player.x)
                player.y = data.get("y", player.y)
                player.hp = data.get("hp", player.hp)
                player.max_hp = data.get("max_hp", player.max_hp)
                player.rigor = data.get("rigor", player.rigor)
        else:
            pdata = msg.get("player", {})
            self.players[0].col = pdata.get("col", self.players[0].col)
            self.players[0].row = pdata.get("row", self.players[0].row)
            self.players[0].x = pdata.get("x", self.players[0].x)
            self.players[0].y = pdata.get("y", self.players[0].y)
            self.players[0].hp = pdata.get("hp", self.players[0].hp)
            self.players[0].max_hp = pdata.get("max_hp", self.players[0].max_hp)
            self.players[0].rigor = pdata.get("rigor", self.players[0].rigor)

        enemy_data = msg.get("enemies", [])
        if len(self.game.enemies) != len(enemy_data) or any(
            i >= len(self.game.enemies) or self.game.enemies[i].type != data.get("type")
            for i, data in enumerate(enemy_data)
        ):
            self.game.enemies = [Enemy(0, 0, data.get("type", "censor")) for data in enemy_data]

        for enemy, data in zip(self.game.enemies, enemy_data):
            enemy.col = data.get("col", enemy.col)
            enemy.row = data.get("row", enemy.row)
            enemy.x = data.get("x", enemy.x)
            enemy.y = data.get("y", enemy.y)
            enemy.hp = data.get("hp", enemy.hp)
            enemy.max_hp = data.get("max_hp", enemy.max_hp)
            enemy.alive = data.get("alive", enemy.alive)
            enemy.dead = data.get("dead", enemy.dead)

        self.enemy_intents = []
        for data in msg.get("enemy_intents", []):
            idx = data.get("enemy_index")
            if idx is None or idx >= len(self.game.enemies):
                continue
            self.enemy_intents.append(EnemyIntent(
                enemy=self.game.enemies[idx],
                move_target=tuple(data["move_target"]) if data.get("move_target") else None,
                attack_type=data.get("attack_type"),
                attack_origin=tuple(data["attack_origin"]) if data.get("attack_origin") else None,
                target_tile=tuple(data["target_tile"]) if data.get("target_tile") else None,
                danger_tiles={tuple(tile) for tile in data.get("danger_tiles", [])},
                lock_mode=data.get("lock_mode", "fixed"),
                telegraph_type=data.get("telegraph_type", "line"),
                is_fake=data.get("is_fake", False),
            ))

        if not preserve_local_turn:
            self.state = incoming_state
            self._set_active_player(incoming_active_idx, reset_ui=False)
            self.cursor_col, self.cursor_row = msg.get("cursor", [self.cursor_col, self.cursor_row])
            self.show_move_range = msg.get("show_move_range", self.show_move_range)
            self.show_action_range = msg.get("show_action_range", self.show_action_range)
            self.selected_skill = msg.get("selected_skill", self.selected_skill)
        self.turn_manager.turn_number = msg.get("turn", self.turn_manager.turn_number)
        self.turn_manager.player_moved = msg.get("player_moved", self.turn_manager.player_moved)
        self.turn_manager.player_acted = msg.get("player_acted", self.turn_manager.player_acted)
        if not preserve_local_turn:
            self.camera_x, self.camera_y = msg.get("camera", [self.camera_x, self.camera_y])
        self.game.entropy = msg.get("entropy", self.game.entropy)

    def _broadcast_scene_switch(self, scene_name):
        if self.game.mp_is_multiplayer and self.game.mp_host:
            self.game.mp_host.broadcast({"type": "scene_switch", "scene": scene_name})

    def _send_mp_command(self, cmd, **payload):
        if self.game.mp_client:
            msg = {"type": "gp_cmd", "cmd": cmd}
            msg.update(payload)
            self.game.mp_client.send(msg)

    def _process_pending_remote_turn(self):
        data = self.mp_pending_remote_turn
        if not data or not self._is_remote_turn():
            return

        if not data.get("move_done"):
            if self.state != "PLAYER_INPUT":
                return
            move_col, move_row = data.get("move", (self.game.player.col, self.game.player.row))
            self.cursor_col = move_col
            self.cursor_row = move_row
            self._confirm_player_cursor()
            if self.state != "RESOLVE_MOVE":
                data["move_done"] = True
            return

        if self.state != "PLAYER_ACTION_SELECT":
            return

        action = data.get("action")
        target = data.get("target")
        skill_id = data.get("skill_id")
        if action == "skill" and skill_id:
            self.selected_skill = None
            self._toggle_skill(skill_id)
        if action == "wait":
            self.cursor_col = self.game.player.col
            self.cursor_row = self.game.player.row
        elif target:
            self.cursor_col, self.cursor_row = target
        self.mp_pending_remote_turn = None
        self._confirm_action_cursor()

    def _apply_remote_gameplay_command(self, msg):
        cmd = msg.get("cmd")
        if cmd not in ("begin_room", "leave_no_combat") and not self._is_remote_turn():
            return

        if cmd == "begin_room" and self.state == "WAVE_INTRO":
            self._begin_room()
        elif cmd == "leave_no_combat" and self.state == "NO_COMBAT":
            self._leave_no_combat_room()
        elif cmd == "cursor_abs" and self.state in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT"):
            col = int(msg.get("col", self.cursor_col))
            row = int(msg.get("row", self.cursor_row))
            self.cursor_col = max(0, min(self.grid.cols - 1, col))
            self.cursor_row = max(0, min(self.grid.rows - 1, row))
        elif cmd == "confirm":
            if self.state == "PLAYER_INPUT":
                self._confirm_player_cursor()
            elif self.state == "PLAYER_ACTION_SELECT":
                self._confirm_action_cursor()
        elif cmd == "cancel_action" and self.state == "PLAYER_ACTION_SELECT":
            self.selected_skill = None
            self.show_action_range = True
        elif cmd == "select_skill" and self.state == "PLAYER_ACTION_SELECT":
            skill_id = msg.get("skill_id")
            if skill_id == "pitagoras" and self.game.skill_tree.is_unlocked("pitagoras"):
                self._toggle_skill("pitagoras")
            elif skill_id == "reflexao" and self.game.skill_tree.is_unlocked("reflexao"):
                self._toggle_skill("reflexao")
            elif skill_id == "integral" and self.game.skill_tree.is_unlocked("integral"):
                self._toggle_skill("integral")
            elif skill_id == "fractal" and self.game.skill_tree.is_unlocked("fractal"):
                self._toggle_skill("fractal")
        elif cmd == "rewind" and self.state in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT"):
            self._try_rewind()
        elif cmd == "submit_turn" and self.state in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT", "RESOLVE_MOVE"):
            move = msg.get("move", [self.game.player.col, self.game.player.row])
            target = msg.get("target")
            self.mp_pending_remote_turn = {
                "move": (int(move[0]), int(move[1])) if len(move) == 2 else (self.game.player.col, self.game.player.row),
                "action": msg.get("action", "wait"),
                "target": (int(target[0]), int(target[1])) if target and len(target) == 2 else None,
                "skill_id": msg.get("skill_id"),
                "move_done": False,
            }
            self._process_pending_remote_turn()

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

        player_snaps = snapshot.get("players", [snapshot["player"]])
        actual_heal = 0
        for idx, player_snap in enumerate(player_snaps):
            if idx >= len(self.players):
                break
            player = self.players[idx]
            player.col = int(player_snap["col"])
            player.row = int(player_snap["row"])
            player.hp = player_snap["hp"]
            player.max_hp = player_snap["max_hp"]
            old_hp = player.hp
            player.hp = min(player.hp + settings.REWIND_HEAL_AMOUNT, player.max_hp)
            if idx == self.active_player_idx:
                actual_heal = player.hp - old_hp
            player.rigor = player_snap["rigor"]
            
            # Restore skill cooldowns
            player.pitagoras_cooldown = player_snap.get("pitagoras_cooldown", 0)
            player.reflexao_cooldown = player_snap.get("reflexao_cooldown", 0)
            player.integral_cooldown = player_snap.get("integral_cooldown", 0)
            player.fractal_cooldown = player_snap.get("fractal_cooldown", 0)
            
            px, py = self.grid.to_pixel(player.col, player.row)
            player.x, player.y = int(px), int(py)

        # Restore enemies list exactly from snapshot to eliminate clones/decoys
        restored_enemies = []
        for i, e_snap in enumerate(snapshot["enemies"]):
            if i < len(self.game.enemies):
                enemy = self.game.enemies[i]
            else:
                enemy = Enemy(0, 0, e_snap["type"])
            
            enemy.col = int(e_snap["col"])
            enemy.row = int(e_snap["row"])
            enemy.hp = e_snap["hp"]
            enemy.max_hp = e_snap["max_hp"]
            enemy.alive = e_snap["alive"]
            enemy.dead = e_snap["dead"]
            
            if "size" in e_snap:
                enemy.size = e_snap["size"]
            if "color" in e_snap:
                enemy.color = e_snap["color"]
                
            px, py = self.grid.to_pixel(enemy.col, enemy.row)
            enemy.x, enemy.y = int(px), int(py)
            restored_enemies.append(enemy)
        self.game.enemies = restored_enemies

        self.game.entropy = snapshot["entropy"]

        self.grid.clear_barriers()
        for col, row in snapshot.get("barrier_cells", []):
            self.grid.mark_barrier(col, row, True)

        penalty = settings.REWIND_ENTROPY_INCREASE
        if self.game.skill_tree.is_unlocked("entropia"):
            penalty //= 2

        self.game.entropy = min(
            self.game.entropy + penalty,
            settings.MAX_ENTROPY
        )
        self.turn_manager.rewind_cooldown_turns = settings.REWIND_COOLDOWN_TURNS

        self.game.rewind_fx_timer = 1.0
        self.game.sfx.play("rewind")

        self.game.sfx.play("your_turn")
        self.state = "PLAYER_INPUT"
        self.turn_manager.start_turn()
        self._set_active_player(0)
        self._generate_enemy_intents()
        self.danger_locked = False

        self.game.floating_text.add_info(self.game.player.x, self.game.player.y - 40, "<< REWIND >>", settings.GREEN)
        if actual_heal > 0:
            self.game.floating_text.add_info(self.game.player.x, self.game.player.y - 60, f"+{actual_heal} HP", settings.GREEN)

    def _draw_derivada_preview(self, screen):
        pc = self.game.player.col
        pr = self.game.player.row

        for enemy in self.game.enemies:
            if enemy.dead or getattr(enemy, 'is_decoy', False):
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
            self._draw_high_tile_shadows(temp, world_offset)
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
            reachable = self.grid.get_reachable_cells(
                pc,
                pr,
                self.game.player.move_range,
                extra_blocked=self._other_player_occupied_cells(self.game.player),
            )
            self.grid.draw(temp, highlight_cells=reachable, highlight_color=settings.BLUE, offset=world_offset)

        if self.state == "PLAYER_ACTION_SELECT" and self.show_action_range:
            if self.selected_skill == "pitagoras":
                cells = self.grid.get_cells_in_radius(
                    self.game.player.col, self.game.player.row,
                    settings.PITAGORAS_RANGE
                )
                self.grid.draw(temp, highlight_cells=cells, highlight_color=settings.YELLOW, offset=world_offset)
                
                pc_c, pc_r = self.game.player.col, self.game.player.row
                cc_c, cc_r = self.cursor_col, self.cursor_row
                corner_c, corner_r = cc_c, pc_r
                
                # Draw the neon right-triangle
                self.grid.draw_triangle(temp,
                    pc_c, pc_r,
                    corner_c, corner_r,
                    cc_c, cc_r,
                    settings.YELLOW, 2, offset=world_offset)
                
                # Draw right-angle square indicator at corner
                if pc_c != cc_c and pc_r != cc_r:
                    cx, cy = self.grid.to_pixel(corner_c, corner_r)
                    cx += world_offset[0]
                    cy += world_offset[1]
                    sgn_x = -1 if cc_c > pc_c else 1
                    sgn_y = 1 if cc_r > pc_r else -1
                    sq_sz = 8
                    pygame.draw.line(temp, settings.YELLOW, (cx, cy + sgn_y * sq_sz), (cx + sgn_x * sq_sz, cy + sgn_y * sq_sz), 1)
                    pygame.draw.line(temp, settings.YELLOW, (cx + sgn_x * sq_sz, cy), (cx + sgn_x * sq_sz, cy + sgn_y * sq_sz), 1)
                
                # Draw elegant formulas / side length labels
                dx = cc_c - pc_c
                dy = cc_r - pc_r
                eucl = math.sqrt(dx * dx + dy * dy)
                font = pygame.font.Font(None, 13)
                
                # Side a (horizontal) label
                if dx != 0:
                    px_a = (self.grid.to_pixel(pc_c, pc_r)[0] + self.grid.to_pixel(corner_c, corner_r)[0]) / 2 + world_offset[0]
                    py_a = self.grid.to_pixel(pc_c, pc_r)[1] + world_offset[1] - 8
                    lbl_a = font.render(f"a={abs(dx)}", True, settings.LIGHT_GRAY)
                    temp.blit(lbl_a, (px_a - lbl_a.get_width() // 2, py_a))
                
                # Side b (vertical) label
                if dy != 0:
                    px_b = self.grid.to_pixel(corner_c, corner_r)[0] + world_offset[0] + 6
                    py_b = (self.grid.to_pixel(corner_c, corner_r)[1] + self.grid.to_pixel(cc_c, cc_r)[1]) / 2 + world_offset[1]
                    lbl_b = font.render(f"b={abs(dy)}", True, settings.LIGHT_GRAY)
                    temp.blit(lbl_b, (px_b, py_b - lbl_b.get_height() // 2))
                
                # Side c (hypotenuse) label
                if dx != 0 and dy != 0:
                    px_c = (self.grid.to_pixel(pc_c, pc_r)[0] + self.grid.to_pixel(cc_c, cc_r)[0]) / 2 + world_offset[0] - 16
                    py_c = (self.grid.to_pixel(pc_c, pc_r)[1] + self.grid.to_pixel(cc_c, cc_r)[1]) / 2 + world_offset[1] - 12
                    lbl_c = font.render(f"c={eucl:.2f}", True, settings.GOLD)
                    temp.blit(lbl_c, (px_c, py_c))
            elif self.selected_skill == "reflexao":
                cells = self.grid.get_cells_in_radius(
                    self.game.player.col, self.game.player.row,
                    settings.REFLEXAO_RANGE
                )
                self.grid.draw(temp, highlight_cells=cells, highlight_color=settings.CYAN, offset=world_offset)
            elif self.selected_skill == "integral":
                st = self.game.skill_tree
                radius = st.get_skill_value("integral", "range", settings.INTEGRAL_RANGE)
                cells = self.grid.get_cells_in_radius(
                    self.game.player.col, self.game.player.row, radius
                )
                self.grid.draw(temp, highlight_cells=cells, highlight_color=(100, 255, 100), offset=world_offset)
            elif self.selected_skill == "fractal":
                cells = self.grid.get_cells_in_radius(
                    self.game.player.col, self.game.player.row, 1
                )
                self.grid.draw(temp, highlight_cells=cells, highlight_color=(255, 180, 100), offset=world_offset)
            else:
                cells = self.grid.get_cells_in_range(
                    self.game.player.col, self.game.player.row,
                    settings.BASIC_ATTACK_RANGE
                )
                self.grid.draw(temp, highlight_cells=cells, highlight_color=settings.RED, offset=world_offset)

        # 🔹 Derivada: Predicted next move velocity vectors
        if self.game.skill_tree.is_unlocked("derivada"):
            for intent in self.enemy_intents:
                if intent is None or intent.enemy.dead:
                    continue
                enemy = intent.enemy
                if intent.move_target and intent.move_target != (enemy.col, enemy.row):
                    d_col = intent.move_target[0] - enemy.col
                    d_row = intent.move_target[1] - enemy.row
                    # Draw neon velocity vector line & arrow
                    self.grid.draw_vector_arrow(temp, enemy.col, enemy.row,
                                               intent.move_target[0], intent.move_target[1], settings.GREEN, 2, offset=world_offset)
                    # Midpoint coordinates for vector formula label
                    fx, fy = self.grid.to_pixel(enemy.col, enemy.row)
                    tx, ty = self.grid.to_pixel(intent.move_target[0], intent.move_target[1])
                    mx = (fx + tx) / 2 + world_offset[0]
                    my = (fy + ty) / 2 + world_offset[1] - 8
                    
                    font = pygame.font.Font(None, 12)
                    lbl_val = f"v = ({d_col:+d}, {d_row:+d})"
                    lbl_img = font.render(lbl_val, True, settings.GREEN)
                    temp.blit(lbl_img, (mx - lbl_img.get_width() // 2, my - lbl_img.get_height() // 2))
                else:
                    # Fallback to direction indicator if no path found
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

        # 🔹 Bayes: Heatmap prediction of attack range probabilities
        if self.game.skill_tree.is_unlocked("bayes"):
            pc = self.game.player.col
            pr = self.game.player.row
            font = pygame.font.Font(None, 11)
            for enemy in self.game.enemies:
                if enemy.dead or getattr(enemy, 'is_decoy', False):
                    continue
                dist = self.grid.grid_distance(enemy.col, enemy.row, pc, pr)
                max_dist = enemy.attack_range
                if max_dist > 0 and dist <= max_dist:
                    proximity = 1.0 - (dist / max_dist)
                    intensity = int(40 + proximity * 60)
                    cells = self.grid.get_cells_in_radius(enemy.col, enemy.row, 2)
                    for col, row in cells:
                        rect = self.grid.cell_rect(col, row)
                        rect.x += world_offset[0]
                        rect.y += world_offset[1]
                        
                        # Glitch distortion when entropy > 50
                        cell_intensity = intensity
                        if self.game.entropy > 50 and random.random() < 0.2:
                            rect.x += random.randint(-3, 3)
                            rect.y += random.randint(-3, 3)
                            cell_intensity = int(intensity * random.uniform(0.3, 1.8))
                        
                        s = pygame.Surface((rect.width, rect.height))
                        s.set_alpha(max(5, min(120, cell_intensity // 3)))
                        s.fill(settings.PURPLE)
                        temp.blit(s, rect)
                        
                        # Draw P(T|E) percentage label on cells
                        p_val = int(proximity * 100)
                        lbl_bayes = font.render(f"P(T)={p_val}%", True, (220, 180, 255))
                        temp.blit(lbl_bayes, (rect.centerx - lbl_bayes.get_width() // 2, rect.centery - lbl_bayes.get_height() // 2))

        # 🔹 Teoria dos Jogos: Threat vectors and Nash Equilibrium safest tile
        if self.game.skill_tree.is_unlocked("teoria_jogos"):
            pc = self.game.player.col
            pr = self.game.player.row
            
            # Red threat vectors pointing to player
            for enemy in self.game.enemies:
                if enemy.dead or getattr(enemy, 'is_decoy', False):
                    continue
                if self.grid.grid_distance(enemy.col, enemy.row, pc, pr) <= enemy.attack_range:
                    self.grid.draw_vector_arrow(temp, enemy.col, enemy.row,
                                               pc, pr, settings.RED, 1, offset=world_offset)
            
            # Evaluate all reachable player cells to identify the Nash Equilibrium (safest tile)
            reachable = self.grid.get_reachable_cells(
                pc, pr, self.game.player.move_range,
                extra_blocked=self._other_player_occupied_cells(self.game.player)
            )
            candidates = [(pc, pr)] + reachable
            safest_cell = None
            min_threat = 999999
            
            for cc, cr in candidates:
                threat_score = 0
                for enemy in self.game.enemies:
                    if enemy.dead or getattr(enemy, 'is_decoy', False):
                        continue
                    # Count threats that can hit this candidate cell
                    if self.grid.grid_distance(enemy.col, enemy.row, cc, cr) <= enemy.attack_range:
                        threat_score += 1
                
                # Tiebreaker: prefer cells closer to player to save movement, or further from enemies
                dist_to_player = self.grid.grid_distance(pc, pr, cc, cr)
                eval_score = threat_score * 1000 + dist_to_player
                
                if eval_score < min_threat:
                    min_threat = eval_score
                    safest_cell = (cc, cr)
            
            # Glow overlay on the Nash Equilibrium cell
            if safest_cell:
                sc_col, sc_row = safest_cell
                rect = self.grid.cell_rect(sc_col, sc_row)
                rect.x += world_offset[0]
                rect.y += world_offset[1]
                
                glow_alpha = int(100 + 60 * math.sin(self.cursor_timer * 6))
                s = pygame.Surface((rect.width, rect.height))
                s.set_alpha(glow_alpha)
                s.fill(settings.CYAN)
                temp.blit(s, rect)
                pygame.draw.rect(temp, settings.CYAN, rect, 2)
                
                font = pygame.font.Font(None, 11)
                lbl_nash = font.render("NASH EQ", True, settings.WHITE)
                temp.blit(lbl_nash, (rect.centerx - lbl_nash.get_width() // 2, rect.centery - lbl_nash.get_height() // 2))

        if self.state in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT", "LOCK_INDICATORS", "ENEMY_TURN"):
            self.grid.draw_danger_indicators(temp, pulse_timer=self.cursor_timer, offset=world_offset)
            self.grid.draw_intent_arrows(temp, self.enemy_intents, 
                                        player_skills=self._get_player_skill_ids() if self.state in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT") else None,
                                        offset=world_offset)

        for enemy in self.game.enemies:
            enemy.draw(temp, offset=world_offset)

        for idx, player in enumerate(self.players):
            if player.hp <= 0:
                continue
            player.draw(temp, offset=world_offset)
            if self._is_true_coop():
                px = int(player.x + world_offset[0])
                py = int(player.y + world_offset[1] - player.size - 28)
                label_color = settings.CYAN if idx == 0 else settings.PURPLE
                draw_text(temp, self._player_label(idx), (px, py), label_color, 14)

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

        self.game.ui.draw_entropy_effects(temp, self.game.entropy)
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

        elif self.state == "NO_COMBAT":
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

        if self.state == "GAME_OVER_TRANSITION":
            progress = min(1.0, self.game_over_timer / settings.GAME_OVER_TRANSITION_DURATION)
            fade = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
            fade.set_alpha(int(200 * progress))
            fade.fill(settings.BLACK)
            screen.blit(fade, (0, 0))

    def _draw_high_tile_shadows(self, screen, world_offset):
        high_tiles = {TILE_HIGH, TILE_HIGH_EDGE}
        low_tiles = {TILE_LOW, TILE_STAIRS_DOWN, TILE_STAIRS_LEFT, TILE_STAIRS_RIGHT}

        for (col, row), tile in self.grid.tile_types.items():
            if tile not in high_tiles:
                continue

            for dc, dr, alpha, height_frac in ((0, 1, 70, 0.42), (1, 0, 40, 1.0), (-1, 0, 40, 1.0)):
                neighbor = (col + dc, row + dr)
                if self.grid.tile_types.get(neighbor) not in low_tiles:
                    continue
                rect = self.grid.cell_rect(neighbor[0], neighbor[1])
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

        is_pitagoras = (self.state == "PLAYER_ACTION_SELECT" and self.selected_skill == "pitagoras")
        is_reflexao = (self.state == "PLAYER_ACTION_SELECT" and self.selected_skill == "reflexao")

        # Glassmorphic Card Settings
        card_w = 280
        card_h = 245 if is_pitagoras else (225 if is_reflexao else 205)
        card_x = settings.WINDOW_WIDTH - card_w - 20
        if card_x < 0:
            card_x = 10
        card_y = settings.ARENA_OFFSET_Y + 5

        # Render glassmorphic card shadow / glow layers
        for glow_offset in range(3, 0, -1):
            glow_alpha = 10 - glow_offset * 2
            glow_surf = pygame.Surface((card_w + glow_offset * 2, card_h + glow_offset * 2), pygame.SRCALPHA)
            if is_pitagoras:
                glow_color = (255, 215, 0, glow_alpha)
            elif is_reflexao:
                glow_color = (0, 255, 255, glow_alpha)
            else:
                glow_color = (80, 100, 220, glow_alpha)
            pygame.draw.rect(glow_surf, glow_color, (0, 0, glow_surf.get_width(), glow_surf.get_height()), border_radius=10 + glow_offset)
            screen.blit(glow_surf, (card_x - glow_offset, card_y - glow_offset))

        # Main glass backdrop surface
        card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        card_surf.fill((8, 10, 22, 220))  # Ultra-dark translucent blue-black
        
        if is_pitagoras:
            border_color = (255, 215, 0, 160)
        elif is_reflexao:
            border_color = (0, 255, 255, 160)
        else:
            border_color = (80, 100, 220, 160)
            
        pygame.draw.rect(card_surf, border_color, (0, 0, card_w, card_h), 1, border_radius=10)
        screen.blit(card_surf, (card_x, card_y))

        # Header Title
        title_font = pygame.font.Font(None, 28)
        if is_pitagoras:
            title_text = "PYTHAGOREAN SCAN"
            title_color = settings.YELLOW
        elif is_reflexao:
            title_text = "REFLEXAO SCAN"
            title_color = settings.CYAN
        else:
            title_text = "COORDINATE ANALYZER"
            title_color = settings.CYAN

        title_img = title_font.render(title_text, True, title_color)
        screen.blit(title_img, (card_x + 12, card_y + 8))

        # Divider line
        pygame.draw.line(screen, (50, 55, 80), (card_x + 10, card_y + 32), (card_x + card_w - 10, card_y + 32), 1)

        # Standard lines
        font = pygame.font.Font(None, 24)
        
        label_color = settings.LIGHT_GRAY
        value_color = settings.WHITE

        lines = [
            (f"v = ({dx:+d}, {dy:+d})", label_color),
            (f"|v| = {dist}", value_color),
        ]

        if dist > 0:
            lines.append((f"||v|| = {eucl:.2f}", settings.YELLOW))

        # Get tile name
        tile_type = self.grid.tile_types.get((cc, cr), 0)
        tile_name = "LOW"
        if tile_type == -1:
            tile_name = "HOLE"
        elif tile_type in (16, 61):
            tile_name = "HIGH"
        elif tile_type in (27, 11, 25, 24):
            tile_name = "STAIRS"
        lines.append((f"Tile: {tile_name}", settings.GRAY))

        # Reachable check
        reachable = self.grid.get_reachable_cells(
            pc,
            pr,
            self.game.player.move_range,
            extra_blocked=self._other_player_occupied_cells(self.game.player),
        )
        can_reach = (cc, cr) in reachable or (cc, cr) == (pc, pr)
        lines.append(("Reachable" if can_reach else "Blocked",
                       settings.GREEN if can_reach else settings.RED))

        # Render lines inside card
        text_y = card_y + 38
        for text, color in lines:
            img = font.render(text, True, color)
            screen.blit(img, (card_x + 12, text_y))
            text_y += 24

        # Draw formulas/debug at the bottom of the card with bigger text
        formula_font = pygame.font.Font(None, 26)
        if self.state == "PLAYER_INPUT" and self.show_move_range and (cc, cr) in reachable:
            move_label = formula_font.render(f"dpos({dx:+d},{dy:+d}) d={dist}", True, settings.BLUE)
            screen.blit(move_label, (card_x + 12, text_y + 4))

        if self.state == "PLAYER_ACTION_SELECT":
            if self.selected_skill == "pitagoras":
                pygame.draw.line(screen, (70, 70, 40), (card_x + 10, text_y + 2), (card_x + card_w - 10, text_y + 2), 1)
                text_y += 8
                formula_label = formula_font.render("a² + b² = c²", True, settings.YELLOW)
                value_label = formula_font.render(f"c = {eucl:.2f}", True, settings.GOLD)
                screen.blit(formula_label, (card_x + 12, text_y))
                screen.blit(value_label, (card_x + 12, text_y + 22))
            elif self.selected_skill == "reflexao":
                pygame.draw.line(screen, (40, 70, 70), (card_x + 10, text_y + 2), (card_x + card_w - 10, text_y + 2), 1)
                text_y += 8
                formula_label = formula_font.render("theta_i = theta_r (reflect)", True, settings.CYAN)
                screen.blit(formula_label, (card_x + 12, text_y))

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

    def _draw_bar_sleek(self, screen, x, y, w, h, pct, fill_color, bg_color):
        pygame.draw.rect(screen, bg_color, (x, y, w, h), border_radius=4)
        if pct > 0:
            filled_w = int(w * min(1.0, pct))
            if filled_w > 0:
                pygame.draw.rect(screen, fill_color, (x, y, filled_w, h), border_radius=4)
                # Glossy shine on the upper half
                shine_surf = pygame.Surface((filled_w, h // 2), pygame.SRCALPHA)
                shine_surf.fill((255, 255, 255, 40))
                screen.blit(shine_surf, (x, y))
        pygame.draw.rect(screen, (80, 100, 130, 180), (x, y, w, h), 1, border_radius=4)

    def _draw_turn_hud(self, screen):
        bar_y = settings.WINDOW_HEIGHT - settings.UI_BAR_HEIGHT
        
        # 1. Base bar panel: Futuristic dark-blue matte-glass style
        pygame.draw.rect(screen, (10, 12, 22), (0, bar_y, settings.WINDOW_WIDTH, settings.UI_BAR_HEIGHT))
        # Top neon border line
        pygame.draw.line(screen, (30, 180, 220), (0, bar_y), (settings.WINDOW_WIDTH, bar_y), 2)
        
        panel_y = bar_y + 10
        panel_h = 128

        # --- DYNAMIC PANEL WIDTHS ---
        total_w = settings.WINDOW_WIDTH
        edge_padding = 10
        gap = 14
        available_w = total_w - 2 * edge_padding - 4 * gap

        # Compute dynamic proportional widths - giving actions/skills (w4) the most space!
        w1 = int(available_w * 0.23)
        w2 = int(available_w * 0.18)
        w3 = int(available_w * 0.11)
        w4 = int(available_w * 0.28)
        w5 = available_w - (w1 + w2 + w3 + w4)  # Take all remaining space on the right

        # X coordinates
        x1 = edge_padding
        x2 = x1 + w1 + gap
        x3 = x2 + w2 + gap
        x4 = x3 + w3 + gap
        x5 = x4 + w4 + gap

        # Glassmorphic panels helper
        def draw_hud_panel(x, w, title=None, title_color=settings.GOLD):
            s = pygame.Surface((w, panel_h), pygame.SRCALPHA)
            # Semi-transparent dark background
            pygame.draw.rect(s, (18, 22, 38, 220), (0, 0, w, panel_h), border_radius=6)
            # High-tech cyber border
            pygame.draw.rect(s, (60, 85, 115, 120), (0, 0, w, panel_h), 1, border_radius=6)
            screen.blit(s, (x, panel_y))
            if title:
                draw_text(screen, title.upper(), (x + 8, panel_y + 8), title_color, 16, center=False)

        current_player = self.game.player
        hp_pct = current_player.hp / current_player.get_max_hp()
        rigor_pct = current_player.rigor / current_player.max_rigor
        entropy_pct = self.game.entropy / settings.MAX_ENTROPY
        exp_pct = current_player.exp / current_player.next_level_exp

        # --- PANEL 1: STATUS (X = x1, W = w1) ---
        draw_hud_panel(x1, w1)
        
        # Level & Identity Header
        player_label = self._player_label(self.active_player_idx)
        draw_text(screen, f"{player_label}  |  LVL {current_player.level}", (x1 + 8, panel_y + 8), settings.CYAN, 15, center=False)
        
        # HP Bar
        hp_color = settings.GREEN if hp_pct > 0.5 else settings.ORANGE if hp_pct > 0.25 else settings.RED
        self._draw_bar_sleek(screen, x1 + 8, panel_y + 26, w1 - 16, 12, hp_pct, hp_color, (45, 15, 15))
        draw_text(screen, f"HP: {current_player.hp}/{current_player.get_max_hp()}", (x1 + w1 // 2, panel_y + 32), settings.WHITE, 14)

        # Rigor Bar
        self._draw_bar_sleek(screen, x1 + 8, panel_y + 49, w1 - 16, 12, rigor_pct, settings.BLUE, (15, 15, 45))
        draw_text(screen, f"{t('rigor')}: {current_player.rigor:.0f}/{current_player.max_rigor}", (x1 + w1 // 2, panel_y + 55), settings.WHITE, 14)

        # EXP Bar
        self._draw_bar_sleek(screen, x1 + 8, panel_y + 72, w1 - 16, 12, exp_pct, settings.GOLD, (30, 25, 10))
        draw_text(screen, f"EXP: {current_player.exp}/{current_player.next_level_exp} ({int(exp_pct*100)}%)", (x1 + w1 // 2, panel_y + 78), settings.WHITE, 13)

        # Entropy Bar
        entropy_color = settings.COLOR_ENTROPY_BAR if entropy_pct < 0.75 else settings.RED
        self._draw_bar_sleek(screen, x1 + 8, panel_y + 95, w1 - 16, 12, entropy_pct, entropy_color, (40, 10, 40))
        draw_text(screen, f"{t('entropy')}: {self.game.entropy:.0f}/{settings.MAX_ENTROPY}", (x1 + w1 // 2, panel_y + 101), settings.WHITE, 13)


        # --- PANEL 2: COMBAT STATS (X = x2, W = w2) ---
        draw_hud_panel(x2, w2, t("stats"), settings.GOLD)
        
        # Two-column dynamic alignment inside w2
        col1_x = x2 + 8
        col2_x = x2 + w2 // 2 + 4
        
        draw_text(screen, f"ATK: {current_player.get_attack_damage()}", (col1_x, panel_y + 28), settings.CYAN, 15, center=False)
        draw_text(screen, f"DEF: {current_player.get_defense()}", (col2_x, panel_y + 28), settings.CYAN, 15, center=False)
        
        draw_text(screen, f"CRIT: {int(settings.PLAYER_CRIT_CHANCE * 100)}%", (col1_x, panel_y + 50), settings.GOLD, 15, center=False)
        draw_text(screen, f"MULT: x{settings.PLAYER_CRIT_MULTIPLIER:.1f}", (col2_x, panel_y + 50), settings.GOLD, 15, center=False)
        
        sp_points = self.game.skill_tree.skill_points if self.game.skill_tree else 0
        draw_text(screen, f"GOLD: {current_player.gold}g", (col1_x, panel_y + 72), settings.GOLD, 15, center=False)
        draw_text(screen, f"SP: {sp_points}", (col2_x, panel_y + 72), settings.CYAN, 15, center=False)
        
        if len(self.players) > 1:
            p1 = self.players[0]
            p2 = self.players[1]
            draw_text(screen, f"P1 HP: {p1.hp}/{p1.max_hp}", (col1_x, panel_y + 94), settings.CYAN, 14, center=False)
            draw_text(screen, f"P2 HP: {p2.hp}/{p2.max_hp}", (col2_x, panel_y + 94), settings.PURPLE, 14, center=False)


        # --- PANEL 3: GAME STATE & TURN (X = x3, W = w3) ---
        draw_hud_panel(x3, w3)
        
        # Turn count
        draw_text(screen, f"TURN {self.turn_manager.turn_number}", (x3 + w3 // 2, panel_y + 16), settings.WHITE, 22)
        
        # Phase info
        phase_text = "PLAYER MOVE"
        phase_symbol = "\u0394x"
        phase_color = settings.CYAN
        if self.state in ("PLAYER_ACTION_SELECT", "RESOLVE_ACTION"):
            phase_text = "PLAYER ATTACK"
            phase_symbol = "f'(x)"
            phase_color = settings.RED
        elif self.state == "RESOLVE_MOVE":
            phase_text = "PLAYER MOVE"
            phase_symbol = "\u0394x"
            phase_color = settings.CYAN
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

        draw_text(screen, f"{phase_text} {phase_symbol}", (x3 + w3 // 2, panel_y + 50), phase_color, 16)
        
        # Move & Action Checklist
        mid_x = x3 + w3 // 2
        move_x = mid_x - 38
        act_x = mid_x + 18
        
        move_ready = self.turn_manager.player_moved
        move_color = settings.GREEN if move_ready else (80, 80, 80)
        pygame.draw.circle(screen, move_color, (move_x, panel_y + 82), 5)
        draw_text(screen, "MOVE", (move_x + 8, panel_y + 83), settings.LIGHT_GRAY, 14, center=False)

        act_ready = self.turn_manager.player_acted
        act_color = settings.GREEN if act_ready else (80, 80, 80)
        pygame.draw.circle(screen, act_color, (act_x, panel_y + 82), 5)
        draw_text(screen, "ACTION", (act_x + 8, panel_y + 83), settings.LIGHT_GRAY, 14, center=False)

# --- PANEL 4: SKILLS & ACTIONS (X = x4, W = w4) ---
        draw_hud_panel(x4, w4, t("actions"), settings.CYAN)
        
        def draw_skill_slot(slot_x, key_label, name_label, unlocked, active, cooldown, max_cooldown, cost, current_rigor, color):
            slot_rect = pygame.Rect(slot_x, panel_y + 30, 32, 32)
            if not unlocked:
                pygame.draw.rect(screen, (22, 22, 34), slot_rect, border_radius=4)
                pygame.draw.rect(screen, (40, 40, 60), slot_rect, 1, border_radius=4)
                draw_text(screen, "\U0001f512", slot_rect.center, (80, 80, 100), 16)
                
                keycap_w = 30 if len(key_label) > 1 else 20
                keycap_x = slot_x + (32 - keycap_w) // 2
                keycap_y = panel_y + 68
                keycap_rect = pygame.Rect(keycap_x, keycap_y, keycap_w, 15)
                pygame.draw.rect(screen, (20, 22, 30), keycap_rect, border_radius=4)
                pygame.draw.rect(screen, (50, 55, 70), keycap_rect, 1, border_radius=4)
                draw_text(screen, key_label, keycap_rect.center, (80, 80, 100), 11)
                return
            
            pygame.draw.rect(screen, (14, 18, 30), slot_rect, border_radius=4)
            if active:
                pygame.draw.rect(screen, settings.GOLD, slot_rect, 2, border_radius=4)
                glow_rect = slot_rect.inflate(2, 2)
                pygame.draw.rect(screen, settings.CYAN, glow_rect, 1, border_radius=4)
            else:
                pygame.draw.rect(screen, (60, 80, 110), slot_rect, 1, border_radius=4)

            draw_text(screen, name_label, slot_rect.center, color, 13)

            if cooldown > 0:
                s_overlay = pygame.Surface((32, 32), pygame.SRCALPHA)
                s_overlay.fill((0, 0, 0, 190))
                screen.blit(s_overlay, slot_rect.topleft)
                draw_text(screen, f"{int(cooldown)} Rnd", slot_rect.center, settings.WHITE, 12)
            elif cost > current_rigor:
                s_overlay = pygame.Surface((32, 32), pygame.SRCALPHA)
                s_overlay.fill((100, 20, 20, 140))
                screen.blit(s_overlay, slot_rect.topleft)
                draw_text(screen, "\u26a1", slot_rect.center, settings.RED, 18)

            keycap_w = 30 if len(key_label) > 1 else 20
            keycap_x = slot_x + (32 - keycap_w) // 2
            keycap_y = panel_y + 68
            keycap_rect = pygame.Rect(keycap_x, keycap_y, keycap_w, 15)
            
            pygame.draw.rect(screen, (30, 36, 55), keycap_rect, border_radius=4)
            border_color = settings.GOLD if active else (80, 100, 130)
            pygame.draw.rect(screen, border_color, keycap_rect, 1, border_radius=4)
            key_color = settings.GOLD if active else settings.WHITE
            draw_text(screen, key_label, keycap_rect.center, key_color, 11)

        start_x = x4 + (w4 - 202) // 2

        draw_skill_slot(start_x, "LMB", "ATK", True, (self.selected_skill is None) and (self.state in ("PLAYER_ACTION_SELECT", "RESOLVE_ACTION")), 0, 0, 0, current_player.rigor, settings.RED)

        has_pitagoras = self.game.skill_tree.is_unlocked("pitagoras") if self.game.skill_tree else False
        draw_skill_slot(start_x + 34, "1", "PIT", has_pitagoras, self.selected_skill == "pitagoras", current_player.pitagoras_cooldown, 1, settings.PITAGORAS_RIGOR_COST, current_player.rigor, settings.YELLOW)

        has_reflexao = self.game.skill_tree.is_unlocked("reflexao") if self.game.skill_tree else False
        draw_skill_slot(start_x + 68, "2", "REF", has_reflexao, self.selected_skill == "reflexao", current_player.reflexao_cooldown, 3, settings.REFLEXAO_RIGOR_COST, current_player.rigor, settings.CYAN)

        has_integral = self.game.skill_tree.is_unlocked("integral") if self.game.skill_tree else False
        draw_skill_slot(start_x + 102, "3", "INT", has_integral, self.selected_skill == "integral", current_player.integral_cooldown, 1, settings.INTEGRAL_RIGOR_COST, current_player.rigor, (100, 255, 100))

        has_fractal = self.game.skill_tree.is_unlocked("fractal") if self.game.skill_tree else False
        draw_skill_slot(start_x + 136, "4", "FRA", has_fractal, self.selected_skill == "fractal", current_player.fractal_cooldown, 5, settings.FRACTAL_RIGOR_COST, current_player.rigor, (255, 180, 100))

        has_ctrlz = self.game.skill_tree.is_unlocked("ctrlz") if self.game.skill_tree else False
        draw_skill_slot(start_x + 170, "R", "Z", has_ctrlz, False, self.turn_manager.rewind_cooldown_turns, settings.REWIND_COOLDOWN_TURNS, 0, current_player.rigor, settings.PURPLE)

        draw_text(screen, "SKILLS & REWIND", (x4 + w4 // 2, panel_y + 100), settings.LIGHT_GRAY, 14)


        # --- PANEL 5: RECENT FEED LOGS (X = x5, W = w5) ---
        draw_hud_panel(x5, w5)
        draw_text(screen, t("feed"), (x5 + w5 // 2, panel_y + 10), settings.GREEN, 15)
        
        log_y = panel_y + 28
        if self.turn_log:
            font = pygame.font.Font(None, 18)
            max_lines = 5
            start_idx = max(0, len(self.turn_log) - max_lines)
            for i, entry in enumerate(self.turn_log[start_idx:start_idx + max_lines]):
                display_entry = entry
                
                max_chars = max(15, int((w5 - 16) / 7))
                if len(display_entry) > max_chars:
                    display_entry = display_entry[:max_chars-3] + "..."
                
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
                    color = (180, 180, 220)

                img = font.render(display_entry, True, color)
                screen.blit(img, (x5 + 8, log_y + i * 17))
        else:
            font = pygame.font.Font(None, 18)
            img1 = font.render("SYSTEM: ACTIVE", True, settings.GREEN)
            screen.blit(img1, (x5 + 8, log_y + 12))
            img2 = font.render("AWAITING FORMULA", True, settings.GRAY)
            screen.blit(img2, (x5 + 8, log_y + 30))

        controls = "WASD/click move + confirm  |  1/2/3/4 skills  |  R rewind  |  Tab Panel  |  I Items  |  Esc pause"
        if self._is_true_coop():
            turn_owner = "HOST" if self._current_player_owner() == "host" else "CLIENT"
            controls = f"{controls}   [ Turn: {turn_owner} {self._player_label(self.active_player_idx)} ]"
        controls_img = pygame.font.Font(None, 15).render(controls, True, settings.GRAY)
        screen.blit(controls_img, (12, bar_y + 141))

    def _draw_bar(self, screen, x, y, w, h, pct, fill_color, bg_color):
        pygame.draw.rect(screen, bg_color, (x, y, w, h))
        if pct > 0:
            pygame.draw.rect(screen, fill_color, (x, y, int(w * pct), h))
        pygame.draw.rect(screen, settings.LIGHT_GRAY, (x, y, w, h), 1)
        pygame.draw.rect(screen, settings.LIGHT_GRAY, (x, y, w, h), 1)
