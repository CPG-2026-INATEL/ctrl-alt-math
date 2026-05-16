import pygame

from scene import Scene


class SkillTreeScene(Scene):
    overlay = True

    def __init__(self, game):
        super().__init__(game)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_TAB, pygame.K_ESCAPE):
                self.game.scene_manager.pop()
            return

        if event.type == pygame.MOUSEMOTION:
            self.game.skill_tree.update_hover(event.pos)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.game.skill_tree.handle_click(event.pos):
                self.game.sfx.play("skill_unlock")

    def update(self, dt):
        self.game.particles.update(dt)
        self.game.floating_text.update(dt)

    def draw(self, screen):
        self.game.scene_manager.get("gameplay").draw(screen)
        self.game.skill_tree.draw(screen)
