import pygame

import settings
from i18n import t
from scenes.scene import Scene


class SkillTreeScene(Scene):
    overlay = True

    def __init__(self, game):
        super().__init__(game)
        self.last_hovered = None

    def enter(self, prev_scene=None):
        if not self.game.skill_tree.hovered_id:
            self.game.skill_tree.hovered_id = "axioma"

    def _unlock_hovered(self):
        sid = self.game.skill_tree.hovered_id
        if sid and self.game.skill_tree.unlock(sid):
            self.game.sfx.play("skill_unlock")

    def _move_selection(self, dx, dy):
        tree = self.game.skill_tree
        if not tree.hovered_id:
            tree.hovered_id = "axioma"
            return

        current = tree.get_skill(tree.hovered_id)
        if not current:
            tree.hovered_id = "axioma"
            return

        best_sid = None
        best_score = None
        for sid, skill in tree.skills.items():
            if sid == tree.hovered_id:
                continue
            vx = skill["x"] - current["x"]
            vy = skill["y"] - current["y"]

            if dx < 0 and vx >= 0:
                continue
            if dx > 0 and vx <= 0:
                continue
            if dy < 0 and vy >= 0:
                continue
            if dy > 0 and vy <= 0:
                continue

            primary = abs(vx) if dx else abs(vy)
            secondary = abs(vy) if dx else abs(vx)
            score = primary * 1000 + secondary
            if best_score is None or score < best_score:
                best_score = score
                best_sid = sid

        if best_sid:
            tree.hovered_id = best_sid

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_s, pygame.K_ESCAPE, pygame.K_TAB):
                self.game.scene_manager.pop()
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._unlock_hovered()
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self._move_selection(-1, 0)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._move_selection(1, 0)
            elif event.key in (pygame.K_UP, pygame.K_w):
                self._move_selection(0, -1)
            elif event.key == pygame.K_DOWN:
                self._move_selection(0, 1)
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
        
        current_hovered = self.game.skill_tree.hovered_id
        if current_hovered and current_hovered != self.last_hovered:
            skill = self.game.skill_tree.get_skill(current_hovered)
            if skill:
                flavor_key = f"skill_{current_hovered}_flavor"
                text = f"{t(skill['name'])}. {t(skill['desc'])}. {t(flavor_key)}"
                self.game.tts.speak(text, lang=settings.LANGUAGE)
        self.last_hovered = current_hovered

    def draw(self, screen):
        if self.game.scene_manager.stack:
            self.game.scene_manager.stack[-1].draw(screen)
        else:
            self.game.scene_manager.get("gameplay").draw(screen)
        self.game.skill_tree.draw(screen)
