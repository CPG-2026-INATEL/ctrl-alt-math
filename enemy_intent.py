class EnemyIntent:
    def __init__(self, enemy, move_target=None, attack_type=None,
                 attack_origin=None, target_tile=None, danger_tiles=None,
                 damage=None, lock_mode="fixed", telegraph_type="line",
                 is_fake=False):
        self.enemy = enemy
        self.move_target = move_target
        self.attack_type = attack_type
        self.attack_origin = attack_origin
        self.target_tile = target_tile
        self.danger_tiles = danger_tiles or set()
        self.damage = damage
        self.lock_mode = lock_mode
        self.telegraph_type = telegraph_type
        self.is_fake = is_fake
        self.resolved = False

    def lock(self):
        if self.lock_mode == "fixed":
            return
        if self.lock_mode == "post_move":
            origin = self.move_target or self.attack_origin
            if origin:
                self.attack_origin = origin

    def get_display_tiles(self, player_skills=None):
        if self.is_fake:
            if player_skills and "bayes" in player_skills:
                return self.danger_tiles, True
            return self.danger_tiles, False
        return self.danger_tiles, False

    def to_action(self):
        if self.attack_type in ("move_then_attack",):
            tc, tr = self.move_target or self.attack_origin or (self.enemy.col, self.enemy.row)
            return {"type": "move_then_attack", "target_col": tc, "target_row": tr, "attack_after": True}
        elif self.attack_type == "move" and self.move_target:
            return {"type": "move", "target_col": self.move_target[0], "target_row": self.move_target[1]}
        elif self.attack_type in ("attack", "line_attack", "area_attack"):
            tc, tr = self.target_tile or (self.enemy.col, self.enemy.row)
            return {"type": self.attack_type, "target_col": tc, "target_row": tr}
        elif self.attack_type == "wait" or self.attack_type is None:
            return {"type": "wait"}
        return {"type": "wait"}