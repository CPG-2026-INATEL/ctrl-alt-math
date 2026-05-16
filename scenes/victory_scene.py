import pygame
import math

import settings
from utils import draw_text
from scenes.scene import Scene


class VictoryScene(Scene):
    overlay = True

    def __init__(self, game):
        super().__init__(game)
        self.qed_timer = 0
        self.qed_alpha = 0
        self.qed_size = 16
        self.qed_color = settings.WHITE

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_RETURN:
            self.game.reset_game_state()
            self.game.scene_manager.switch("gameplay")
        elif event.key == pygame.K_ESCAPE:
            self.game.sfx.play("menu_select")
            self.game.scene_manager.switch("menu")

    def update(self, dt):
        self.game.particles.update(dt)
        self.game.floating_text.update(dt)
        self.qed_timer += dt

    def enter(self, prev_scene=None):
        self.qed_timer = 0
        self.qed_alpha = 0
        self.qed_size = 16
        self.qed_color = settings.WHITE
        self.game.particles.emit_burst(
            settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2,
            settings.GOLD, 50, 150, 1.0
        )
        self.game.sfx.play("victory")

    def draw(self, screen):
        gameplay = self.game.scene_manager.scenes.get("gameplay")
        if gameplay:
            gameplay.draw(screen)

        progress = min(1.0, self.qed_timer / settings.VICTORY_TRANSITION_DURATION)

        self.qed_size = int(16 + 56 * progress)
        self.qed_alpha = int(255 * min(1.0, self.qed_timer / 0.5))
        r = int(255 * (1 - progress) + 255 * progress)
        g = int(255 * (1 - progress) + 215 * progress)
        b = int(255 * (1 - progress) + 0 * progress)
        self.qed_color = (r, g, b)

        qed_surf = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
        qed_surf.fill(settings.BLACK)
        qed_surf.set_alpha(int(100 * progress))
        screen.blit(qed_surf, (0, 0))

        draw_text(screen, "Q.E.D.",
                 (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 - 20),
                 self.qed_color, self.qed_size)

        if progress > 0.5:
            sub_alpha = int(255 * ((progress - 0.5) * 2))
            s = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
            s.set_alpha(sub_alpha)
            s.fill(settings.BLACK)
            screen.blit(s, (0, 0))

            draw_text(screen, "Quod Erat Demonstrandum",
                     (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 + 30),
                     settings.GOLD, 18)
            draw_text(screen, "\"What was to be demonstrated\"",
                     (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 + 55),
                     settings.LIGHT_GRAY, 14)

        self.game.ui.draw_victory(screen)

