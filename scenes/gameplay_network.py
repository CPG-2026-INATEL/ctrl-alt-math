import math
import settings
from enemy import Enemy
from enemy_intent import EnemyIntent
from grid import Grid
from tilemap import TileMap
from player import Player

class GameplayNetwork:
    def __init__(self, scene):
        self.scene = scene
        self.game = scene.game

    def serialize_mp_state(self):
        scene = self.scene
        game = self.game

        room = None
        if game.current_room:
            room = [game.current_room.col, game.current_room.row]

        enemy_intents = []
        for intent in scene.enemy_intents:
            if intent is None or intent.enemy.dead:
                continue
            try:
                enemy_index = game.enemies.index(intent.enemy)
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
            "state": scene.state,
            "grid_cols": scene.grid.cols,
            "grid_rows": scene.grid.rows,
            "blocked": [list(cell) for cell in scene.grid.blocked],
            "barriers": [list(cell) for cell in scene.grid.barrier_cells],
            "tile_types": [[c, r, tval] for (c, r), tval in scene.grid.tile_types.items()],
            "tilemap": scene.tilemap.map_data if scene.tilemap else None,
            "player": {
                "col": game.player.col,
                "row": game.player.row,
                "x": game.player.x,
                "y": game.player.y,
                "hp": game.player.hp,
                "max_hp": game.player.max_hp,
                "rigor": game.player.rigor,
            },
            "players": [
                {
                    "col": p.col,
                    "row": p.row,
                    "x": p.x,
                    "y": p.y,
                    "hp": p.hp,
                    "max_hp": p.max_hp,
                    "rigor": p.rigor,
                    "anim": p.current_anim, "dir_x": p.dir_x, "dir_y": p.dir_y, "player_id": getattr(p, "player_id", idx + 1),
                }
                for idx, p in enumerate(scene.players)
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
                    "dead": enemy.dead, "anim": getattr(enemy, "current_anim", "idle"),
                }
                for enemy in game.enemies
            ],
            "cursor": [scene.cursor_col, scene.cursor_row],
            "active_player_idx": scene.active_player_idx,
            "show_move_range": scene.show_move_range,
            "show_action_range": scene.show_action_range,
            "selected_skill": scene.selected_skill,
            "turn": scene.turn_manager.turn_number,
            "player_moved": scene.turn_manager.player_moved,
            "player_acted": scene.turn_manager.player_acted,
            "danger_locked": scene.danger_locked,
            "danger_tiles": [list(entry) for entry in scene.grid.danger_tiles],
            "enemy_intents": enemy_intents,
            "camera": [scene.camera_x, scene.camera_y],
            "entropy": game.entropy,
        }

    def compute_state_diff(self, current, previous):
        if previous is None:
            return current, True
        diff = {}
        for key, value in current.items():
            if key == "type":
                continue
            prev_value = previous.get(key)
            if value != prev_value:
                diff[key] = value
        return diff, False

    def apply_mp_state(self, msg):
        scene = self.scene
        game = self.game

        incoming_state = msg.get("state", scene.state)
        incoming_active_idx = msg.get("active_player_idx", scene.active_player_idx)
        preserve_local_turn = (
            scene._is_client_control_turn()
            and scene.state == incoming_state
            and scene.state != "WAIT_REMOTE_SYNC"
        )
        if scene.state == "WAIT_REMOTE_SYNC" and incoming_active_idx == scene.active_player_idx and incoming_state in (
            "PLAYER_INPUT",
            "PLAYER_ACTION_SELECT",
            "RESOLVE_MOVE",
        ):
            preserve_local_turn = True

        room = msg.get("room")
        if room:
            game.current_room = game.world_map.rooms.get((room[0], room[1]))

        cols = msg.get("grid_cols", scene.grid.cols)
        rows = msg.get("grid_rows", scene.grid.rows)
        if scene.grid.cols != cols or scene.grid.rows != rows:
            scene.grid = Grid(cols, rows)

        scene.grid.blocked = {tuple(cell) for cell in msg.get("blocked", [])}
        scene.grid.barrier_cells = {tuple(cell) for cell in msg.get("barriers", [])}
        scene.grid.tile_types = {(c, r): tval for c, r, tval in msg.get("tile_types", [])}
        scene.grid.danger_tiles = {tuple(entry) for entry in msg.get("danger_tiles", [])}
        scene.danger_locked = msg.get("danger_locked", False)
        scene.grid.danger_locked = scene.danger_locked

        tilemap_data = msg.get("tilemap")
        if tilemap_data is not None:
            try:
                scene.tilemap = TileMap(scene.TILESET_PATH, tile_size=scene.TILE_SIZE)
                scene.tilemap.load_from_list(tilemap_data)
            except Exception:
                pass

        players_data = msg.get("players")
        if players_data and len(scene.players) != len(players_data):
            scene.players = [Player() for _ in players_data]
            for idx, p in enumerate(scene.players):
                p.player_id = idx + 1
                if idx == 1:
                    p.skin_index = 1
            game.players = scene.players
            game.player2 = scene.players[1] if len(scene.players) > 1 else scene.players[0]

        if players_data:
            for idx, data in enumerate(players_data):
                if idx >= len(scene.players):
                    break
                p = scene.players[idx]
                p.col = data.get("col", p.col)
                p.row = data.get("row", p.row)
                p.x = data.get("x", p.x)
                p.y = data.get("y", p.y)
                p.hp = data.get("hp", p.hp)
                p.max_hp = data.get("max_hp", p.max_hp)
                p.rigor = data.get("rigor", p.rigor)
                if "anim" in data: p.current_anim = data["anim"]
                if "dir_x" in data: p.dir_x = data["dir_x"]
                if "dir_y" in data: p.dir_y = data["dir_y"]
        else:
            pdata = msg.get("player", {})
            scene.players[0].col = pdata.get("col", scene.players[0].col)
            scene.players[0].row = pdata.get("row", scene.players[0].row)
            scene.players[0].x = pdata.get("x", scene.players[0].x)
            scene.players[0].y = pdata.get("y", scene.players[0].y)
            scene.players[0].hp = pdata.get("hp", scene.players[0].hp)
            scene.players[0].max_hp = pdata.get("max_hp", scene.players[0].max_hp)
            scene.players[0].rigor = pdata.get("rigor", scene.players[0].rigor)

        enemy_data = msg.get("enemies", [])
        if len(game.enemies) != len(enemy_data) or any(
            i >= len(game.enemies) or game.enemies[i].type != data.get("type")
            for i, data in enumerate(enemy_data)
        ):
            game.enemies = [Enemy(0, 0, data.get("type", "censor")) for data in enemy_data]

        for enemy, data in zip(game.enemies, enemy_data):
            enemy.col = data.get("col", enemy.col)
            enemy.row = data.get("row", enemy.row)
            enemy.x = data.get("x", enemy.x)
            enemy.y = data.get("y", enemy.y)
            enemy.hp = data.get("hp", enemy.hp)
            enemy.max_hp = data.get("max_hp", enemy.max_hp)
            enemy.alive = data.get("alive", enemy.alive)
            enemy.dead = data.get("dead", enemy.dead)
            if "anim" in data: enemy.current_anim = data["anim"]

        scene.enemy_intents = []
        for data in msg.get("enemy_intents", []):
            idx = data.get("enemy_index")
            if idx is None or idx >= len(game.enemies):
                continue
            scene.enemy_intents.append(EnemyIntent(
                enemy=game.enemies[idx],
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
            scene.state = incoming_state
            scene._set_active_player(incoming_active_idx, reset_ui=False)
            scene.cursor_col, scene.cursor_row = msg.get("cursor", [scene.cursor_col, scene.cursor_row])
            scene.show_move_range = msg.get("show_move_range", scene.show_move_range)
            scene.show_action_range = msg.get("show_action_range", scene.show_action_range)
            scene.selected_skill = msg.get("selected_skill", scene.selected_skill)
        scene.turn_manager.turn_number = msg.get("turn", scene.turn_manager.turn_number)
        scene.turn_manager.player_moved = msg.get("player_moved", scene.turn_manager.player_moved)
        scene.turn_manager.player_acted = msg.get("player_acted", scene.turn_manager.player_acted)
        if not preserve_local_turn:
            scene.camera_x, scene.camera_y = msg.get("camera", [scene.camera_x, scene.camera_y])
        game.entropy = msg.get("entropy", game.entropy)

    def broadcast_scene_switch(self, scene_name):
        scene = self.scene
        game = self.game
        if game.mp_is_multiplayer and game.mp_host:
            game.mp_host.broadcast({"type": "scene_switch", "scene": scene_name})

    def send_mp_command(self, cmd, **payload):
        game = self.game
        if game.mp_client:
            msg = {"type": "gp_cmd", "cmd": cmd}
            msg.update(payload)
            game.mp_client.send(msg)

    def process_pending_remote_turn(self):
        scene = self.scene
        game = self.game
        data = scene.mp_pending_remote_turn
        if not data or not scene._is_remote_turn():
            return

        if not data.get("move_done"):
            if scene.state != "PLAYER_INPUT":
                return
            move_col, move_row = data.get("move", (game.player.col, game.player.row))
            scene.cursor_col = move_col
            scene.cursor_row = move_row
            scene._confirm_player_cursor()
            if scene.state != "RESOLVE_MOVE":
                data["move_done"] = True
            return

        if scene.state != "PLAYER_ACTION_SELECT":
            return

        action = data.get("action")
        target = data.get("target")
        skill_id = data.get("skill_id")
        if action == "skill" and skill_id:
            scene.selected_skill = None
            scene._toggle_skill(skill_id)
        if action == "wait":
            scene.cursor_col = game.player.col
            scene.cursor_row = game.player.row
        elif target:
            scene.cursor_col, scene.cursor_row = target
        scene.mp_pending_remote_turn = None
        scene._confirm_action_cursor()

    def apply_remote_gameplay_command(self, msg):
        scene = self.scene
        game = self.game
        cmd = msg.get("cmd")
        if cmd not in ("begin_room", "leave_no_combat", "request_sync") and not scene._is_remote_turn():
            return

        if cmd == "request_sync":
            scene.mp_full_sync_counter = scene.mp_full_sync_interval - 1
            return
        if cmd == "begin_room" and scene.state == "WAVE_INTRO":
            scene._begin_room()
        elif cmd == "leave_no_combat" and scene.state == "NO_COMBAT":
            scene._leave_no_combat_room()
        elif cmd == "cursor_abs" and scene.state in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT"):
            col = int(msg.get("col", scene.cursor_col))
            row = int(msg.get("row", scene.cursor_row))
            scene.cursor_col = max(0, min(scene.grid.cols - 1, col))
            scene.cursor_row = max(0, min(scene.grid.rows - 1, row))
        elif cmd == "confirm":
            if scene.state == "PLAYER_INPUT":
                scene._confirm_player_cursor()
            elif scene.state == "PLAYER_ACTION_SELECT":
                scene._confirm_action_cursor()
        elif cmd == "cancel_action" and scene.state == "PLAYER_ACTION_SELECT":
            scene.selected_skill = None
            scene.show_action_range = True
        elif cmd == "select_skill" and scene.state == "PLAYER_ACTION_SELECT":
            skill_id = msg.get("skill_id")
            if skill_id == "pitagoras" and game.skill_tree.is_unlocked("pitagoras"):
                scene._toggle_skill("pitagoras")
            elif skill_id == "reflexao" and game.skill_tree.is_unlocked("reflexao"):
                scene._toggle_skill("reflexao")
            elif skill_id == "integral" and game.skill_tree.is_unlocked("integral"):
                scene._toggle_skill("integral")
            elif skill_id == "fractal" and game.skill_tree.is_unlocked("fractal"):
                scene._toggle_skill("fractal")
        elif cmd == "rewind" and scene.state in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT"):
            scene._try_rewind()
        elif cmd == "submit_turn" and scene.state in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT", "RESOLVE_MOVE"):
            move = msg.get("move", [game.player.col, game.player.row])
            target = msg.get("target")
            scene.mp_pending_remote_turn = {
                "move": (int(move[0]), int(move[1])) if len(move) == 2 else (game.player.col, game.player.row),
                "action": msg.get("action", "wait"),
                "target": (int(target[0]), int(target[1])) if target and len(target) == 2 else None,
                "skill_id": msg.get("skill_id"),
                "move_done": False,
            }
            self.process_pending_remote_turn()
