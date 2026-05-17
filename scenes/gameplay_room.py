import pygame
import random
import settings
from i18n import t
from enemy import Enemy
from enemy_intent import EnemyIntent
from tilemap import TileMap, MapGenerator

class GameplayRoom:
    def __init__(self, scene):
        self.scene = scene
        self.game = scene.game

    def enter(self, prev_scene=None):
        scene = self.scene
        game = self.game

        scene.active_player_idx = 0
        scene.selected_skill = None
        scene.show_move_range = True
        scene.show_action_range = False
        scene.turn_log = []
        scene.mp_cached_state = None
        scene.mp_pending_remote_turn = None
        scene.mp_last_state = None
        scene.mp_sync_timer = 0.0
        scene.mp_full_sync_counter = 0

        game.player.pitagoras_cooldown = 0
        game.player.reflexao_cooldown = 0
        game.player.integral_cooldown = 0
        game.player.fractal_cooldown = 0

        # Initialize network sync request
        scene._send_mp_command("request_sync")

        # Setup players list
        if game.mp_is_multiplayer:
            if not game.mp_host:
                scene.players = [Player() for _ in range(2)]
                for idx, p in enumerate(scene.players):
                    p.player_id = idx + 1
                    if idx == 1:
                        p.skin_index = 1
                game.players = scene.players
                game.player2 = scene.players[1]
            else:
                scene.players = game.players
        else:
            scene.players = [game.player]
            game.players = scene.players

        # Load difficulty multiplier
        difficulty_scaling = settings.DIFFICULTY_SCALING[settings.DIFFICULTY]

        # Reset crits count
        scene.crits_this_room = 0
        scene.player_took_damage_this_room = False

        if game.current_room:
            # Generate deterministic seed for map generator
            room_seed = (game.current_room.col * 1000 + game.current_room.row)
            if settings.DIFFICULTY == "facil":
                room_seed += 10000
            elif settings.DIFFICULTY == "dificil":
                room_seed += 20000
            
            random.seed(room_seed)
            cols = random.randint(11, 15)
            rows = random.randint(11, 15)
            scene.grid = Grid(cols, rows)
            
            # Setup obstacles
            prob = difficulty_scaling["obstacle_density"]
            obstacles = []
            for r in range(rows):
                for c in range(cols):
                    if (c == 0 or c == cols - 1 or r == 0 or r == rows - 1):
                        continue
                    if random.random() < prob:
                        obstacles.append([c, r])
            scene.obstacles_data = obstacles

            # Generate tilemap
            self.generate_tilemap()
            
            # Reposition players
            spawn_col, spawn_row = self.find_spawn_grid_cell()
            game.player.col = spawn_col
            game.player.row = spawn_row
            px, py = scene.grid.to_pixel(spawn_col, spawn_row)
            game.player.x, game.player.y = px, py

            if len(scene.players) > 1:
                p2_spawn_col, p2_spawn_row = spawn_col + 1, spawn_row
                if not scene.grid.is_valid(p2_spawn_col, p2_spawn_row) or scene.grid.is_blocked(p2_spawn_col, p2_spawn_row):
                    p2_spawn_col, p2_spawn_row = spawn_col, spawn_row + 1
                scene.players[1].col = p2_spawn_col
                scene.players[1].row = p2_spawn_row
                p2x, p2y = scene.grid.to_pixel(p2_spawn_col, p2_spawn_row)
                scene.players[1].x, scene.players[1].y = p2x, p2y

            # Position camera
            scene.camera_x = game.player.x - settings.WINDOW_WIDTH / 2
            scene.camera_y = game.player.y - (settings.WINDOW_HEIGHT - settings.UI_BAR_HEIGHT) / 2

            # Spawn enemies if host or offline
            if not game.mp_client or game.mp_host:
                game.enemies = []
                enemy_prob = difficulty_scaling["enemy_count_range"]
                num_enemies = random.randint(enemy_prob[0], enemy_prob[1])
                
                # Check for boss rooms
                is_boss = getattr(game.current_room, "is_final_gate", False) or game.current_room.type == "boss"
                if is_boss:
                    num_enemies = 1
                
                for _ in range(num_enemies):
                    ec, er = self.find_spawn_grid_cell()
                    if is_boss:
                        enemy = Enemy(ec, er, "boss")
                    else:
                        etype = random.choice(["censor", "strawman", "bayesian", "ortogonal", "atirador", "granadeiro"])
                        enemy = Enemy(ec, er, etype)
                    
                    ex, ey = scene.grid.to_pixel(ec, er)
                    enemy.x, enemy.y = ex, ey
                    game.enemies.append(enemy)

            # Set initial room state
            if game.current_room.type == "no_combat":
                scene.state = "NO_COMBAT"
            else:
                scene.state = "WAVE_INTRO"

        scene.cursor_col, scene.cursor_row = game.player.col, game.player.row
        scene.turn_manager.player_moved = False
        scene.turn_manager.player_acted = False
        scene.turn_manager.turn_number = 1
        scene.turn_manager.history = []
        scene.turn_manager.rewind_cooldown_turns = 0

        # Dynamic lore text toast trigger
        scene.lore_toast = None
        if game.current_room and game.current_room.type != "victory" and game.current_room.type != "no_combat":
            scene.lore_toast = {
                "title": t("lore_title_combat"),
                "text": t("lore_desc_combat"),
                "timer": 4.0
            }

        # Clear active scene visuals
        game.floating_text.clear()
        game.particles.clear()

        # Play room entry sounds
        game.sfx.play("victory" if (game.current_room and game.current_room.type == "victory") else "room_enter")

    def find_spawn_grid_cell(self):
        scene = self.scene
        game = self.game

        for attempt in range(100):
            c = random.randint(1, scene.grid.cols - 2)
            r = random.randint(1, scene.grid.rows - 2)
            if not scene.grid.is_blocked(c, r):
                occupied = False
                for p in scene.players:
                    if p.col == c and p.row == r:
                        occupied = True
                for e in game.enemies:
                    if e.col == c and e.row == r:
                        occupied = True
                if not occupied:
                    return c, r
        return 2, 2

    def generate_tilemap(self):
        scene = self.scene
        game = self.game

        try:
            scene.tilemap = TileMap(scene.TILESET_PATH, tile_size=scene.TILE_SIZE)
            scene.grid.blocked.clear()
            
            # Setup barriers list
            barriers_list = [[c, r] for (c, r) in scene.obstacles_data]
            
            # Load MapGenerator
            gen = MapGenerator(scene.grid.cols, scene.grid.rows, barriers_list)
            map_data, tile_types_dict = gen.generate_data()
            
            scene.tilemap.load_from_list(map_data)
            scene.grid.tile_types = tile_types_dict
            
            # Set blocked tiles based on map generator types
            for (col, row), tval in tile_types_dict.items():
                if tval in (16, 61, -1):
                    scene.grid.mark_blocked(col, row, True)
        except Exception:
            scene.tilemap = None

    def begin_room(self):
        scene = self.scene
        game = self.game

        # Lock first-turn intent vectors
        scene.turn_manager.start_turn()
        scene._set_active_player(0)
        scene._generate_enemy_intents()
        scene.state = "PLAYER_INPUT"
        scene.turn_log.append("Battle Start")
        game.sfx.play("your_turn")

    def leave_no_combat_room(self):
        scene = self.scene
        game = self.scene.game

        # Automatically clear room progression check
        if game.world_map:
            game.world_map.mark_cleared(game.current_room.col, game.current_room.row)
            
            # Handle boss achievement unlock
            if getattr(game.current_room, "is_final_gate", False):
                from achievement_manager import AchievementManager
                AchievementManager().unlock("math_god", settings.DIFFICULTY)
                scene._restore_primary_player()
                scene._broadcast_scene_switch("victory")
                game.scene_manager.switch("victory")
                return

        scene._restore_primary_player()
        scene._broadcast_scene_switch("map")
        game.scene_manager.switch("map")

    def check_victory(self):
        scene = self.scene
        game = self.game

        # All non-decoy enemies dead check
        alive_count = sum(1 for e in game.enemies if e.alive and not getattr(e, 'is_decoy', False))
        if alive_count == 0 and scene.state not in ("VICTORY_TRANSITION", "NO_COMBAT"):
            scene.state = "VICTORY_TRANSITION"
            scene.victory_timer = 0
            game.sfx.play("victory")
            
            # Register room complete awards
            if game.world_map:
                game.world_map.mark_cleared(game.current_room.col, game.current_room.row)
                game.skill_tree.skill_points += 1
                
                # Check performance achievements
                mgr = AchievementManager()
                if not scene.player_took_damage_this_room:
                    mgr.unlock("no_damage", settings.DIFFICULTY)
                
                if scene.turn_manager.turn_number < 10:
                    mgr.unlock("fast_win", settings.DIFFICULTY)
                    
                if game.current_room and (game.current_room.type == "victory" or getattr(game.current_room, "is_final_gate", False)):
                    mgr.unlock("math_god", settings.DIFFICULTY)
# imports needed
from grid import Grid
from player import Player
from achievement_manager import AchievementManager
