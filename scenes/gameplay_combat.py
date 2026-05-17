import random
import settings
from i18n import t
from enemy import Enemy

class GameplayCombat:
    def __init__(self, scene):
        self.scene = scene
        self.game = scene.game

    def execute_basic_attack(self, target_enemies=None):
        scene = self.scene
        game = self.game

        pc = game.player.col
        pr = game.player.row
        hit_enemies = []

        if target_enemies is not None:
            for enemy in target_enemies:
                d = scene.grid.grid_distance(pc, pr, enemy.col, enemy.row)
                if d <= settings.BASIC_ATTACK_RANGE and not scene.grid.is_level_change(pc, pr, enemy.col, enemy.row):
                    hit_enemies.append(enemy)
        else:
            for enemy in game.enemies:
                if enemy.dead:
                    continue
                d = scene.grid.grid_distance(pc, pr, enemy.col, enemy.row)
                if d <= settings.BASIC_ATTACK_RANGE and not scene.grid.is_level_change(pc, pr, enemy.col, enemy.row):
                    hit_enemies.append(enemy)

        if hit_enemies:
            is_crit = game.player.check_crit()
            st = game.skill_tree
            axioma_bonus = st.get_skill_value("axioma", "damage_bonus", 0)
            derivada_mult = st.get_skill_value("derivada", "move_damage_mult", 1.0)
            move_bonus = 1.0 + (derivada_mult - 1.0) * scene.tiles_moved_this_turn

            for enemy in hit_enemies:
                base_dmg = (game.player.get_attack_damage() + axioma_bonus) * move_bonus
                if is_crit:
                    dmg = int(base_dmg * settings.PLAYER_CRIT_MULTIPLIER)
                else:
                    dmg = int(base_dmg)
                
                dx = abs(enemy.col - pc)
                dy = abs(enemy.row - pr)
                dist_formula = f"d={dx}+{dy}={dx+dy}" if dx + dy < 5 else f"|v|={dx+dy}"
                if scene.tiles_moved_this_turn > 0:
                    dist_formula = f"f'={scene.tiles_moved_this_turn} -> " + dist_formula
                game.floating_text.add_formula(
                    enemy.x, enemy.y - 30,
                    dist_formula, settings.YELLOW if not is_crit else settings.GOLD
                )
                enemy.take_damage(dmg)
                game.floating_text.add_enemy_damage(enemy.x, enemy.y, dmg, is_crit)
                game.particles.emit_burst(enemy.x, enemy.y, settings.WHITE, 8, 60, 0.3)
                game.screen_shake = 0.1 if is_crit else 0.05
                game.shake_intensity = 6 if is_crit else 3
                game.sfx.play("hit")
                scene._apply_weapon_effect(enemy)
                if enemy.dead:
                    scene._on_enemy_death(enemy)
            
            if is_crit:
                scene.crits_this_room += 1
                if scene.crits_this_room >= 3:
                    from achievement_manager import AchievementManager
                    AchievementManager().unlock("crit_thinking", settings.DIFFICULTY)
            
            scene.turn_log.append(f"Attack{' (CRIT!)' if is_crit else ''}")
        else:
            game.floating_text.add_miss(game.player.x, game.player.y)
            scene.turn_log.append("Miss")

        scene.turn_manager.player_acted = True
        scene.show_action_range = False
        scene.selected_skill = None
        if not game.mp_client or game.mp_host:
            scene._check_victory()
            if scene.state == "VICTORY_TRANSITION":
                return
        scene._advance_after_player_turn()

    def execute_skill(self):
        scene = self.scene
        game = self.game

        pc = game.player.col
        pr = game.player.row
        skill = scene.selected_skill

        if skill == "pitagoras":
            target_enemy = scene._get_enemy_at_cursor()
            if target_enemy is None:
                return False
            if not game.player.pitagoras_attack():
                return False
            hit = False
            dx = abs(scene.cursor_col - pc)
            dy = abs(scene.cursor_row - pr)
            is_crit = game.player.check_crit()
            st = game.skill_tree
            dmg_base = st.get_skill_value("pitagoras", "damage", settings.PITAGORAS_DAMAGE)
            derivada_mult = st.get_skill_value("derivada", "move_damage_mult", 1.0)
            move_bonus = 1.0 + (derivada_mult - 1.0) * scene.tiles_moved_this_turn
            
            game.floating_text.add_formula(
                game.player.x, game.player.y - 30,
                f"a^2+b^2=c^2  ({dx}^2+{dy}^2={dx*dx+dy*dy})",
                settings.GOLD if is_crit else settings.YELLOW
            )
            if not scene.grid.is_level_change(pc, pr, target_enemy.col, target_enemy.row):
                dmg = int(dmg_base * move_bonus)
                if is_crit: dmg = int(dmg * settings.PLAYER_CRIT_MULTIPLIER)
                target_enemy.take_damage(dmg)
                game.floating_text.add_enemy_damage(target_enemy.x, target_enemy.y, dmg, is_crit)
                game.particles.emit_burst(target_enemy.x, target_enemy.y, settings.YELLOW, 12, 80, 0.4)
                game.screen_shake = 0.12 if is_crit else 0.08
                game.shake_intensity = 7 if is_crit else 5
                game.sfx.play("enemy_hit")
                hit = True
                if target_enemy.dead:
                    scene._on_enemy_death(target_enemy)
            else:
                game.floating_text.add_evasion(target_enemy.x, target_enemy.y)
            
            if is_crit:
                scene.crits_this_room += 1
                if scene.crits_this_room >= 3:
                    from achievement_manager import AchievementManager
                    AchievementManager().unlock("crit_thinking", settings.DIFFICULTY)

            scene.turn_log.append(f"Pitagoras{' (CRIT!)' if is_crit else ''}" if hit else "Pitagoras Miss")
            game.sfx.play("pitagoras")

        elif skill == "reflexao":
            if not game.player.reflexao_attack():
                return False
            
            # Area damage
            st = game.skill_tree
            radius = st.get_skill_value("reflexao", "range", settings.REFLEXAO_RANGE)
            target_cells = scene.grid.get_cells_in_radius(pc, pr, radius)
            hit_count = 0
            dmg_base = st.get_skill_value("reflexao", "damage", settings.REFLEXAO_DAMAGE)
            derivada_mult = st.get_skill_value("derivada", "move_damage_mult", 1.0)
            move_bonus = 1.0 + (derivada_mult - 1.0) * scene.tiles_moved_this_turn
            
            is_crit = game.player.check_crit()
            dmg = int(dmg_base * move_bonus)
            if is_crit: 
                dmg = int(dmg * settings.PLAYER_CRIT_MULTIPLIER)
            
            for enemy in game.enemies:
                if not enemy.dead and (enemy.col, enemy.row) in target_cells:
                    enemy.take_damage(dmg)
                    game.floating_text.add_formula(enemy.x, enemy.y - 30, "theta_i=theta_r", settings.CYAN)
                    game.floating_text.add_enemy_damage(enemy.x, enemy.y, dmg, is_crit)
                    game.particles.emit_burst(enemy.x, enemy.y, settings.CYAN, 8, 60, 0.3)
                    hit_count += 1
                    if enemy.dead:
                        scene._on_enemy_death(enemy)
            
            if is_crit:
                scene.crits_this_room += 1
                if scene.crits_this_room >= 3:
                    from achievement_manager import AchievementManager
                    AchievementManager().unlock("crit_thinking", settings.DIFFICULTY)

            # Effects
            game.particles.emit_burst(
                game.player.x, game.player.y, settings.CYAN, 30, 120, 0.5
            )
            game.screen_shake = 0.15
            game.shake_intensity = 6
            game.floating_text.add_formula(
                game.player.x, game.player.y - 30,
                "Pulse: sum(E) in area", settings.CYAN
            )
            game.sfx.play("reflexao")
            scene.turn_log.append(f"Reflexao hit {hit_count} enemies")

        elif skill == "integral":
            if not game.player.integral_attack():
                return False
            st = game.skill_tree
            radius = st.get_skill_value("integral", "range", settings.INTEGRAL_RANGE)
            target_cells = scene.grid.get_cells_in_radius(pc, pr, radius)
            dmg_base = st.get_skill_value("integral", "damage", settings.INTEGRAL_DAMAGE)
            lifesteal = st.get_skill_value("integral", "lifesteal", settings.INTEGRAL_LIFESTEAL)
            total_dmg = 0
            hit_count = 0
            for enemy in game.enemies:
                if not enemy.dead and (enemy.col, enemy.row) in target_cells:
                    enemy.take_damage(dmg_base)
                    game.floating_text.add_enemy_damage(enemy.x, enemy.y, dmg_base, False)
                    game.particles.emit_burst(enemy.x, enemy.y, (100, 255, 100), 6, 40, 0.2)
                    total_dmg += dmg_base
                    hit_count += 1
                    if enemy.dead:
                        scene._on_enemy_death(enemy)
            if total_dmg > 0:
                heal = int(total_dmg * lifesteal)
                game.player.hp = min(game.player.hp + heal, game.player.get_max_hp())
                game.floating_text.add_heal(game.player.x, game.player.y, heal)
                game.particles.emit_burst(game.player.x, game.player.y, (100, 255, 100), 15, 80, 0.4)
            game.sfx.play("menu_select")
            scene.turn_log.append(f"Integral hit {hit_count} for {total_dmg} dmg, healed {int(total_dmg * lifesteal)}")

        elif skill == "fractal":
            target_cell = (scene.cursor_col, scene.cursor_row)
            if target_cell == (pc, pr):
                return False
            if scene.grid.is_blocked(scene.cursor_col, scene.cursor_row) or scene.grid.is_level_change(pc, pr, scene.cursor_col, scene.cursor_row):
                return False
            if not game.player.fractal_attack():
                return False
            st = game.skill_tree
            clone_hp = st.get_skill_value("fractal", "hp", settings.FRACTAL_HP_PER_LEVEL)
            level = st.get_level("fractal")
            clone = Enemy(0, 0, "strawman")
            clone.col = scene.cursor_col
            clone.row = scene.cursor_row
            clone.x, clone.y = scene.grid.to_pixel(scene.cursor_col, scene.cursor_row)
            clone.hp = clone_hp
            clone.max_hp = clone_hp
            clone.color = (100, 255, 180)
            clone.is_decoy = True
            clone.decoy_lifetime = level * 2 + 2
            clone.robot_type = "Clone"
            clone.size = settings.ENEMY_SIZE * 0.8
            game.enemies.append(clone)
            game.floating_text.add_info(clone.x, clone.y - 20, "CLONE", (100, 255, 180))
            game.particles.emit_burst(clone.x, clone.y, (100, 255, 180), 20, 100, 0.5)
            game.sfx.play("menu_select")
            scene.turn_log.append(f"Fractal clone spawned with {clone_hp} HP")

        scene.turn_manager.player_acted = True
        scene.show_action_range = False
        scene.selected_skill = None
        if not game.mp_client or game.mp_host:
            scene._check_victory()
            if scene.state == "VICTORY_TRANSITION":
                return True
        scene._advance_after_player_turn()
        return True

    def on_enemy_death(self, enemy):
        scene = self.scene
        game = self.game

        if getattr(enemy, "death_processed", False):
            return
        enemy.death_processed = True
        scene.last_enemy_death_pos = (enemy.x, enemy.y)

        game.floating_text.add_formula(
            enemy.x, enemy.y,
            t("eliminated"), settings.GREEN
        )
        game.particles.emit_burst(enemy.x, enemy.y, enemy.color, 15, 80, 0.4)
        game.floating_text.add_info(enemy.x, enemy.y, t("qed"), settings.GREEN)
        game.screen_shake = 0.1
        game.shake_intensity = 4
        game.sfx.play("enemy_die")

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
            if game.player.add_exp(exp_reward):
                game.floating_text.add_info(game.player.x, game.player.y - 60,
                                                 f"LEVEL UP! ({game.player.level})", settings.GOLD)
                game.sfx.play("victory")
                game.particles.emit_burst(game.player.x, game.player.y, settings.GOLD, 20, 100, 0.5)

    def apply_weapon_effect(self, enemy):
        scene = self.scene
        game = self.game

        if enemy.dead:
            return
        weapon_effect = game.player.get_weapon_effect()
        if not weapon_effect:
            return
        if weapon_effect == "burn":
            enemy.status_effects.append({"effect": "burn", "damage": 3, "turns": 2})
            game.floating_text.add_info(enemy.x, enemy.y - 20, "BURN", settings.ORANGE)
        elif weapon_effect == "poison":
            enemy.status_effects.append({"effect": "poison", "damage": 2, "turns": 3})
            game.floating_text.add_info(enemy.x, enemy.y - 20, "POISON", (100, 200, 50))
        elif weapon_effect == "slow":
            enemy.status_effects.append({"effect": "slow", "turns": 1})
            game.floating_text.add_info(enemy.x, enemy.y - 20, "SLOW", settings.CYAN)
        elif weapon_effect == "stun":
            if random.random() < 0.35:
                enemy.status_effects.append({"effect": "stun", "turns": 1})
                game.floating_text.add_info(enemy.x, enemy.y - 20, "STUN", settings.GOLD)
        elif weapon_effect == "aoe":
            pc = game.player.col
            pr = game.player.row
            for other in game.enemies:
                if other is enemy or other.dead:
                    continue
                dx = abs(other.col - enemy.col)
                dy = abs(other.row - enemy.row)
                if dx + dy <= 1:
                    aoe_dmg = max(1, int(game.player.get_attack_damage() * 0.5))
                    other.take_damage(aoe_dmg)
                    game.floating_text.add_enemy_damage(other.x, other.y, aoe_dmg, False)
                    game.particles.emit_burst(other.x, other.y, settings.YELLOW, 5, 40, 0.2)
                    if other.dead:
                        scene._on_enemy_death(other)

    def tick_enemy_status_effects(self):
        scene = self.scene
        game = self.game

        for enemy in game.enemies:
            if enemy.dead:
                continue
            expired = []
            for i, se in enumerate(enemy.status_effects):
                if se["effect"] == "burn":
                    enemy.take_damage(se["damage"])
                    game.floating_text.add_enemy_damage(enemy.x, enemy.y, se["damage"], False)
                    game.particles.emit_burst(enemy.x, enemy.y, settings.ORANGE, 4, 30, 0.2)
                    se["turns"] -= 1
                    if se["turns"] <= 0:
                        expired.append(i)
                elif se["effect"] == "poison":
                    enemy.take_damage(se["damage"])
                    game.floating_text.add_enemy_damage(enemy.x, enemy.y, se["damage"], False)
                    game.particles.emit_burst(enemy.x, enemy.y, (100, 200, 50), 4, 30, 0.2)
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
                scene._on_enemy_death(enemy)

    def tick_decoy_clones(self):
        scene = self.scene
        game = self.game

        for i in range(len(game.enemies) - 1, -1, -1):
            enemy = game.enemies[i]
            if getattr(enemy, 'is_decoy', False) and not enemy.dead:
                enemy.decoy_lifetime -= 1
                if enemy.decoy_lifetime <= 0:
                    game.particles.emit_burst(enemy.x, enemy.y, (100, 255, 180), 10, 50, 0.3)
                    game.enemies.pop(i)

        scene._check_victory()
