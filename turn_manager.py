import copy


class TurnManager:
    def __init__(self):
        self.turn_number = 1
        self.phase = "PLAYER_INPUT"
        self.player_moved = False
        self.player_acted = False
        self.action_queue = []
        self.resolve_timer = 0
        self.resolve_duration = 0
        self.current_action = None
        self.history = []
        self.max_history = 30
        self.rewind_cooldown_turns = 0
        self.barrier_turns_remaining = {}

    def start_turn(self):
        self.phase = "PLAYER_INPUT"
        self.player_moved = False
        self.player_acted = False
        self.action_queue = []
        self.current_action = None

    def can_player_move(self):
        return self.phase == "PLAYER_INPUT" and not self.player_moved

    def can_player_act(self):
        return self.phase == "PLAYER_INPUT" and self.player_moved and not self.player_acted

    def queue_action(self, action):
        self.action_queue.append(action)

    def start_resolve(self, action):
        self.current_action = action
        self.resolve_timer = 0
        if action["type"] == "move":
            self.resolve_duration = 0.3
        elif action["type"] == "attack":
            self.resolve_duration = 0.4
        elif action["type"] == "skill":
            self.resolve_duration = 0.5
        elif action["type"] == "barrier":
            self.resolve_duration = 0.3
        else:
            self.resolve_duration = 0.2

    def update_resolve(self, dt):
        if self.current_action is None:
            return False
        self.resolve_timer += dt
        return self.resolve_timer >= self.resolve_duration

    def finish_current_action(self):
        action = self.current_action
        self.current_action = None
        if action["type"] == "move":
            action["actor"].col = action["target_col"]
            action["actor"].row = action["target_row"]
        return action

    def next_phase(self):
        if self.phase == "PLAYER_INPUT":
            if not self.player_moved:
                return
            if not self.player_acted:
                self.phase = "PLAYER_ACTION_SELECT"
                return
            self.phase = "ENEMY_TURN"
        elif self.phase == "PLAYER_ACTION_SELECT":
            self.phase = "ENEMY_TURN"
        elif self.phase == "ENEMY_TURN":
            self.phase = "TURN_END"

    def snapshot(self, game_state):
        snap = {
            "turn": self.turn_number,
            "player": {
                "col": game_state["player_col"],
                "row": game_state["player_row"],
                "hp": game_state["player_hp"],
                "max_hp": game_state["player_max_hp"],
                "rigor": game_state["player_rigor"],
            },
            "enemies": [],
            "entropy": game_state["entropy"],
            "barrier_cells": list(game_state.get("barrier_cells", set())),
        }
        for e in game_state["enemies"]:
            snap["enemies"].append({
                "type": e.type,
                "col": e.col,
                "row": e.row,
                "hp": e.hp,
                "max_hp": e.max_hp,
                "alive": e.alive,
                "dead": e.dead,
                "size": e.size,
                "color": e.color,
            })
        self.history.append(snap)
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def undo(self, steps=1):
        if not self.history:
            return None
        target = None
        for _ in range(steps):
            if self.history:
                target = self.history.pop()
        if target is not None:
            self.turn_number = target["turn"]
        return target

    def can_undo(self):
        return len(self.history) >= 1 and self.rewind_cooldown_turns <= 0

    def end_turn(self, game_state):
        self.snapshot(game_state)
        self.turn_number += 1
        if self.rewind_cooldown_turns > 0:
            self.rewind_cooldown_turns -= 1
        self.start_turn()
