import pygame
import sys

import settings
from player import Player
from skills import SkillTree
from particles import ParticleSystem
from ui import UI
from sfx import SFX
from floating_text import FloatingTextSystem
from math_bg import MathBackground
from map import WorldMap
from music import MusicManager
from rewind_fx import RewindEffects
from tts_manager import TTSManager
from save_game import save_game, load_game, save_exists

from scenes.scene_manager import SceneManager
from scenes.menu_scene import MenuScene
from scenes.gameplay_scene import GameplayScene
from scenes.skill_tree_scene import SkillTreeScene
from scenes.pause_scene import PauseScene
from scenes.game_over_scene import GameOverScene
from scenes.tilemap_scene import TilemapScene
from scenes.victory_scene import VictoryScene
from scenes.map_scene import MapScene
from scenes.lore_scene import LoreScene
from scenes.lobby_scene import LobbyScene
from scenes.achievement_scene import AchievementScene
from scenes.player_panel_scene import PlayerPanelScene
from scenes.shop_scene import ShopScene
from scenes.inventory_dock_scene import InventoryDockScene
from scenes.upgrades_scene import UpgradesScene
from scenes.equip_dock_scene import EquipDockScene


class Game:
    def __init__(self):
        pygame.init()
        self._configure_display()
        pygame.display.set_caption("Ctrl + Alt + Math")
        self.clock = pygame.time.Clock()
        self.running = True
        self._autosave_timer = 0.0

        self.ui = UI()
        self.sfx = SFX()
        self.music = MusicManager()
        self.rewind_fx = RewindEffects()
        self.tts = TTSManager()

        self.prev_scene_name = None

        self._init_shared_state()
        
        from achievement_manager import AchievementManager
        AchievementManager().ui = self.ui

        self.scene_manager = SceneManager(self)
        self.scene_manager.add("menu", MenuScene)
        self.scene_manager.add("gameplay", GameplayScene)
        self.scene_manager.add("skill_tree", SkillTreeScene)
        self.scene_manager.add("pause", PauseScene)
        self.scene_manager.add("game_over", GameOverScene)
        self.scene_manager.add("victory", VictoryScene)
        self.scene_manager.add("map", MapScene)
        self.scene_manager.add("tilemap", TilemapScene)
        self.scene_manager.add("lore", LoreScene)
        self.scene_manager.add("lobby", LobbyScene)
        self.scene_manager.add("achievements", AchievementScene)
        self.scene_manager.add("player_panel", PlayerPanelScene)
        self.scene_manager.add("shop", ShopScene)
        self.scene_manager.add("inventory_dock", InventoryDockScene)
        self.scene_manager.add("upgrades", UpgradesScene)
        self.scene_manager.add("equip_dock", EquipDockScene)
        self.scene_manager.switch("menu")
        self.music.play_fixed("menu")

    def _configure_display(self):
        display_info = pygame.display.Info()
        mon_w = display_info.current_w
        mon_h = display_info.current_h

        if settings.FULLSCREEN:
            # Exclusive fullscreen — kept as opt-in but BORDERLESS is preferred
            settings.WINDOW_WIDTH = mon_w
            settings.WINDOW_HEIGHT = mon_h
            self.screen = pygame.display.set_mode(
                (settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT),
                pygame.FULLSCREEN | pygame.DOUBLEBUF,
            )
        elif getattr(settings, 'BORDERLESS', False):
            # Borderless windowed: fills the monitor but does NOT change the
            # display resolution, so other windows are unaffected and Alt-Tab
            # works cleanly.
            settings.WINDOW_WIDTH = mon_w
            settings.WINDOW_HEIGHT = mon_h
            self.screen = pygame.display.set_mode(
                (settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT),
                pygame.NOFRAME | pygame.DOUBLEBUF,
            )
        else:
            self.screen = pygame.display.set_mode(
                (settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT),
                pygame.DOUBLEBUF,
            )

        settings.UI_SCALE = min(
            settings.WINDOW_WIDTH / settings.BASE_WIDTH,
            settings.WINDOW_HEIGHT / settings.BASE_HEIGHT,
        )
        settings.UI_BAR_HEIGHT = int(120 * settings.UI_SCALE)

        available_w = settings.WINDOW_WIDTH - 40
        available_h = settings.WINDOW_HEIGHT - settings.UI_BAR_HEIGHT - 30
        arena_w_from_h = int(available_h * settings.GRID_COLS / settings.GRID_ROWS)
        settings.ARENA_WIDTH = min(available_w, arena_w_from_h)
        settings.ARENA_HEIGHT = int(settings.ARENA_WIDTH * settings.GRID_ROWS / settings.GRID_COLS)
        settings.ARENA_OFFSET_X = (settings.WINDOW_WIDTH - settings.ARENA_WIDTH) // 2
        settings.ARENA_OFFSET_Y = max(15, (available_h - settings.ARENA_HEIGHT) // 2 + 10)

        settings.MAP_ROOM_WIDTH = int(120 * settings.UI_SCALE)
        settings.MAP_ROOM_HEIGHT = int(80 * settings.UI_SCALE)
        settings.MAP_ROOM_GAP = int(30 * settings.UI_SCALE)
        
        # Dynamic map dimensions based on difficulty
        scaling = settings.DIFFICULTY_SCALING.get(settings.DIFFICULTY, settings.DIFFICULTY_SCALING["medium"])
        map_depth = scaling.get("depth", 7)
        map_cols = map_depth + 1
        map_rows = 4
        
        map_width = map_cols * settings.MAP_ROOM_WIDTH + (map_cols - 1) * settings.MAP_ROOM_GAP
        map_height = map_rows * settings.MAP_ROOM_HEIGHT + (map_rows - 1) * settings.MAP_ROOM_GAP
        settings.MAP_OFFSET_X = max(40, (settings.WINDOW_WIDTH - map_width) // 2)
        top_space = int(90 * settings.UI_SCALE)
        bottom_space = int(170 * settings.UI_SCALE)
        settings.MAP_OFFSET_Y = max(top_space, (settings.WINDOW_HEIGHT - bottom_space - map_height) // 2)

    def _init_shared_state(self):
        self.players = [Player(), Player()]
        self.players[0].player_id = 1
        self.players[1].player_id = 2
        self.players[1].skin_index = 1
        self.player = self.players[0]
        self.player2 = self.players[1]
        self.skill_tree = SkillTree()
        self.particles = ParticleSystem()
        self.enemies = []
        self.floating_text = FloatingTextSystem()
        self.math_bg = MathBackground()
        self.world_map = WorldMap()
        self.world_map._game = self

        self.entropy = 0
        self.rewind_cooldown = 0
        self.rewind_fx_timer = 0
        self.gold = 0
        self.mp_is_multiplayer = False
        self.mp_player_index = 1
        self.mp_host = None
        self.mp_client = None
        self.player.gold = 0
        self.player.equipment = {"weapon": "basic_sword", "shield": "wooden_shield"}
        self.player.inventory = [{"id": "hp_potion_small", "count": 2}, {"id": "atk_tonic", "count": 1}]

        self.screen_shake = 0.0
        self.shake_intensity = 0

        self.prev_scene_name = None

        self.hit_stop_timer = 0
        self.hit_stop_duration = 0

        self.current_room = None
        self.boss_hp_override = None

        from grid import Grid
        self.obstacles = Grid().obstacle_rects(settings.ARENA_OBSTACLES)

    def reset_game_state(self):
        self._configure_display()
        self.players = [Player(), Player()]
        self.players[0].player_id = 1
        self.players[1].player_id = 2
        self.players[1].skin_index = 1
        self.player = self.players[0]
        self.player2 = self.players[1]
        self.skill_tree = SkillTree()
        self.particles = ParticleSystem()
        self.enemies = []
        self.floating_text = FloatingTextSystem()
        self.math_bg = MathBackground()
        self.world_map = WorldMap()
        self.world_map._game = self

        self.entropy = 0
        self.rewind_cooldown = 0
        self.rewind_fx_timer = 0
        self.gold = 0
        self.player.gold = 0
        self.player.equipment = {"weapon": "basic_sword", "shield": "wooden_shield"}
        self.player.inventory = [{"id": "hp_potion_small", "count": 2}, {"id": "atk_tonic", "count": 1}]

        self.screen_shake = 0.0
        self.shake_intensity = 0

        self.prev_scene_name = None

        self.hit_stop_timer = 0
        self.hit_stop_duration = 0

        self.current_room = None
        self.boss_hp_override = None

        from grid import Grid
        self.obstacles = Grid().obstacle_rects(settings.ARENA_OBSTACLES)

    def reset_player_state(self):
        self.players = [Player(), Player()]
        self.players[0].player_id = 1
        self.players[1].player_id = 2
        self.players[1].skin_index = 1
        self.player = self.players[0]
        self.player2 = self.players[1]
        self.skill_tree = SkillTree()
        self.particles = ParticleSystem()
        self.enemies = []
        self.floating_text = FloatingTextSystem()
        self.math_bg = MathBackground()

        self.entropy = 0
        self.rewind_cooldown = 0
        self.rewind_fx_timer = 0

        self.screen_shake = 0.0
        self.shake_intensity = 0

        self.hit_stop_timer = 0
        self.hit_stop_duration = 0

        self.current_room = None
        self.boss_hp_override = None

        from grid import Grid
        self.obstacles = Grid().obstacle_rects(settings.ARENA_OBSTACLES)

    def save_progress(self):
        if self.mp_is_multiplayer:
            return
        save_game(self)

    def load_progress(self):
        return load_game(self)

    def can_continue(self):
        return save_exists()

    def run(self):
        while self.running:
            dt = self.clock.tick(settings.FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    if self.scene_manager.current:
                        self.scene_manager.current.handle_event(event)
                
                if event.type == pygame.ACTIVEEVENT:
                    if event.state & pygame.APPACTIVE and event.gain:
                        # Gained focus - could trigger a redraw or resume
                        pass

            if self.scene_manager.current:
                self.scene_manager.current.update(dt)

            scene_name = self.scene_manager.current.__class__.__name__ if self.scene_manager.current else ""
            if scene_name != self.prev_scene_name:
                self.prev_scene_name = scene_name
                self._update_music(scene_name)
            if not self.mp_is_multiplayer and scene_name not in {"MenuScene", "LobbyScene"}:
                self._autosave_timer += dt
                if self._autosave_timer >= 2.0:
                    self._autosave_timer = 0.0
                    self.save_progress()
            else:
                self._autosave_timer = 0.0

            self.tts.update()
            
            # Use get_active to check if window is visible/focused
            # This helps preventing black screen glitches on some systems
            if pygame.display.get_active():
                self.screen.fill(self.math_bg.get_bg_color())
                if self.scene_manager.current:
                    self.scene_manager.current.draw(self.screen)
                
                # Global UI overlays
                if self.ui.achievement_queue:
                    toast = self.ui.achievement_queue[0]
                    toast.update(dt)
                    self.ui.draw_achievement_notification(self.screen, toast)
                    if toast.is_dead():
                        self.ui.achievement_queue.pop(0)
                
                pygame.display.flip()
            else:
                pygame.time.delay(10)

        self.tts.stop()
        self.music.stop(fade_ms=500)
        pygame.quit()
        sys.exit()

    def _update_music(self, scene_name):
        fixed_map = {
            "MenuScene": "menu",
            "LobbyScene": "menu",
            "MapScene": "map",
            "PlayerPanelScene": "map",
            "ShopScene": "map",
            "EquipDockScene": "map",
            "UpgradesScene": "map",
            "VictoryScene": "victory",
            "GameOverScene": "game_over",
            "AchievementScene": "menu",
            "LoreScene": "menu",
        }
        overlay_scenes = {
            "PauseScene", "SkillTreeScene", "InventoryDockScene",
        }
        if scene_name in overlay_scenes:
            return

        track = fixed_map.get(scene_name)
        if track:
            self.music.play_fixed(track)
        # GameplayScene handles its own music via play_room in enter()
