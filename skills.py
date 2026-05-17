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
            entry["level"] = 0
            entry["max_level"] = 10  # Reasonable cap for linear scaling
            self.skills[s["id"]] = entry

        self.skill_points = settings.PLAYER_START_SKILL_POINTS
        self.hovered_id = None
        self.unlock_animations = {}
        # Start with axioma level 1 (free)
        self.skills["axioma"]["level"] = 1
        
    def get_upgrade_cost(self, skill_id):
        skill = self.skills.get(skill_id)
        if not skill: return 999
        # unlocking (L0->L1) costs 1, lvl up 2 (L1->L2) costs 2, etc.
        return skill["level"] + 1

    def unlock(self, skill_id):
        # This is now effectively "upgrade"
        skill = self.skills.get(skill_id)
        if skill and self.can_unlock(skill_id):
            cost = self.get_upgrade_cost(skill_id)
            skill["level"] += 1
            self.skill_points -= cost
            self.unlock_animations[skill_id] = 0.5
            
            # Check for skill_master achievement
            unlocked_count = sum(1 for s in self.skills.values() if s["level"] > 0)
            if unlocked_count >= 5:
                from achievement_manager import AchievementManager
                AchievementManager().unlock("skill_master", settings.DIFFICULTY)
            
            return True
        return False

    def can_unlock(self, skill_id):
        skill = self.skills.get(skill_id)
        if not skill or skill["level"] >= skill["max_level"]:
            return False
        
        cost = self.get_upgrade_cost(skill_id)
        if self.skill_points < cost:
            return False
            
        # For initial unlock (level 0 -> 1), check prereqs
        if skill["level"] == 0:
            for prereq in skill["prereqs"]:
                p = self.skills.get(prereq)
                if not p or p["level"] == 0:
                    return False
        return True

    def is_unlocked(self, skill_id):
        skill = self.skills.get(skill_id)
        return skill is not None and skill["level"] > 0

    def get_level(self, skill_id):
        skill = self.skills.get(skill_id)
        return skill["level"] if skill else 0

    def is_available(self, skill_id):
        return self.can_unlock(skill_id)

    def get_skill_value(self, skill_id, key, base_val=None):
        level = self.get_level(skill_id)
        if level == 0: return base_val
        
        if skill_id == "axioma":
            # Buffs base damage: +3 per level above 1
            if key == "damage_bonus": return (level - 1) * 3
            
        if skill_id == "pitagoras":
            # Buffs damage: +5 per level; Range: +1 every 2 levels
            if key == "damage": return settings.PITAGORAS_DAMAGE + (level - 1) * 5
            if key == "range": return settings.PITAGORAS_RANGE + (level - 1) // 2
            
        if skill_id == "reflexao":
            # Buffs damage: +4 per level; Range: +1 every 3 levels
            if key == "damage": return settings.REFLEXAO_DAMAGE + (level - 1) * 4
            if key == "range": return settings.REFLEXAO_RANGE + (level - 1) // 3
            
        if skill_id == "ctrlz":
            # Buffs undo turns: +1 every 2 levels; Heal: +5 per level
            if key == "undo_turns": return settings.REWIND_UNDO_TURNS + (level - 1) // 2
            if key == "heal": return settings.REWIND_HEAL_AMOUNT + (level - 1) * 5
            
        if skill_id == "entropia":
            # Buffs entropy reduction: -10% per level
            if key == "reduction": return 0.5 + (level - 1) * 0.1
            
        if skill_id == "derivada":
            # Buffs damage per tile moved: +5% per level
            if key == "move_damage_mult": return 1.0 + (level * 0.05)
            if key == "show_arrows": return level >= 1
            if key == "show_damage_pred": return level >= 3
            if key == "show_crit_pred": return level >= 5

        if skill_id == "bayes":
            # Reveal more info
            if key == "reveal_fake": return level >= 1
            if key == "reveal_target": return level >= 2
            if key == "reveal_next_move": return level >= 4

        if skill_id == "teoria_jogos":
            # Tactical bonuses
            if key == "crit_bonus": return (level) * 0.05 # +5% crit per level
            
        return base_val

    def add_points(self, n):
        self.skill_points += n

    def get_skill(self, skill_id):
        return self.skills.get(skill_id)

    def get_node_rect(self, skill):
        w, h = 100, 32
        x = (skill["x"] - 400) * 0.65 + 200
        y = skill["y"]
        return pygame.Rect(x - w // 2, y - h // 2, w, h)

    def update_hover(self, pos):
        self.hovered_id = None
        for sid, skill in self.skills.items():
            if self.get_node_rect(skill).collidepoint(pos):
                self.hovered_id = sid
                break # Found it

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
        # Semi-transparent background with a dark tint on the left half only
        panel_w = 400
        overlay = pygame.Surface((panel_w, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 20, 240))
        screen.blit(overlay, (0, 0))

        # Gold dividing line on the right edge of the panel
        pygame.draw.line(screen, settings.GOLD, (panel_w, 0), (panel_w, settings.WINDOW_HEIGHT), 2)

        # Title and Points centered at x = 200
        center_x = 200
        draw_text(screen, t("skill_tree_title"), (center_x, 25), settings.WHITE, 28)
        
        # Points indicator with a small box
        points_text = f"{t('skill_points')}: {self.skill_points}"
        points_surf = pygame.font.Font(None, int(20 * settings.UI_SCALE)).render(points_text, True, settings.GOLD)
        points_rect = points_surf.get_rect(center=(center_x, 60))
        pygame.draw.rect(screen, (40, 40, 60), points_rect.inflate(20, 6), border_radius=10)
        pygame.draw.rect(screen, settings.GOLD, points_rect.inflate(20, 6), 2, border_radius=10)
        screen.blit(points_surf, points_rect)
        
        # Draw Connections First
        for sid, skill in self.skills.items():
            for prereq in skill["prereqs"]:
                if prereq in self.skills:
                    p = self.skills[prereq]
                    start = ((p["x"] - 400) * 0.65 + 200, p["y"])
                    end = ((skill["x"] - 400) * 0.65 + 200, skill["y"])

                    if skill["level"] > 0:
                        color = settings.GREEN
                        width = 3
                    elif self.can_unlock(sid):
                        color = settings.GOLD
                        width = 2
                    else:
                        color = (50, 50, 70)
                        width = 1

                    pygame.draw.line(screen, color, start, end, width)
                    
                    if skill["level"] > 0:
                        time_mod = (pygame.time.get_ticks() / 1000.0) % 1.0
                        px = start[0] + (end[0] - start[0]) * time_mod
                        py = start[1] + (end[1] - start[1]) * time_mod
                        pygame.draw.circle(screen, settings.WHITE, (int(px), int(py)), 2)

        # Draw Nodes
        for sid, skill in self.skills.items():
            rect = self.get_node_rect(skill)
            is_hovered = (self.hovered_id == sid)
            level = skill["level"]
            
            if level > 0:
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
                pygame.draw.rect(screen, settings.WHITE, rect.inflate(6, 6), 2, border_radius=8)
                bg_color = tuple(min(255, c + 40) for c in bg_color)
                border_color = settings.WHITE

            pygame.draw.rect(screen, bg_color, rect, border_radius=6)
            pygame.draw.rect(screen, border_color, rect, 2, border_radius=6)

            # Skill Name
            name_text = t(skill["name"])
            if level > 0:
                name_text += f" (Lv.{level})"
            name_size = 13 if len(name_text) < 15 else 11
            draw_text(screen, name_text, rect.center, text_color, name_size)

            # Cost Badge
            cost = self.get_upgrade_cost(sid)
            if level < skill["max_level"]:
                cost_color = settings.GOLD if self.skill_points >= cost else settings.RED
                cost_label = str(cost)
                badge_rect = pygame.Rect(rect.right - 18, rect.bottom - 14, 15, 13)
                pygame.draw.rect(screen, (20, 20, 30), badge_rect, border_radius=3)
                pygame.draw.rect(screen, cost_color, badge_rect, 1, border_radius=3)
                draw_text(screen, cost_label, badge_rect.center, cost_color, 10)

            if level > 0:
                pygame.draw.circle(screen, settings.GREEN, (rect.right - 6, rect.top + 6), 3)

        # Detailed Info Panel inside the left side
        if self.hovered_id:
            skill = self.skills[self.hovered_id]
            panel_w, panel_h = 360, 220
            panel_rect = pygame.Rect(20, 
                                     settings.WINDOW_HEIGHT - panel_h - 40, 
                                     panel_w, panel_h)
            
            pygame.draw.rect(screen, (15, 15, 30, 250), panel_rect, border_radius=12)
            pygame.draw.rect(screen, settings.CYAN, panel_rect, 2, border_radius=12)
            
            title_y = panel_rect.top + 22
            title_text = t(skill["name"]).upper()
            if skill["level"] > 0:
                title_text += f" - LV.{skill['level']}"
            draw_text(screen, title_text, (panel_rect.centerx, title_y), settings.CYAN, 20)
            
            desc_y = title_y + 35
            draw_text(screen, t(skill["desc"]), (panel_rect.centerx, desc_y), settings.WHITE, 14)
            
            # Show Stat Summary
            stats_y = desc_y + 40
            txt = ""
            if self.hovered_id == "axioma":
                txt = f"Base Damage: {settings.PLAYER_ATTACK_DAMAGE + (max(0, skill['level']-1)*3)}"
            elif self.hovered_id == "pitagoras":
                dmg = self.get_skill_value(self.hovered_id, 'damage', settings.PITAGORAS_DAMAGE)
                rng = self.get_skill_value(self.hovered_id, 'range', settings.PITAGORAS_RANGE)
                txt = f"Dmg: {dmg}, Range: {rng}"
            elif self.hovered_id == "derivada":
                mult = self.get_skill_value(self.hovered_id, 'move_damage_mult', 1.0)
                txt = f"Dmg Multiplier: x{mult:.2f} per tile"
            
            if txt:
                draw_text(screen, txt, (panel_rect.centerx, stats_y), settings.GREEN, 14)

            # Show Next Level Buff
            if skill["level"] < skill["max_level"]:
                buff_text = f"Next Level: +Buff (Cost: {self.get_upgrade_cost(self.hovered_id)} SP)"
                draw_text(screen, buff_text, (panel_rect.centerx, stats_y + 22), settings.GOLD, 14)

            flavor_key = f"skill_{self.hovered_id}_flavor"
            draw_text(screen, f"\"{t(flavor_key)}\"", (panel_rect.centerx, panel_rect.bottom - 25), 
                      (100, 200, 200), 12)

        draw_text(screen, t("skill_tree_footer"),
                  (200, settings.WINDOW_HEIGHT - 20),
                  settings.GRAY, 11)
