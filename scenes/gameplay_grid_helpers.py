import settings

class GameplayGridHelpers:
    def __init__(self, scene):
        self.scene = scene
        self.game = scene.game

    def build_anim_path(self, from_col, from_row, to_col, to_row, include_barriers=False, extra_blocked=None):
        scene = self.scene
        path = []

        def try_axes(horizontal_first):
            test_path = []
            curr_c, curr_r = from_col, from_row
            dc = to_col - from_col
            dr = to_row - from_row

            step_c = 1 if dc > 0 else (-1 if dc < 0 else 0)
            step_r = 1 if dr > 0 else (-1 if dr < 0 else 0)

            if horizontal_first:
                for _ in range(abs(dc)):
                    next_c = curr_c + step_c
                    if scene.grid.is_blocked(next_c, curr_r, include_barriers=include_barriers) or (extra_blocked and (next_c, curr_r) in extra_blocked):
                        return None
                    if scene.grid.is_level_change(curr_c, curr_r, next_c, curr_r):
                        return None
                    test_path.append((next_c, curr_r))
                    curr_c = next_c
                for _ in range(abs(dr)):
                    next_r = curr_r + step_r
                    if scene.grid.is_blocked(curr_c, next_r, include_barriers=include_barriers) or (extra_blocked and (curr_c, next_r) in extra_blocked):
                        return None
                    if scene.grid.is_level_change(curr_c, curr_r, curr_c, next_r):
                        return None
                    test_path.append((curr_c, next_r))
                    curr_r = next_r
            else:
                for _ in range(abs(dr)):
                    next_r = curr_r + step_r
                    if scene.grid.is_blocked(curr_c, next_r, include_barriers=include_barriers) or (extra_blocked and (curr_c, next_r) in extra_blocked):
                        return None
                    if scene.grid.is_level_change(curr_c, curr_r, curr_c, next_r):
                        return None
                    test_path.append((curr_c, next_r))
                    curr_r = next_r
                for _ in range(abs(dc)):
                    next_c = curr_c + step_c
                    if scene.grid.is_blocked(next_c, curr_r, include_barriers=include_barriers) or (extra_blocked and (next_c, curr_r) in extra_blocked):
                        return None
                    if scene.grid.is_level_change(curr_c, curr_r, next_c, curr_r):
                        return None
                    test_path.append((next_c, curr_r))
                    curr_c = next_c
            return test_path

        p1 = try_axes(True)
        if p1 is not None:
            return p1
        p2 = try_axes(False)
        if p2 is not None:
            return p2
        return [(to_col, to_row)]

    def confirm_player_cursor(self):
        scene = self.scene
        game = self.game

        pc = game.player.col
        pr = game.player.row
        cc = scene.cursor_col
        cr = scene.cursor_row

        reachable = scene.grid.get_reachable_cells(
            pc, pr,
            game.player.move_range,
            extra_blocked=scene._other_player_occupied_cells(game.player)
        )

        if (cc, cr) in reachable and (cc, cr) != (pc, pr):
            path = scene.grid.find_path(
                pc, pr,
                cc, cr,
                extra_blocked=scene._other_player_occupied_cells(game.player)
            )
            if path:
                # Save rewind snapshot before acting
                scene._save_rewind_state()
                anim_path = self.build_anim_path(
                    pc, pr,
                    cc, cr,
                    extra_blocked=scene._other_player_occupied_cells(game.player)
                )
                game.player.start_move_anim(pc, pr, cc, cr, scene.grid, path=anim_path)
                
                # Check for stairs or floor triggers
                tile_type = scene.grid.tile_types.get((cc, cr), 0)
                if tile_type in (27, 11, 25, 24):
                    game.sfx.play("stairs")
                else:
                    game.sfx.play("step")
                
                game.player.col = cc
                game.player.row = cr
                scene.tiles_moved_this_turn = len(path)
                scene.state = "RESOLVE_MOVE"
                scene.turn_manager.player_moved = True

        elif (cc, cr) == (pc, pr):
            scene._save_rewind_state()
            scene.tiles_moved_this_turn = 0
            scene.turn_manager.player_moved = True
            scene._enter_action_select()

    def get_enemy_at_cursor(self):
        scene = self.scene
        game = self.game
        for enemy in game.enemies:
            if not enemy.dead and enemy.col == scene.cursor_col and enemy.row == scene.cursor_row:
                return enemy
        return None

    def get_enemies_at_cursor(self):
        scene = self.scene
        game = self.game
        hit_enemies = []
        for enemy in game.enemies:
            if not enemy.dead and enemy.col == scene.cursor_col and enemy.row == scene.cursor_row:
                hit_enemies.append(enemy)
        return hit_enemies

    def get_action_cells(self):
        scene = self.scene
        game = self.game
        pc = game.player.col
        pr = game.player.row

        if scene.selected_skill == "pitagoras":
            return scene.grid.get_cells_in_radius(pc, pr, settings.PITAGORAS_RANGE)
        elif scene.selected_skill == "reflexao":
            return scene.grid.get_cells_in_radius(pc, pr, settings.REFLEXAO_RANGE)
        elif scene.selected_skill == "integral":
            st = game.skill_tree
            radius = st.get_skill_value("integral", "range", settings.INTEGRAL_RANGE)
            return scene.grid.get_cells_in_radius(pc, pr, radius)
        elif scene.selected_skill == "fractal":
            return scene.grid.get_cells_in_radius(pc, pr, 1)
        else:
            return scene.grid.get_cells_in_range(pc, pr, settings.BASIC_ATTACK_RANGE)

    def can_execute_cursor_action(self):
        scene = self.scene
        game = self.game

        cc, cr = scene.cursor_col, scene.cursor_row
        action_cells = self.get_action_cells()
        if (cc, cr) not in action_cells:
            return False

        if scene.selected_skill == "fractal":
            occupied = False
            for p in scene.players:
                if p.col == cc and p.row == cr: occupied = True
            for e in game.enemies:
                if e.col == cc and e.row == cr: occupied = True
            if scene.grid.is_blocked(cc, cr) or occupied:
                return False
            return True

        if scene.selected_skill in ("reflexao", "integral"):
            return True

        # For Pythagoras/basic attack, needs target enemy
        target_enemies = self.get_enemies_at_cursor()
        return len(target_enemies) > 0

    def confirm_action_cursor(self):
        scene = self.scene
        game = self.game

        if self.can_execute_cursor_action():
            if scene.selected_skill:
                # Skill trigger
                if scene._execute_skill():
                    if game.mp_client:
                        scene._send_mp_command(
                            "submit_turn",
                            move=[game.player.col, game.player.row],
                            action="skill",
                            target=[scene.cursor_col, scene.cursor_row],
                            skill_id=scene.selected_skill
                        )
            else:
                # Basic attack trigger
                target_enemies = self.get_enemies_at_cursor()
                scene._execute_basic_attack(target_enemies)
                if game.mp_client:
                    scene._send_mp_command(
                        "submit_turn",
                        move=[game.player.col, game.player.row],
                        action="attack",
                        target=[scene.cursor_col, scene.cursor_row]
                    )
