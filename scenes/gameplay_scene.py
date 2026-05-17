import pygame
import settings
from i18n import t
from grid import Grid
from turn_manager import TurnManager

from scenes.scene import Scene
from scenes.gameplay_renderer import GameplayRenderer
from scenes.gameplay_network import GameplayNetwork
from scenes.gameplay_rewind import GameplayRewind
from scenes.gameplay_combat import GameplayCombat
from scenes.gameplay_enemy_executor import GameplayEnemyExecutor
from scenes.gameplay_room import GameplayRoom
from scenes.gameplay_input import GameplayInput
from scenes.gameplay_grid_helpers import GameplayGridHelpers
from scenes.gameplay_players_manager import GameplayPlayersManager

class GameplayScene(Scene):
    TILESET_PATH = "assets/Tileset/tileset_arranged.png"
    TILE_SIZE = 16
    ENEMY_ATTACK_DELAY = 0.25

    def __init__(self, game):
        super().__init__(game)
        self.renderer = GameplayRenderer(self)
        self.network_sync = GameplayNetwork(self)
        self.rewind_handler = GameplayRewind(self)
        self.combat = GameplayCombat(self)
        self.enemy_executor = GameplayEnemyExecutor(self)
        self.room = GameplayRoom(self)
        self.input_handler = GameplayInput(self)
        self.grid_helpers = GameplayGridHelpers(self)
        self.players_mgr = GameplayPlayersManager(self)

        self.state = "WAVE_INTRO"
        self.grid = Grid()
        self.turn_manager = TurnManager()
        self.obstacles_data = settings.ARENA_OBSTACLES
        self.tilemap = None

        self.active_player_idx = 0
        self.show_move_range = True
        self.show_action_range = False
        self.selected_skill = None
        self.tiles_moved_this_turn = 0
        self.enemy_actions = []
        self.enemy_resolve_idx = 0
        self.enemy_phase = None
        self.enemy_pending_attack = None
        self.enemy_attack_delay_timer = 0.0
        self.enemy_intents = []
        self.danger_locked = False
        self.lock_timer = 0.0

        self.camera_x = 0
        self.camera_y = 0

        self.cursor_col = 0
        self.cursor_row = 0
        self.cursor_timer = 0.0
        self.hovered_enemy = None
        self.hovered_intent_data = None

        self.turn_log = []
        self.crits_this_room = 0
        self.player_took_damage_this_room = False

        self.mp_cached_state = None
        self.mp_pending_remote_turn = None
        self.mp_last_state = None
        self.mp_sync_timer = 0.0
        self.mp_full_sync_counter = 0
        self.mp_full_sync_interval = settings.LAN_FULL_SYNC_INTERVAL

        self.victory_timer = 0.0
        self.game_over_timer = 0.0
        self.lore_toast = None

    def _is_true_coop(self):
        return self.players_mgr.is_true_coop()

    def _refresh_players(self):
        self.players_mgr.refresh_players()

    def _living_players(self):
        return self.players_mgr.living_players()

    def _player_label(self, idx):
        return self.players_mgr.player_label(idx)

    def _restore_primary_player(self):
        self.players_mgr.restore_primary_player()

    def _current_player_owner(self):
        return self.players_mgr.current_player_owner()

    def _is_local_turn(self):
        return self.players_mgr.is_local_turn()

    def _is_remote_turn(self):
        return self.players_mgr.is_remote_turn()

    def _is_client_control_turn(self):
        return self.players_mgr.is_client_control_turn()

    def _set_active_player(self, idx, reset_ui=True):
        self.players_mgr.set_active_player(idx, reset_ui)

    def _get_local_turn_move_target(self):
        return self.players_mgr.get_local_turn_move_target()

    def _next_living_player_idx(self, start_idx):
        return self.players_mgr.next_living_player_idx(start_idx)

    def _first_living_player_idx(self):
        return self.players_mgr.first_living_player_idx()

    def _target_player_for_enemy(self, enemy):
        return self.players_mgr.target_player_for_enemy(enemy)

    def _target_player_for_cell(self, col, row):
        return self.players_mgr.target_player_for_cell(col, row)

    def _other_player_occupied_cells(self, current_player=None):
        return self.players_mgr.other_player_occupied_cells(current_player)

    def _apply_enemy_damage_to_player(self, enemy, player, dmg, reason):
        return self.players_mgr.apply_enemy_damage_to_player(enemy, player, dmg, reason)

    def _advance_after_player_turn(self):
        self.players_mgr.advance_after_player_turn()

    def update(self, dt):
        if self.game.mp_is_multiplayer and self.game.mp_client:
            msgs = self.game.mp_client.poll()
            for msg in msgs:
                if msg.get("type") == "gp_state":
                    self.mp_cached_state = dict(msg)
                    self._apply_mp_state(msg)
                elif msg.get("type") == "gp_state_diff":
                    if self.mp_cached_state is not None:
                        merged = dict(self.mp_cached_state)
                        merged.update(msg)
                        merged["type"] = "gp_state"
                        self.mp_cached_state = merged
                        self._apply_mp_state(merged)
                elif msg.get("type") == "scene_switch":
                    self._restore_primary_player()
                    self.game.scene_manager.switch(msg.get("scene", "map"))
                    return
            if not self._is_client_control_turn() and self.state not in ("WAVE_INTRO", "NO_COMBAT"):
                return

        if self.game.mp_is_multiplayer and self.game.mp_host:
            self._process_pending_remote_turn()

        self.cursor_timer += dt

        if self.game.rewind_fx_timer > 0:
            self.game.rewind_fx_timer -= dt
        
        target_cam_x = self.game.player.x - settings.WINDOW_WIDTH / 2
        target_cam_y = self.game.player.y - (settings.WINDOW_HEIGHT - settings.UI_BAR_HEIGHT) / 2
        self.camera_x += (target_cam_x - self.camera_x) * 5 * dt
        self.camera_y += (target_cam_y - self.camera_y) * 5 * dt

        # Update toast timings
        if self.lore_toast:
            self.lore_toast["timer"] -= dt
            if self.lore_toast["timer"] <= 0:
                self.lore_toast = None

        if self.state in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT", "LOCK_INDICATORS", "ENEMY_TURN"):
            # Tooltip hovered targets check
            mx, my = pygame.mouse.get_pos()
            cx = mx + self.camera_x
            cy = my + self.camera_y
            m_col, m_row = self.grid.to_grid(cx, cy)
            
            self.hovered_enemy = None
            if self.grid.is_valid(m_col, m_row):
                for enemy in self.game.enemies:
                    if not enemy.dead and enemy.col == m_col and enemy.row == m_row:
                        self.hovered_enemy = enemy
                        break
            
            self.hovered_intent_data = None
            if not self.hovered_enemy and self.grid.is_valid(m_col, m_row):
                for intent in self.enemy_intents:
                    if intent and (m_col, m_row) in intent.danger_tiles:
                        self.hovered_intent_data = (intent.attack_type, intent.is_fake)
                        break

        # Action resolution loops
        if self.state == "VICTORY_TRANSITION":
            self.victory_timer += dt
            if self.victory_timer >= 1.5:
                self._restore_primary_player()
                self._broadcast_scene_switch("map")
                self.game.scene_manager.switch("map")
            return

        elif self.state == "GAME_OVER_TRANSITION":
            self.game_over_timer += dt
            if self.game_over_timer >= settings.GAME_OVER_TRANSITION_DURATION:
                self._restore_primary_player()
                self._broadcast_scene_switch("game_over")
                self.game.scene_manager.switch("game_over")
            return

        # Turn loop managers
        if self.state == "RESOLVE_MOVE":
            if not self.game.player.is_animating():
                self._enter_action_select()

        elif self.state == "LOCK_INDICATORS":
            self.lock_timer += dt
            if self.lock_timer >= 0.4:
                self.lock_timer = 0.0
                self.state = "ENEMY_TURN"
                self.enemy_actions = []
                # Plan all non-dead enemy turns
                for enemy in self.game.enemies:
                    if enemy.dead:
                        continue
                    action = enemy.decide_action(
                        self.game.player.col,
                        self.game.player.row,
                        self.grid,
                        self.game.enemies
                    )
                    if action:
                        self.enemy_actions.append((enemy, action))
                self.enemy_resolve_idx = 0
                self.enemy_phase = None
                self.enemy_pending_attack = None

        elif self.state == "ENEMY_TURN":
            self._resolve_enemy_turn(dt)

        elif self.state == "TURN_END":
            self._end_turn()

        # Update entities
        self.game.particles.update(dt)
        self.game.floating_text.update(dt)
        for enemy in self.game.enemies:
            enemy.update(dt)
        for p in self.players:
            p.update(dt)

        # Decay passive entropy over time
        if self.state == "PLAYER_INPUT" or self.state == "PLAYER_ACTION_SELECT":
            entropy_rate = settings.DIFFICULTY_SCALING[settings.DIFFICULTY]["entropy_per_turn"]
            self.game.entropy = min(settings.MAX_ENTROPY,
                                    self.game.entropy + entropy_rate * dt * 0.1)

        # Handle host state broadcasting
        if self.game.mp_is_multiplayer and self.game.mp_host:
            self.mp_sync_timer += dt
            if self.mp_sync_timer >= 1.0 / settings.LAN_TICK_RATE:
                self.mp_sync_timer = 0
                self.mp_full_sync_counter += 1
                current_state = self._serialize_mp_state()
                if self.mp_last_state is None or self.mp_full_sync_counter >= self.mp_full_sync_interval:
                    self.mp_full_sync_counter = 0
                    self.mp_last_state = current_state
                    self.game.mp_host.broadcast(current_state)
                else:
                    diff, _ = self._compute_state_diff(current_state, self.mp_last_state)
                    if diff:
                        diff["type"] = "gp_state_diff"
                        self.game.mp_host.broadcast(diff)
                    self.mp_last_state = current_state

            msgs = self.game.mp_host.poll()
            for msg in msgs:
                if msg.get("type") == "gp_cmd":
                    self._apply_remote_gameplay_command(msg)
            self._process_pending_remote_turn()

    def _end_turn(self):
        # Apply regeneration passive first
        for player in self._living_players():
            reg_pct = self.game.skill_tree.get_skill_value("axioma", "regen", 0.0) if self.game.skill_tree else 0.0
            if reg_pct > 0:
                heal = int(player.get_max_hp() * reg_pct)
                if heal > 0:
                    player.hp = min(player.hp + heal, player.get_max_hp())
                    self.game.floating_text.add_heal(player.x, player.y, heal)

        # Tick statuses
        self._tick_enemy_status_effects()
        self._tick_decoy_clones()

        # Tick skill cooldowns
        for player in self.players:
            if player.pitagoras_cooldown > 0: player.pitagoras_cooldown -= 1
            if player.reflexao_cooldown > 0: player.reflexao_cooldown -= 1
            if player.integral_cooldown > 0: player.integral_cooldown -= 1
            if player.fractal_cooldown > 0: player.fractal_cooldown -= 1

        if self.turn_manager.rewind_cooldown_turns > 0:
            self.turn_manager.rewind_cooldown_turns -= 1

        self.turn_manager.turn_number += 1
        self.turn_manager.player_moved = False
        self.turn_manager.player_acted = False
        self.state = "PLAYER_INPUT"
        self.turn_manager.start_turn()
        self._set_active_player(0)
        self._generate_enemy_intents()
        self.danger_locked = False
        self.game.sfx.play("your_turn")

    def _get_player_skill_ids(self):
        ids = []
        if self.game.skill_tree.is_unlocked("pitagoras"): ids.append("pitagoras")
        if self.game.skill_tree.is_unlocked("reflexao"): ids.append("reflexao")
        if self.game.skill_tree.is_unlocked("integral"): ids.append("integral")
        if self.game.skill_tree.is_unlocked("fractal"): ids.append("fractal")
        return ids

    def _generate_enemy_intents(self):
        pc = self.game.player.col
        pr = self.game.player.row
        self.enemy_intents = []
        self.grid.clear_danger_tiles()
        for enemy in self.game.enemies:
            if enemy.dead:
                continue
            intent = enemy.generate_intent(pc, pr, self.grid, self.game.enemies)
            if intent:
                self.enemy_intents.append(intent)
                self.grid.mark_danger_tiles(intent.danger_tiles)

    def _enter_action_select(self):
        self.state = "PLAYER_ACTION_SELECT"
        self.show_action_range = True
        self.selected_skill = None
        self.cursor_col = self.game.player.col
        self.cursor_row = self.game.player.row

    def _get_game_state(self):
        return {
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
            "enemies": [
                {
                    "type": enemy.type,
                    "col": enemy.col,
                    "row": enemy.row,
                    "hp": enemy.hp,
                    "max_hp": enemy.max_hp,
                    "alive": enemy.alive,
                    "dead": enemy.dead,
                    "size": getattr(enemy, 'size', settings.ENEMY_SIZE),
                    "color": getattr(enemy, 'color', settings.RED),
                }
                for enemy in self.game.enemies
            ],
            "entropy": self.game.entropy,
            "barrier_cells": self.grid.barrier_cells.copy(),
            "player_obj": self.game.player,
        }

    def _save_rewind_state(self):
        gs = self._get_game_state()
        self.turn_manager.snapshot(gs)

    # Subsystem Delegations
    def enter(self, prev_scene=None):
        self.room.enter(prev_scene)

    def _get_spawn_position(self):
        return self.room._get_spawn_position()

    def _find_spawn_grid_cell(self):
        return self.room.find_spawn_grid_cell()

    def _generate_tilemap(self):
        self.room.generate_tilemap()

    def _begin_room(self):
        self.room.begin_room()

    def _leave_no_combat_room(self):
        self.room.leave_no_combat_room()

    def _check_victory(self):
        self.room.check_victory()

    def handle_event(self, event):
        self.input_handler.handle_event(event)

    def _set_cursor_from_mouse(self, pos):
        self.input_handler.set_cursor_from_mouse(pos)

    def _toggle_skill(self, skill_id):
        self.input_handler.toggle_skill(skill_id)

    def _build_anim_path(self, from_col, from_row, to_col, to_row, include_barriers=False, extra_blocked=None):
        return self.grid_helpers.build_anim_path(from_col, from_row, to_col, to_row, include_barriers, extra_blocked)

    def _confirm_player_cursor(self):
        self.grid_helpers.confirm_player_cursor()

    def _get_enemy_at_cursor(self):
        return self.grid_helpers.get_enemy_at_cursor()

    def _get_enemies_at_cursor(self):
        return self.grid_helpers.get_enemies_at_cursor()

    def _get_action_cells(self):
        return self.grid_helpers.get_action_cells()

    def _can_execute_cursor_action(self):
        return self.grid_helpers.can_execute_cursor_action()

    def _confirm_action_cursor(self):
        self.grid_helpers.confirm_action_cursor()

    def _execute_basic_attack(self, target_enemies=None):
        self.combat.execute_basic_attack(target_enemies)

    def _execute_skill(self):
        return self.combat.execute_skill()

    def _on_enemy_death(self, enemy):
        self.combat.on_enemy_death(enemy)

    def _apply_weapon_effect(self, enemy):
        self.combat.apply_weapon_effect(enemy)

    def _tick_enemy_status_effects(self):
        self.combat.tick_enemy_status_effects()

    def _tick_decoy_clones(self):
        self.combat.tick_decoy_clones()

    def _resolve_enemy_turn(self, dt):
        self.enemy_executor.resolve_enemy_turn(dt)

    def _enemy_attack(self, enemy):
        self.enemy_executor.enemy_attack(enemy)

    def _enemy_cross_attack(self, enemy):
        self.enemy_executor.enemy_cross_attack(enemy)

    def _enemy_line_attack(self, enemy, action):
        self.enemy_executor.enemy_line_attack(enemy, action)

    def _enemy_ranged_line_attack(self, enemy):
        self.enemy_executor.enemy_ranged_line_attack(enemy)

    def _enemy_area_attack(self, enemy, action):
        self.enemy_executor.enemy_area_attack(enemy, action)

    def _serialize_mp_state(self):
        return self.network_sync.serialize_mp_state()

    def _compute_state_diff(self, current, previous):
        return self.network_sync.compute_state_diff(current, previous)

    def _apply_mp_state(self, msg):
        self.network_sync.apply_mp_state(msg)

    def _broadcast_scene_switch(self, scene_name):
        self.network_sync.broadcast_scene_switch(scene_name)

    def _send_mp_command(self, cmd, **payload):
        self.network_sync.send_mp_command(cmd, **payload)

    def _process_pending_remote_turn(self):
        self.network_sync.process_pending_remote_turn()

    def _apply_remote_gameplay_command(self, msg):
        self.network_sync.apply_remote_gameplay_command(msg)

    def _try_rewind(self):
        self.rewind_handler.try_rewind()

    def draw(self, screen):
        self.renderer.draw(screen)
