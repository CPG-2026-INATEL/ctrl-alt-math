import pygame
import sys

import settings
from player import Player
from skills import SkillTree
from rewind import RewindBuffer
from particles import ParticleSystem
from ui import UI
from sfx import SFX
from floating_text import FloatingTextSystem

from scenes.scene_manager import SceneManager
from scenes.menu_scene import MenuScene
from scenes.gameplay_scene import GameplayScene
from scenes.skill_tree_scene import SkillTreeScene
from scenes.pause_scene import PauseScene
from scenes.game_over_scene import GameOverScene
from scenes.victory_scene import VictoryScene
from scenes.tilemap_scene import TilemapScene


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT)
        )
        pygame.display.set_caption("Ctrl + Alt + Math")
        self.clock = pygame.time.Clock()
        self.running = True

        self.ui = UI()
        self.sfx = SFX()

        self._init_shared_state()

        self.scene_manager = SceneManager(self)
        self.scene_manager.add("menu", MenuScene)
        self.scene_manager.add("gameplay", GameplayScene)
        self.scene_manager.add("skill_tree", SkillTreeScene)
        self.scene_manager.add("pause", PauseScene)
        self.scene_manager.add("game_over", GameOverScene)
        self.scene_manager.add("victory", VictoryScene)
        self.scene_manager.add("tilemap", TilemapScene)
        self.scene_manager.switch("tilemap")

    def _init_shared_state(self):
        self.player = Player()
        self.skill_tree = SkillTree()
        self.rewind_buffer = RewindBuffer()
        self.particles = ParticleSystem()
        self.enemies = []
        self.projectiles = []
        self.floating_text = FloatingTextSystem()
        self.current_wave = 0
        self.entropy = 0
        self.rewind_cooldown = 0
        self.screen_shake = 0.0
        self.shake_intensity = 0
        self.queue_basic_damage = False
        self.queue_pitagoras_damage = False
        self.hit_stop_timer = 0
        self.hit_stop_duration = 0
        self.wave_countdown = 0
        self.wave_countdown_duration = 1.5
        self.obstacles = [pygame.Rect(o["x"], o["y"], o["w"], o["h"])
                          for o in settings.ARENA_OBSTACLES]

    def reset_game_state(self):
        self._init_shared_state()

    def run(self):
        while self.running:
            dt = self.clock.tick(settings.FPS) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()
        pygame.quit()
        sys.exit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                self.scene_manager.current.handle_event(event)

    def _update(self, dt):
        self.scene_manager.current.update(dt)

    def _draw(self):
        self.scene_manager.current.draw(self.screen)
        pygame.display.flip()
