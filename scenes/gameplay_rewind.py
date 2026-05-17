import settings
from i18n import t
from enemy import Enemy

class GameplayRewind:
    def __init__(self, scene):
        self.scene = scene
        self.game = scene.game

    def try_rewind(self):
        scene = self.scene
        game = self.game

        if not game.skill_tree.is_unlocked("ctrlz"):
            game.floating_text.add_info(
                game.player.x, game.player.y - 40,
                t("rewind_locked"), settings.RED
            )
            game.sfx.play("error")
            return
        if not scene.turn_manager.can_undo():
            game.floating_text.add_info(
                game.player.x, game.player.y - 40,
                t("no_rewind_available"), settings.GRAY
            )
            game.sfx.play("error")
            return

        steps = 2 if len(scene.turn_manager.history) >= 2 else 1
        snapshot = scene.turn_manager.undo(steps)
        if snapshot is None:
            return

        player_snaps = snapshot.get("players", [snapshot["player"]])
        actual_heal = 0
        for idx, player_snap in enumerate(player_snaps):
            if idx >= len(scene.players):
                break
            player = scene.players[idx]
            player.col = int(player_snap["col"])
            player.row = int(player_snap["row"])
            player.hp = player_snap["hp"]
            player.max_hp = player_snap["max_hp"]
            old_hp = player.hp
            player.hp = min(player.hp + settings.REWIND_HEAL_AMOUNT, player.max_hp)
            if idx == scene.active_player_idx:
                actual_heal = player.hp - old_hp
            player.rigor = player_snap["rigor"]
            
            # Restore skill cooldowns
            player.pitagoras_cooldown = player_snap.get("pitagoras_cooldown", 0)
            player.reflexao_cooldown = player_snap.get("reflexao_cooldown", 0)
            player.integral_cooldown = player_snap.get("integral_cooldown", 0)
            player.fractal_cooldown = player_snap.get("fractal_cooldown", 0)
            
            px, py = scene.grid.to_pixel(player.col, player.row)
            player.x, player.y = int(px), int(py)

        # Restore enemies list exactly from snapshot to eliminate clones/decoys
        restored_enemies = []
        for i, e_snap in enumerate(snapshot["enemies"]):
            if i < len(game.enemies):
                enemy = game.enemies[i]
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
                
            px, py = scene.grid.to_pixel(enemy.col, enemy.row)
            enemy.x, enemy.y = int(px), int(py)
            restored_enemies.append(enemy)
        game.enemies = restored_enemies

        game.entropy = snapshot["entropy"]

        scene.grid.clear_barriers()
        for col, row in snapshot.get("barrier_cells", []):
            scene.grid.mark_barrier(col, row, True)

        penalty = settings.REWIND_ENTROPY_INCREASE
        if game.skill_tree.is_unlocked("entropia"):
            penalty //= 2

        game.entropy = min(
            game.entropy + penalty,
            settings.MAX_ENTROPY
        )
        scene.turn_manager.rewind_cooldown_turns = settings.REWIND_COOLDOWN_TURNS

        game.rewind_fx_timer = 1.0
        game.sfx.play("rewind")

        game.sfx.play("your_turn")
        scene.state = "PLAYER_INPUT"
        scene.turn_manager.start_turn()
        scene._set_active_player(0)
        scene._generate_enemy_intents()
        scene.danger_locked = False

        game.floating_text.add_info(game.player.x, game.player.y - 40, "<< REWIND >>", settings.GREEN)
        if actual_heal > 0:
            game.floating_text.add_info(game.player.x, game.player.y - 60, f"+{actual_heal} HP", settings.GREEN)
