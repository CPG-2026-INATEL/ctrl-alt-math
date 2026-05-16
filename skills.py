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
        # Design width is 800, center the nodes if window is wider
        offset_x = (settings.WINDOW_WIDTH - 800) // 2
        return pygame.Rect(skill["x"] + offset_x - w // 2, skill["y"] - h // 2, w, h)

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
        # Semi-transparent background with a dark tint
        overlay = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 20, 230))
        screen.blit(overlay, (0, 0))

        # Title and Points
        center_x = settings.WINDOW_WIDTH // 2
        draw_text(screen, t("skill_tree_title"), (center_x, 25), settings.WHITE, 42)
        
        # Points indicator with a small box
        points_text = f"{t('skill_points')}: {self.skill_points}"
        points_surf = pygame.font.Font(None, int(30 * settings.UI_SCALE)).render(points_text, True, settings.GOLD)
        points_rect = points_surf.get_rect(center=(center_x, 75))
        pygame.draw.rect(screen, (40, 40, 60), points_rect.inflate(30, 10), border_radius=15)
        pygame.draw.rect(screen, settings.GOLD, points_rect.inflate(30, 10), 2, border_radius=15)
        screen.blit(points_surf, points_rect)

        offset_x = (settings.WINDOW_WIDTH - 800) // 2
        
        # Draw Connections First (to keep them behind nodes)
        for sid, skill in self.skills.items():
            for prereq in skill["prereqs"]:
                if prereq in self.skills:
                    p = self.skills[prereq]
                    start = (p["x"] + offset_x, p["y"])
                    end = (skill["x"] + offset_x, skill["y"])

                    if skill["unlocked"]:
                        color = settings.GREEN
                        width = 3
                    elif self.can_unlock(sid):
                        color = settings.GOLD
                        width = 2
                    else:
                        color = (50, 50, 70)
                        width = 1

                    pygame.draw.line(screen, color, start, end, width)
                    
                    # Add small flow particles for unlocked paths
                    if skill["unlocked"]:
                        time_mod = (pygame.time.get_ticks() / 1000.0) % 1.0
                        px = start[0] + (end[0] - start[0]) * time_mod
                        py = start[1] + (end[1] - start[1]) * time_mod
                        pygame.draw.circle(screen, settings.WHITE, (int(px), int(py)), 2)

        # Draw Nodes
        for sid, skill in self.skills.items():
            rect = self.get_node_rect(skill)
            is_hovered = (self.hovered_id == sid)
            
            # Better colors and contrast
            if skill["unlocked"]:
                bg_color = (20, 80, 20)
                border_color = settings.GREEN
                text_color = settings.WHITE
            elif self.can_unlock(sid):
                bg_color = (80, 70, 20)
                border_color = settings.GOLD
                text_color = settings.WHITE
            else:
                bg_color = (30, 30, 40)
                border_color = (70, 70, 90)
                text_color = (130, 130, 150)

            if is_hovered:
                # Hover effect: Glow and brighter color
                pygame.draw.rect(screen, settings.WHITE, rect.inflate(10, 10), 2, border_radius=8)
                bg_color = tuple(min(255, c + 40) for c in bg_color)
                border_color = settings.WHITE

            # Draw Node Box
            pygame.draw.rect(screen, bg_color, rect, border_radius=6)
            pygame.draw.rect(screen, border_color, rect, 2, border_radius=6)

            # Skill Name
            name_size = 20 if len(t(skill["name"])) < 12 else 18
            draw_text(screen, t(skill["name"]), rect.center, text_color, name_size)

            # Cost Badge (if not unlocked)
            if not skill["unlocked"] and skill["cost"] > 0:
                cost_color = settings.GOLD if self.skill_points >= skill["cost"] else settings.RED
                cost_label = str(skill["cost"])
                badge_rect = pygame.Rect(rect.right - 25, rect.bottom - 20, 20, 18)
                pygame.draw.rect(screen, (20, 20, 30), badge_rect, border_radius=4)
                pygame.draw.rect(screen, cost_color, badge_rect, 1, border_radius=4)
                draw_text(screen, cost_label, badge_rect.center, cost_color, 14)

            # Status Indicator
            if skill["unlocked"]:
                pygame.draw.circle(screen, settings.GREEN, (rect.right - 10, rect.top + 10), 4)

        # Detailed Info Panel for Hovered Skill
        if self.hovered_id:
            skill = self.skills[self.hovered_id]
            panel_w, panel_h = 500, 220
            # Position panel with some margin from the bottom
            panel_rect = pygame.Rect((settings.WINDOW_WIDTH - panel_w) // 2, 
                                     settings.WINDOW_HEIGHT - panel_h - 70, 
                                     panel_w, panel_h)
            
            # Panel Background with glow
            pygame.draw.rect(screen, (15, 15, 30, 250), panel_rect, border_radius=15)
            pygame.draw.rect(screen, settings.CYAN, panel_rect, 2, border_radius=15)
            
            # Skill Title
            title_y = panel_rect.top + 30
            draw_text(screen, t(skill["name"]).upper(), (panel_rect.centerx, title_y), settings.CYAN, 28)
            
            # Description (Handling multiple lines with better spacing)
            desc_y = title_y + 45
            draw_text(screen, t(skill["desc"]), (panel_rect.centerx, desc_y), settings.WHITE, 18)
            
            # Flavor Text (Always at the bottom of the panel)
            flavor_key = f"skill_{self.hovered_id}_flavor"
            draw_text(screen, f"\"{t(flavor_key)}\"", (panel_rect.centerx, panel_rect.bottom - 35), 
                      (100, 200, 200), 15)

        # Footer (Pushed slightly lower)
        draw_text(screen, t("skill_tree_footer"),
                  (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT - 20),
                  settings.GRAY, 14)
