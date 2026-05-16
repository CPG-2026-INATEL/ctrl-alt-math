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