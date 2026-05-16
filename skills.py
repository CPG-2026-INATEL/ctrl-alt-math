import pygame
import math

import settings
from utils import draw_text
from i18n import t


class SkillTree:
    def __init__(self):
        self.skills = {}
        for s in settings.SKILL_TREE_DATA:
            entry = dict(s)
            entry["unlocked"] = False
            self.skills[s["id"]] = entry

        self.skill_points = settings.PLAYER_START_SKILL_POINTS
        self.hovered_id = None
        self.unlock_animations = {}
        self.unlock("axioma")

    def unlock(self, skill_id):
        skill = self.skills.get(skill_id)
        if skill and not skill["unlocked"] and self.can_unlock(skill_id):
            skill["unlocked"] = True
            self.skill_points -= skill["cost"]
            self.unlock_animations[skill_id] = 0.5
            return True
        return False

    def can_unlock(self, skill_id):
        skill = self.skills.get(skill_id)
        if not skill or skill["unlocked"]:
            return False
        if self.skill_points < skill["cost"]:
            return False
        for prereq in skill["prereqs"]:
            p = self.skills.get(prereq)
            if not p or not p["unlocked"]:
                return False
        return True

    def is_unlocked(self, skill_id):
        skill = self.skills.get(skill_id)
        return skill is not None and skill["unlocked"]

    def is_available(self, skill_id):
        return self.can_unlock(skill_id)

    def add_points(self, n):
        self.skill_points += n

    def get_skill(self, skill_id):
        return self.skills.get(skill_id)

    def get_node_rect(self, skill):
        w, h = 160, 46
        return pygame.Rect(skill["x"] - w // 2, skill["y"] - h // 2, w, h)

    def update_hover(self, pos):
        self.hovered_id = None
        for sid, skill in self.skills.items():
            if self.get_node_rect(skill).collidepoint(pos):
                self.hovered_id = sid
                return

        for sid in list(self.unlock_animations.keys()):
            self.unlock_animations[sid] -= 0.016
            if self.unlock_animations[sid] <= 0:
                del self.unlock_animations[sid]

    def handle_click(self, pos):
        for sid, skill in self.skills.items():
            if self.get_node_rect(skill).collidepoint(pos):
                return self.unlock(sid)
        return False

    def draw(self, screen):
        overlay = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(settings.BLACK)
        screen.blit(overlay, (0, 0))

        draw_text(screen, t("skill_tree_title"), (settings.WINDOW_WIDTH // 2, 20),
                  settings.WHITE, 36)

        for sid, skill in self.skills.items():
            for prereq in skill["prereqs"]:
                if prereq in self.skills:
                    p = self.skills[prereq]
                    start = (p["x"], p["y"] + 23)
                    end = (skill["x"], skill["y"] - 23)

                    if skill["unlocked"]:
                        color = settings.GREEN
                    elif self.can_unlock(sid):
                        color = settings.GOLD
                    else:
                        color = (60, 60, 60)

                    pygame.draw.line(screen, color, start, end, 2)

                    if skill["unlocked"]:
                        dx = end[0] - start[0]
                        dy = end[1] - start[1]
                        length = max(1, math.sqrt(dx * dx + dy * dy))
                        steps = int(length / 8)
                        for i in range(steps):
                            frac = i / steps
                            px = start[0] + dx * frac
                            py = start[1] + dy * frac
                            pygame.draw.circle(screen, (30, 120, 30), (int(px), int(py)), 1)

        for sid, skill in self.skills.items():
            rect = self.get_node_rect(skill)
            is_hovered = (self.hovered_id == sid)
            unlock_anim = self.unlock_animations.get(sid, 0)

            if skill["unlocked"]:
                color = (50, 180, 50)
                border_color = settings.GREEN
            elif self.can_unlock(sid):
                color = (180, 160, 40)
                border_color = settings.GOLD
            else:
                color = (50, 50, 50)
                border_color = (80, 80, 80)

            if is_hovered:
                border_color = settings.WHITE
                color = tuple(min(255, c + 20) for c in color)

            if unlock_anim > 0:
                glow_size = int(10 * (unlock_anim / 0.5))
                glow_surf = pygame.Surface((rect.width + glow_size * 2, rect.height + glow_size * 2))
                glow_surf.set_alpha(int(100 * (unlock_anim / 0.5)))
                glow_surf.fill(settings.GREEN)
                screen.blit(glow_surf, (rect.x - glow_size, rect.y - glow_size))

            pygame.draw.rect(screen, color, rect, border_radius=4)
            pygame.draw.rect(screen, border_color, rect, 2, border_radius=4)

            name_color = settings.WHITE if skill["unlocked"] or self.can_unlock(sid) else (120, 120, 120)
            draw_text(screen, t(skill["name"]), rect.center, name_color, 18)
            cost_text = t("cost_label", cost=skill['cost']) if skill["cost"] > 0 else t("cost_free")
            draw_text(screen, cost_text, (rect.centerx, rect.bottom + 10),
                      settings.LIGHT_GRAY, 14)

            if skill["unlocked"]:
                check_surf = pygame.font.Font(None, 20).render(t("skill_unlocked_ok"), True, settings.GREEN)
                screen.blit(check_surf, (rect.right - 20, rect.top + 5))

        draw_text(screen, f"{t('skill_points')}: {self.skill_points}",
                  (settings.WINDOW_WIDTH // 2, 110),
                  settings.GOLD, 28)

        if self.hovered_id:
            skill = self.skills[self.hovered_id]
            lines = t(skill["desc"]).split('\n')
            y_offset = settings.WINDOW_HEIGHT - 40 - len(lines) * 20
            for i, line in enumerate(lines):
                draw_text(screen, line,
                          (settings.WINDOW_WIDTH // 2, y_offset + i * 22),
                          settings.LIGHT_GRAY, 16)

        draw_text(screen, t("skill_tree_footer"),
                  (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT - 15),
                  settings.GRAY, 14)
