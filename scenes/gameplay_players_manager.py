from i18n import t
import settings

class GameplayPlayersManager:
    def __init__(self, scene):
        self.scene = scene
        self.game = scene.game

    def is_true_coop(self):
        return self.game.mp_is_multiplayer and len(self.scene.players) > 1

    def refresh_players(self):
        if not self.game.mp_is_multiplayer:
            self.scene.players = [self.game.player]
            self.game.players = self.scene.players

    def living_players(self):
        return [p for p in self.scene.players if p.hp > 0]

    def player_label(self, idx):
        if self.is_true_coop():
            return "P1" if idx == 0 else "P2"
        return t("you")

    def restore_primary_player(self):
        if len(self.scene.players) > 1:
            self.game.player = self.scene.players[0]

    def current_player_owner(self):
        if not self.is_true_coop():
            return "host"
        return "host" if self.scene.active_player_idx == 0 else "client"

    def is_local_turn(self):
        if not self.game.mp_is_multiplayer:
            return True
        owner = self.current_player_owner()
        return (owner == "host" and self.game.mp_host) or (owner == "client" and self.game.mp_client)

    def is_remote_turn(self):
        return self.game.mp_is_multiplayer and not self.is_local_turn()

    def is_client_control_turn(self):
        return self.is_true_coop() and self.current_player_owner() == "client" and bool(self.game.mp_host)

    def set_active_player(self, idx, reset_ui=True):
        if idx >= len(self.scene.players):
            return
        self.scene.active_player_idx = idx
        self.game.player = self.scene.players[idx]
        if reset_ui:
            self.scene.cursor_col = self.game.player.col
            self.scene.cursor_row = self.game.player.row
            self.scene.show_move_range = True
            self.scene.show_action_range = False
            self.scene.selected_skill = None

    def get_local_turn_move_target(self):
        return (self.game.player.col, self.game.player.row)

    def next_living_player_idx(self, start_idx):
        for offset in range(1, len(self.scene.players)):
            candidate = (start_idx + offset) % len(self.scene.players)
            if self.scene.players[candidate].hp > 0:
                return candidate
        return start_idx

    def first_living_player_idx(self):
        for idx, p in enumerate(self.scene.players):
            if p.hp > 0:
                return idx
        return 0

    def target_player_for_enemy(self, enemy):
        living = self.living_players()
        if not living:
            return None
        best_p = None
        min_d = 999999
        for p in living:
            d = self.scene.grid.grid_distance(enemy.col, enemy.row, p.col, p.row)
            if d < min_d:
                min_d = d
                best_p = p
        return best_p

    def target_player_for_cell(self, col, row):
        for p in self.living_players():
            if p.col == col and p.row == row:
                return p
        return None

    def other_player_occupied_cells(self, current_player=None):
        cells = set()
        for p in self.scene.players:
            if p.hp > 0 and p != current_player:
                cells.add((p.col, p.row))
        return cells

    def apply_enemy_damage_to_player(self, enemy, player, dmg, reason):
        if player.hp <= 0:
            return False
        st = self.game.skill_tree
        axioma_unlocked = st.get_skill_value("axioma", "defense_bonus", 0) > 0
        defended = player.take_damage(dmg)
        
        self.scene.player_took_damage_this_room = True
        
        self.game.floating_text.add_player_damage(player.x, player.y, dmg)
        self.game.particles.emit_burst(player.x, player.y, settings.RED, 12, 70, 0.4)
        self.game.screen_shake = 0.15
        self.game.shake_intensity = 5
        self.game.sfx.play("player_hit")
        self.scene.turn_log.append(reason)

        if player.hp <= 0:
            self.game.floating_text.add_info(player.x, player.y, "CRITICAL ERROR", settings.RED)
            self.game.sfx.play("error")
            living = self.living_players()
            if not living:
                self.scene.state = "GAME_OVER_TRANSITION"
                self.scene.game_over_timer = 0.0
                self.game.sfx.play("game_over")
            else:
                next_idx = self.first_living_player_idx()
                self.set_active_player(next_idx)
        return True

    def advance_after_player_turn(self):
        living = self.living_players()
        if not living:
            return

        current_owner = self.current_player_owner()
        next_idx = self.next_living_player_idx(self.scene.active_player_idx)

        if next_idx != self.scene.active_player_idx and next_idx > self.scene.active_player_idx:
            self.set_active_player(next_idx)
            self.scene.state = "PLAYER_INPUT"
            self.game.sfx.play("your_turn")
            if self.game.mp_is_multiplayer and current_owner == "host":
                self.scene.state = "WAIT_REMOTE_SYNC"
        else:
            self.scene._start_enemy_turn()
