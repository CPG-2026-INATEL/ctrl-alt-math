import settings
from i18n import t

class GameplayEnemyExecutor:
    def __init__(self, scene):
        self.scene = scene
        self.game = scene.game

    def resolve_enemy_turn(self, dt):
        scene = self.scene
        game = self.game

        if scene.enemy_resolve_idx >= len(scene.enemy_actions):
            scene.enemy_phase = None
            scene.state = "TURN_END"
            return

        if not scene._living_players():
            scene.enemy_phase = None
            scene.state = "TURN_END"
            return

        if scene.enemy_pending_attack is not None:
            scene.enemy_phase = "ATTACK"
            enemy, attack_type, action = scene.enemy_pending_attack
            if enemy.is_animating():
                return
            scene.enemy_attack_delay_timer += dt
            if scene.enemy_attack_delay_timer < scene.ENEMY_ATTACK_DELAY:
                return
            scene.enemy_pending_attack = None
            scene.enemy_attack_delay_timer = 0
            if attack_type == "attack":
                self.enemy_attack(enemy)
            elif attack_type == "line_attack":
                self.enemy_line_attack(enemy, action)
            elif attack_type == "area_attack":
                self.enemy_area_attack(enemy, action)
            elif attack_type == "cross_attack":
                self.enemy_cross_attack(enemy)
            elif attack_type == "ranged_line_attack":
                self.enemy_ranged_line_attack(enemy)
            scene.enemy_resolve_idx += 1
            return

        enemy, action = scene.enemy_actions[scene.enemy_resolve_idx]
        if enemy.dead:
            scene.enemy_resolve_idx += 1
            return

        scene.turn_manager.resolve_timer += dt
        if scene.turn_manager.resolve_timer < 0.15:
            return

        scene.turn_manager.resolve_timer = 0

        if action["type"] == "wait":
            scene.enemy_phase = "MOVE"
            scene.turn_log.append(f"{enemy.type} waits")
        elif action["type"] == "move":
            scene.enemy_phase = "MOVE"
            tc, tr = action["target_col"], action["target_row"]
            if scene.grid.is_valid(tc, tr) and not scene.grid.is_blocked(tc, tr, include_barriers=True):
                if not scene.grid.is_level_change(enemy.col, enemy.row, tc, tr):
                    old_col, old_row = enemy.col, enemy.row
                    anim_path = scene._build_anim_path(old_col, old_row, tc, tr, include_barriers=True)
                    enemy.start_move_anim(old_col, old_row, tc, tr, scene.grid, path=anim_path)
                    enemy.col = tc
                    enemy.row = tr
                    scene.turn_log.append(f"{enemy.type} moved")
                else:
                    scene.turn_log.append(f"{enemy.type} can't reach")
            else:
                scene.turn_log.append(f"{enemy.type} blocked")

        elif action["type"] == "move_then_attack":
            scene.enemy_phase = "MOVE"
            tc, tr = action["target_col"], action["target_row"]
            moved = False
            if scene.grid.is_valid(tc, tr) and not scene.grid.is_blocked(tc, tr, include_barriers=True):
                if not scene.grid.is_level_change(enemy.col, enemy.row, tc, tr):
                    old_col, old_row = enemy.col, enemy.row
                    anim_path = scene._build_anim_path(old_col, old_row, tc, tr, include_barriers=True)
                    enemy.start_move_anim(old_col, old_row, tc, tr, scene.grid, path=anim_path)
                    enemy.col = tc
                    enemy.row = tr
                    scene.turn_log.append(f"{enemy.type} moved")
                    moved = True
                else:
                    scene.turn_log.append(f"{enemy.type} can't reach")
            else:
                scene.turn_log.append(f"{enemy.type} blocked")
            if moved:
                attack_type = "attack"
                if enemy.type == "ortogonal":
                    attack_type = "cross_attack"
                elif enemy.type == "atirador":
                    attack_type = "ranged_line_attack"
                elif enemy.type == "granadeiro":
                    attack_type = "area_attack"
                scene.enemy_pending_attack = (enemy, attack_type, action)
                scene.enemy_attack_delay_timer = 0
                scene.enemy_phase = "ATTACK"
                return

        elif action["type"] == "attack":
            scene.enemy_phase = "ATTACK"
            if enemy.type == "ortogonal":
                self.enemy_cross_attack(enemy)
            elif enemy.type == "atirador":
                self.enemy_ranged_line_attack(enemy)
            else:
                self.enemy_attack(enemy)

        elif action["type"] == "line_attack":
            scene.enemy_phase = "ATTACK"
            if enemy.type == "boss":
                self.enemy_line_attack(enemy, action)
            else:
                self.enemy_ranged_line_attack(enemy)

        elif action["type"] == "area_attack":
            scene.enemy_phase = "ATTACK"
            self.enemy_area_attack(enemy, action)

        elif action["type"] == "cross_attack":
            scene.enemy_phase = "ATTACK"
            self.enemy_cross_attack(enemy)

        scene.enemy_resolve_idx += 1

    def enemy_attack(self, enemy):
        scene = self.scene
        game = self.game

        target = scene._target_player_for_enemy(enemy)
        if target is None:
            scene.turn_log.append(f"{enemy.type} attack missed")
            return

        d = scene.grid.grid_distance(enemy.col, enemy.row, target.col, target.row)
        if d <= enemy.attack_range and not scene.grid.is_level_change(enemy.col, enemy.row, target.col, target.row):
            dmg = enemy.roll_damage(game.entropy)
            dx = abs(target.col - enemy.col)
            dy = abs(target.row - enemy.row)
            if scene._apply_enemy_damage_to_player(enemy, target, dmg, f"{enemy.type} hit {scene._player_label(scene.players.index(target))} for {dmg}{' (CRIT!)' if enemy.last_crit else ''}"):
                if enemy.last_crit:
                    game.floating_text.add_formula(
                        target.x, target.y + 15,
                        f"CRITICAL! ({dx}+{dy}={dx+dy})", settings.ORANGE
                    )
        elif d <= enemy.attack_range:
            game.floating_text.add_evasion(enemy.x, enemy.y)
            scene.turn_log.append(f"{enemy.type} can't reach (elevation)")
        else:
            scene.turn_log.append(f"{enemy.type} attack missed")

    def enemy_cross_attack(self, enemy):
        scene = self.scene
        game = self.game

        ec, er = enemy.col, enemy.row
        hit_cells = [(ec, er - 1), (ec, er + 1), (ec - 1, er), (ec + 1, er)]
        dmg = enemy.roll_damage()
        for player in scene._living_players():
            if (player.col, player.row) in hit_cells and not scene.grid.is_level_change(ec, er, player.col, player.row):
                label = scene._player_label(scene.players.index(player))
                scene._apply_enemy_damage_to_player(enemy, player, dmg, f"Ortogonal cross hit {label} for {dmg}{' (CRIT!)' if enemy.last_crit else ''}")
        for cx, cy in hit_cells:
            if scene.grid.is_valid(cx, cy):
                px, py = scene.grid.to_pixel(cx, cy)
                game.particles.emit_burst(px, py, settings.ORANGE, 5, 40, 0.3)
        game.sfx.play("hit")

    def enemy_line_attack(self, enemy, action):
        scene = self.scene
        game = self.game

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
        dmg = enemy.roll_damage(game.entropy)
        game.floating_text.add_formula(
            enemy.x, enemy.y - 30,
            f"Phase {['I','II','III'][phase-1]} -> |v|={count}",
            settings.ORANGE
        )

        for i in range(count):
            offset = i - (count - 1) // 2
            c = enemy.col + step_dc * settings.BOSS_ATTACK_RANGE
            r = enemy.row + step_dr * settings.BOSS_ATTACK_RANGE + offset
            c = max(0, min(scene.grid.cols - 1, c))
            r = max(0, min(scene.grid.rows - 1, r))

            for player in scene._living_players():
                if c == player.col and r == player.row:
                    label = scene._player_label(scene.players.index(player))
                    scene._apply_enemy_damage_to_player(enemy, player, dmg, f"Boss line attack hit {label} for {dmg}!")

        game.particles.emit_burst(enemy.x, enemy.y, (255, 100, 100), 10, 50, 0.3)
        game.sfx.play("pitagoras")
        scene.turn_log.append(f"Boss line attack")

    def enemy_ranged_line_attack(self, enemy):
        scene = self.scene
        game = self.game

        target = scene._target_player_for_enemy(enemy)
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

        game.floating_text.add_formula(
            enemy.x, enemy.y - 30,
            f"|v|={range_val}", settings.YELLOW
        )

        for i in range(1, range_val + 1):
            c = ec + step_dc * i
            r = er + step_dr * i
            if not scene.grid.is_valid(c, r):
                break
            if scene.grid.is_blocked(c, r):
                break
            px, py = scene.grid.to_pixel(c, r)
            game.particles.emit_burst(px, py, settings.ORANGE, 3, 30, 0.2)
            for player in scene._living_players():
                if c == player.col and r == player.row and not scene.grid.is_level_change(ec, er, c, r):
                    label = scene._player_label(scene.players.index(player))
                    if scene._apply_enemy_damage_to_player(enemy, player, dmg, f"Atirador line attack hit {label} for {dmg}{' (CRIT!)' if enemy.last_crit else ''}"):
                        hit = True

        game.sfx.play("hit")
        scene.turn_log.append(f"Atirador line attack{' hit!' if hit else ' missed'}")

    def enemy_area_attack(self, enemy, action):
        scene = self.scene
        game = self.game

        tc, tr = action["target_col"], action["target_row"]
        radius = 2
        dmg = enemy.roll_damage(game.entropy)
        hit = False
        game.floating_text.add_formula(
            enemy.x, enemy.y - 30,
            f"int dA  r={radius}", settings.RED
        )
        for col in range(tc - radius, tc + radius + 1):
            for row in range(tr - radius, tr + radius + 1):
                for player in scene._living_players():
                    if col == player.col and row == player.row:
                        label = scene._player_label(scene.players.index(player))
                        if scene._apply_enemy_damage_to_player(enemy, player, dmg, f"Boss AoE hit {label} for {dmg}!"):
                            hit = True

        cx, cy = scene.grid.to_pixel(tc, tr)
        game.particles.emit_burst(cx, cy, settings.RED, 20, 80, 0.4)
        game.sfx.play("boss_phase")
        if not hit:
            scene.turn_log.append(f"Boss AoE missed")
