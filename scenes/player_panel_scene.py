import pygame
import math

import settings
from i18n import t
from scenes.scene import Scene
from skills import SkillTree
from utils import draw_text


TAB_UPGRADES = 0
TAB_SKILLS = 1
TAB_INVENTORY = 2
TAB_EQUIP = 3

TAB_LABELS = ["UPGRADES", "SKILLS", "INV", "EQUIP"]
TAB_COLORS = [settings.ORANGE, settings.GOLD, settings.GREEN, settings.PURPLE]


class PlayerPanelScene(Scene):
    overlay = True

    def __init__(self, game):
        super().__init__(game)
        self.active_tab = TAB_UPGRADES
        self.scroll_y = 0
        self.hovered_upgrade = None
        self.hovered_skill = None
        self.hovered_item = None
        self.hovered_equip_slot = None

    def enter(self, prev_scene=None):
        if prev_scene and prev_scene.__class__.__name__ == "MapScene":
            self.active_tab = TAB_INVENTORY
        else:
            self.active_tab = TAB_UPGRADES
        self.scroll_y = 0
        self._sync_gold()

    def _sync_gold(self):
        self.game.gold = self.game.player.gold

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB or event.key == pygame.K_ESCAPE:
                self._sync_gold()
                self.game.scene_manager.pop()
                return
            if event.key == pygame.K_1 or event.key == pygame.K_u:
                self.active_tab = TAB_UPGRADES
                self.scroll_y = 0
            elif event.key == pygame.K_2:
                self.active_tab = TAB_SKILLS
                self.scroll_y = 0
            elif event.key == pygame.K_3:
                self.active_tab = TAB_INVENTORY
                self.scroll_y = 0
            elif event.key == pygame.K_4:
                self.active_tab = TAB_EQUIP
                self.scroll_y = 0

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)

        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y -= event.y * 30
            max_scroll = self._get_max_scroll()
            self.scroll_y = max(0, min(max_scroll, self.scroll_y))

        if event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)

    def _handle_click(self, pos):
        mx, my = pos
        tab_y = 10
        tab_h = 30
        tab_w = settings.WINDOW_WIDTH // 4
        for i in range(4):
            tab_rect = pygame.Rect(i * tab_w, tab_y, tab_w, tab_h)
            if tab_rect.collidepoint(mx, my):
                self.active_tab = i
                self.scroll_y = 0
                return

        if self.active_tab == TAB_UPGRADES:
            self._handle_upgrade_click(pos)
        elif self.active_tab == TAB_SKILLS:
            self._handle_skill_click(pos)
        elif self.active_tab == TAB_INVENTORY:
            self._handle_inventory_click(pos)

    def _handle_upgrade_click(self, pos):
        mx, my = pos
        content_x = settings.WINDOW_WIDTH // 2 + 20
        content_w = settings.WINDOW_WIDTH // 2 - 40
        player = self.game.player

        for i, utype in enumerate(["atk", "def", "hp", "range"]):
            row_y = 80 + i * 80 - int(self.scroll_y)
            buy_x = content_x + content_w - 80
            buy_y = row_y + 30
            buy_rect = pygame.Rect(buy_x, buy_y, 70, 28)
            if buy_rect.collidepoint(mx, my):
                if player.buy_upgrade(utype):
                    self._sync_gold()
                    return

    def _handle_skill_click(self, pos):
        mx, my = pos
        if not self.game.skill_tree:
            return
        skill_tree = self.game.skill_tree
        content_x = settings.WINDOW_WIDTH // 2 + 20
        content_w = settings.WINDOW_WIDTH // 2 - 40
        content_h = settings.WINDOW_HEIGHT - 100
        scale = min(content_w / 800, content_h / 520)
        node_w = int(160 * scale)
        node_h = int(46 * scale)
        offset_x = content_x + (content_w - int(800 * scale)) // 2
        offset_y = 80 - int(self.scroll_y)

        for skill in skill_tree.skills.values():
            sx = offset_x + int(skill["x"] * scale) - node_w // 2
            sy = offset_y + int(skill["y"] * scale) - node_h // 2
            node_rect = pygame.Rect(sx, sy, node_w, node_h)
            if node_rect.collidepoint(mx, my):
                if skill_tree.can_unlock(skill["id"]):
                    skill_tree.unlock(skill["id"])
                    return

    def _handle_inventory_click(self, pos):
        mx, my = pos
        player = self.game.player
        content_x = settings.WINDOW_WIDTH // 2 + 20
        item_w = (settings.WINDOW_WIDTH // 2 - 60) // 2
        item_h = 55
        sy = int(self.scroll_y)

        for i, item in enumerate(player.inventory):
            col = i % 2
            row = i // 2
            ix = content_x + 10 + col * (item_w + 10)
            iy = 80 + row * (item_h + 5) - sy
            use_rect = pygame.Rect(ix + item_w - 50, iy + 30, 45, 20)
            if use_rect.collidepoint(mx, my):
                item_data = settings.CONSUMABLE_DATA.get(item.get("id"), {})
                if item_data and item_data.get("effect") == "heal":
                    player.use_consumable(item["id"])
                    self._sync_gold()
                    self.game.sfx.play("menu_select")
                    return
                elif item_data:
                    player.use_consumable(item["id"])
                    self._sync_gold()
                    self.game.sfx.play("menu_select")
                    return

    def _update_hover(self, pos):
        mx, my = pos
        self.hovered_upgrade = None
        self.hovered_skill = None
        self.hovered_item = None
        self.hovered_equip_slot = None

        if self.active_tab == TAB_UPGRADES:
            content_x = settings.WINDOW_WIDTH // 2 + 20
            content_w = settings.WINDOW_WIDTH // 2 - 40
            for i, utype in enumerate(["atk", "def", "hp", "range"]):
                row_y = 80 + i * 80 - int(self.scroll_y)
                row_rect = pygame.Rect(content_x, row_y, content_w, 70)
                if row_rect.collidepoint(mx, my):
                    self.hovered_upgrade = utype

        elif self.active_tab == TAB_SKILLS:
            if self.game.skill_tree:
                skill_tree = self.game.skill_tree
                content_w = settings.WINDOW_WIDTH // 2 - 40
                content_h = settings.WINDOW_HEIGHT - 100
                scale = min(content_w / 800, content_h / 520)
                node_w = int(160 * scale)
                node_h = int(46 * scale)
                offset_x = settings.WINDOW_WIDTH // 2 + 20 + (content_w - int(800 * scale)) // 2
                offset_y = 80 - int(self.scroll_y)
                for skill in skill_tree.skills.values():
                    sx = offset_x + int(skill["x"] * scale) - node_w // 2
                    sy = offset_y + int(skill["y"] * scale) - node_h // 2
                    node_rect = pygame.Rect(sx, sy, node_w, node_h)
                    if node_rect.collidepoint(mx, my):
                        self.hovered_skill = skill["id"]

        elif self.active_tab == TAB_INVENTORY:
            pass

        elif self.active_tab == TAB_EQUIP:
            content_x = settings.WINDOW_WIDTH // 2 + 20
            equip_area_y = 80 - int(self.scroll_y)
            slot_w = 200
            slot_h = 60
            for slot_name, y_off in [("weapon", 0), ("shield", 70)]:
                slot_rect = pygame.Rect(content_x + 20, equip_area_y + y_off, slot_w, slot_h)
                if slot_rect.collidepoint(mx, my):
                    self.hovered_equip_slot = slot_name

    def _get_max_scroll(self):
        if self.active_tab == TAB_UPGRADES:
            return max(0, 4 * 80 - (settings.WINDOW_HEIGHT - 100))
        elif self.active_tab == TAB_INVENTORY:
            player = self.game.player
            rows = max(1, (len(player.inventory) + 1) // 2)
            return max(0, rows * 60 - (settings.WINDOW_HEIGHT - 100))
        return 0

    def update(self, dt):
        pass

    def draw(self, screen):
        overlay = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 30, 230))
        screen.blit(overlay, (0, 0))

        self._draw_tabs(screen)
        self._draw_left_panel(screen)

        content_clip = pygame.Rect(settings.WINDOW_WIDTH // 2, 45,
                                   settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT - 55)
        screen.set_clip(content_clip)

        if self.active_tab == TAB_UPGRADES:
            self._draw_upgrades(screen)
        elif self.active_tab == TAB_SKILLS:
            self._draw_skills(screen)
        elif self.active_tab == TAB_INVENTORY:
            self._draw_inventory(screen)
        elif self.active_tab == TAB_EQUIP:
            self._draw_equipment(screen)

        screen.set_clip(None)

    def _draw_tabs(self, screen):
        tab_y = 10
        tab_h = 30
        tab_w = settings.WINDOW_WIDTH // 4
        for i in range(4):
            tab_rect = pygame.Rect(i * tab_w, tab_y, tab_w, tab_h)
            is_active = (i == self.active_tab)
            bg_color = (35, 40, 70, 230) if is_active else (10, 10, 25, 180)
            
            tab_surf = pygame.Surface((tab_w, tab_h), pygame.SRCALPHA)
            pygame.draw.rect(tab_surf, bg_color, (0, 0, tab_w, tab_h), border_radius=4)
            screen.blit(tab_surf, tab_rect)
            
            border_color = TAB_COLORS[i] if is_active else (50, 50, 70)
            pygame.draw.rect(screen, border_color, tab_rect, 2 if is_active else 1, border_radius=4)
            
            if is_active:
                # Glowing neon indicator at bottom of active tab
                pygame.draw.line(screen, TAB_COLORS[i], (i * tab_w + 12, tab_y + tab_h - 3), ((i + 1) * tab_w - 12, tab_y + tab_h - 3), 3)

            label_font = pygame.font.Font(None, 16)
            label = label_font.render(TAB_LABELS[i], True,
                                      TAB_COLORS[i] if is_active else (120, 120, 140))
            screen.blit(label, (tab_rect.centerx - label.get_width() // 2,
                                tab_rect.centery - label.get_height() // 2))

    def _draw_left_panel(self, screen):
        panel_w = settings.WINDOW_WIDTH // 2
        panel_h = settings.WINDOW_HEIGHT - 50
        panel_y = 50

        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((12, 12, 28, 220))
        screen.blit(panel_surf, (0, panel_y))

        # Thin neon border dividing panels
        pygame.draw.line(screen, (50, 50, 80), (panel_w - 1, panel_y), (panel_w - 1, settings.WINDOW_HEIGHT), 1)

        player = self.game.player
        lx = 25
        bar_w = panel_w - 50
        bar_h = 16
        content_right = panel_w - 25

        y = panel_y + 20

        sprite = player.get_current_sprite()
        sprite_size = 110
        center_x = panel_w // 2
        cy = y + sprite_size // 2

        # Rotating math scan vector circles around player sprite
        time_val = pygame.time.get_ticks() / 1000.0
        
        # Inner scan ring
        r1 = sprite_size // 2 + 10
        pygame.draw.circle(screen, (0, 80, 80, 100), (center_x, cy), r1, 1)
        for d_idx in range(3):
            ang = time_val * 1.5 + d_idx * (2 * math.pi / 3)
            dx = int(center_x + r1 * math.cos(ang))
            dy = int(cy + r1 * math.sin(ang))
            pygame.draw.circle(screen, settings.CYAN, (dx, dy), 4)

        # Outer scan ring
        r2 = sprite_size // 2 + 20
        pygame.draw.circle(screen, (80, 60, 0, 100), (center_x, cy), r2, 1)
        for d_idx in range(4):
            ang = -time_val * 1.0 + d_idx * (math.pi / 2)
            dx = int(center_x + r2 * math.cos(ang))
            dy = int(cy + r2 * math.sin(ang))
            pygame.draw.circle(screen, settings.GOLD, (dx, dy), 3)

        if sprite:
            scaled = pygame.transform.scale(sprite, (sprite_size, sprite_size))
            flip = pygame.transform.flip(scaled, True, False) if player.dir_x < 0 else scaled
            screen.blit(flip, (center_x - sprite_size // 2, y))
        else:
            pygame.draw.rect(screen, settings.CYAN,
                             (center_x - sprite_size // 2, y,
                              sprite_size, sprite_size), border_radius=8)
            pygame.draw.rect(screen, settings.WHITE,
                             (center_x - sprite_size // 2, y,
                              sprite_size, sprite_size), 2, border_radius=8)
        y += sprite_size + 16

        # Draw character name card
        name_card = pygame.Rect(center_x - 60, y, 120, 24)
        pygame.draw.rect(screen, (30, 40, 60), name_card, border_radius=12)
        pygame.draw.rect(screen, settings.GOLD, name_card, 1, border_radius=12)
        draw_text(screen, f"Lv.{player.level}", (center_x, y + 12), settings.GOLD, 16)
        y += 36

        pygame.draw.line(screen, (40, 40, 60), (lx, y), (content_right, y), 1)
        y += 12

        hp_pct = max(0, player.hp / player.get_max_hp()) if player.get_max_hp() > 0 else 0
        self._draw_bar(screen, lx, y, bar_w, bar_h, hp_pct, settings.RED, (60, 20, 20))
        draw_text(screen, f"HP {player.hp}/{player.get_max_hp()}",
                 (lx + 8, y + 2), settings.WHITE, 12, center=False)
        y += bar_h + 8

        xp_pct = player.exp / player.next_level_exp if player.next_level_exp > 0 else 0
        self._draw_bar(screen, lx, y, bar_w, bar_h, xp_pct, settings.GOLD, (40, 40, 10))
        draw_text(screen, f"XP {player.exp}/{player.next_level_exp}",
                 (lx + 8, y + 2), settings.WHITE, 12, center=False)
        y += bar_h + 16

        # High-tech stat badges
        col_w = (bar_w - 20) // 2
        badge_h = 24
        
        # Row 1: Attack & Defense
        pygame.draw.rect(screen, (35, 15, 15), (lx, y, col_w, badge_h), border_radius=4)
        pygame.draw.rect(screen, settings.RED, (lx, y, col_w, badge_h), 1, border_radius=4)
        draw_text(screen, f"ATK: {player.get_attack_damage()}", (lx + 10, y + badge_h // 2), settings.RED, 14, center=False)
        
        pygame.draw.rect(screen, (15, 15, 35), (lx + col_w + 10, y, col_w, badge_h), border_radius=4)
        pygame.draw.rect(screen, settings.BLUE, (lx + col_w + 10, y, col_w, badge_h), 1, border_radius=4)
        draw_text(screen, f"DEF: {player.get_defense()}", (lx + col_w + 20, y + badge_h // 2), settings.BLUE, 14, center=False)
        y += badge_h + 8

        # Row 2: Range & Gold
        pygame.draw.rect(screen, (15, 35, 35), (lx, y, col_w, badge_h), border_radius=4)
        pygame.draw.rect(screen, settings.CYAN, (lx, y, col_w, badge_h), 1, border_radius=4)
        draw_text(screen, f"RANGE: {player.get_move_range()}", (lx + 10, y + badge_h // 2), settings.CYAN, 14, center=False)
        
        pygame.draw.rect(screen, (35, 35, 15), (lx + col_w + 10, y, col_w, badge_h), border_radius=4)
        pygame.draw.rect(screen, settings.GOLD, (lx + col_w + 10, y, col_w, badge_h), 1, border_radius=4)
        draw_text(screen, f"GOLD: {player.gold}", (lx + col_w + 20, y + badge_h // 2), settings.GOLD, 14, center=False)
        y += badge_h + 8

        # Row 3: SP & Tickets
        sp = self.game.skill_tree.skill_points if self.game.skill_tree else 0
        pygame.draw.rect(screen, (25, 15, 35), (lx, y, col_w, badge_h), border_radius=4)
        pygame.draw.rect(screen, settings.PURPLE, (lx, y, col_w, badge_h), 1, border_radius=4)
        draw_text(screen, f"SP: {sp}", (lx + 10, y + badge_h // 2), settings.PURPLE, 14, center=False)
        
        tickets = getattr(player, "upgrade_tickets", 0)
        pygame.draw.rect(screen, (35, 25, 15), (lx + col_w + 10, y, col_w, badge_h), border_radius=4)
        pygame.draw.rect(screen, settings.GOLD, (lx + col_w + 10, y, col_w, badge_h), 1, border_radius=4)
        draw_text(screen, f"TICKETS: {tickets}", (lx + col_w + 20, y + badge_h // 2), settings.GOLD, 14, center=False)
        y += badge_h + 16

        pygame.draw.line(screen, (40, 40, 60), (lx, y), (content_right, y), 1)

    def _draw_upgrades(self, screen):
        player = self.game.player
        content_x = settings.WINDOW_WIDTH // 2 + 20
        content_w = settings.WINDOW_WIDTH // 2 - 40

        draw_text(screen, "UPGRADES", (content_x + 10, 55), settings.WHITE, 22, center=False)
        tickets = getattr(player, "upgrade_tickets", 0)
        if tickets > 0:
            draw_text(screen, f"Tickets: {tickets}", (content_x + content_w - 120, 55), settings.GOLD, 14, center=False)

        upgrade_info = [
            ("atk", "ATK", "+3 per level", settings.RED),
            ("def", "DEF", "+2 per level", settings.BLUE),
            ("hp", "HP", "+15 max per level", settings.GREEN),
            ("range", "RANGE", "+1 move per level", settings.CYAN),
        ]

        sy = int(self.scroll_y)
        for i, (utype, name, desc, color) in enumerate(upgrade_info):
            row_y = 80 + i * 80 - sy
            if row_y < 45 or row_y > settings.WINDOW_HEIGHT:
                continue

            level = player.upgrades[utype]
            cost = player.get_upgrade_cost(utype)
            can_afford = player.gold >= cost

            row_rect = pygame.Rect(content_x, row_y, content_w, 70)
            bg_color = (25, 25, 50) if i % 2 == 0 else (20, 20, 40)
            pygame.draw.rect(screen, bg_color, row_rect, border_radius=6)
            if self.hovered_upgrade == utype:
                pygame.draw.rect(screen, color, row_rect, 2, border_radius=6)

            draw_text(screen, f"{name}", (content_x + 15, row_y + 8), color, 18, center=False)
            draw_text(screen, f"Lv.{level}", (content_x + 100, row_y + 8), settings.WHITE, 16, center=False)
            draw_text(screen, desc, (content_x + 15, row_y + 30), settings.GRAY, 13, center=False)

            bonus_map = {"atk": 3 * level, "def": 2 * level, "hp": 15 * level, "range": level}
            draw_text(screen, f"+{bonus_map[utype]}", (content_x + 15, row_y + 48), settings.GOLD, 13, center=False)

            if tickets > 0:
                buy_color = settings.GREEN
                buy_text_color = settings.BLACK
                button_label = "FREE"
            else:
                buy_color = settings.GREEN if can_afford else settings.DARK_GRAY
                buy_text_color = settings.BLACK if can_afford else settings.GRAY
                button_label = f"{cost}g"

            buy_rect = pygame.Rect(content_x + content_w - 80, row_y + 30, 70, 28)
            pygame.draw.rect(screen, buy_color, buy_rect, border_radius=4)
            draw_text(screen, button_label, (buy_rect.centerx, buy_rect.centery + 2), buy_text_color, 14)

    def _draw_skills(self, screen):
        skill_tree = self.game.skill_tree
        if not skill_tree:
            content_x = settings.WINDOW_WIDTH // 2 + 20
            draw_text(screen, "No skill tree available", (content_x + 10, 80), settings.GRAY, 18)
            return

        content_x = settings.WINDOW_WIDTH // 2 + 20
        content_w = settings.WINDOW_WIDTH // 2 - 40
        content_h = settings.WINDOW_HEIGHT - 100

        scale = min(content_w / 800, content_h / 520)
        node_w = int(160 * scale)
        node_h = int(46 * scale)
        offset_x = content_x + (content_w - int(800 * scale)) // 2
        offset_y = 80 - int(self.scroll_y)

        draw_text(screen, "SKILLS", (content_x + 10, 55), settings.GOLD, 22, center=False)
        draw_text(screen, f"Points: {skill_tree.skill_points}", (content_x + content_w - 80, 55), settings.GOLD, 14, center=False)

        for skill in skill_tree.skills.values():
            sx = offset_x + int(skill["x"] * scale) - node_w // 2
            sy = offset_y + int(skill["y"] * scale) - node_h // 2
            level = skill_tree.get_level(skill["id"])
            unlocked = level > 0
            can_unlock = skill_tree.can_unlock(skill["id"])

            node_rect = pygame.Rect(sx, sy, node_w, node_h)
            if unlocked:
                bg = skill.get("color", settings.CYAN)
                bg_dark = (bg[0] // 3, bg[1] // 3, bg[2] // 3)
                pygame.draw.rect(screen, bg_dark, node_rect, border_radius=4)
                pygame.draw.rect(screen, bg, node_rect, 2, border_radius=4)
            elif can_unlock:
                pygame.draw.rect(screen, (30, 30, 50), node_rect, border_radius=4)
                pygame.draw.rect(screen, settings.GRAY, node_rect, 1, border_radius=4)
            else:
                pygame.draw.rect(screen, (15, 15, 25), node_rect, border_radius=4)
                pygame.draw.rect(screen, (40, 40, 50), node_rect, 1, border_radius=4)

            font = pygame.font.Font(None, int(12 * settings.UI_SCALE))
            label = font.render(t(skill["name"])[:12], True,
                                settings.WHITE if unlocked else settings.GRAY)
            screen.blit(label, (node_rect.centerx - label.get_width() // 2,
                                 node_rect.centery - int(6 * settings.UI_SCALE)))
            lv_text = pygame.font.Font(None, int(10 * settings.UI_SCALE)).render(f"Lv.{level}", True, settings.GOLD if unlocked else settings.DARK_GRAY)
            screen.blit(lv_text, (node_rect.centerx - lv_text.get_width() // 2,
                                    node_rect.centery + int(3 * settings.UI_SCALE)))

            for prereq_id in skill.get("prereqs", []):
                prereq = skill_tree.skills.get(prereq_id)
                if prereq:
                    px = offset_x + int(prereq["x"] * scale)
                    py = offset_y + int(prereq["y"] * scale)
                    nx = offset_x + int(skill["x"] * scale)
                    ny = offset_y + int(skill["y"] * scale)
                    
                    is_prereq_unlocked = skill_tree.get_level(prereq_id) > 0
                    line_color = settings.GREEN if is_prereq_unlocked else (40, 40, 50)
                    pygame.draw.line(screen, line_color, (px, py), (nx, ny), 2)
                    
                    # Animated energy flow dots along the connection path!
                    if is_prereq_unlocked:
                        time_val = pygame.time.get_ticks() / 1000.0
                        progress = (time_val * 0.8) % 1.0
                        dot_x = int(px + (nx - px) * progress)
                        dot_y = int(py + (ny - py) * progress)
                        pygame.draw.circle(screen, settings.GOLD, (dot_x, dot_y), 4)
                        pygame.draw.circle(screen, settings.WHITE, (dot_x, dot_y), 2)

        if self.hovered_skill:
            skill = skill_tree.skills.get(self.hovered_skill)
            if skill:
                self._draw_skill_popup(screen, skill, skill_tree, content_x, content_w)

    def _draw_skill_popup(self, screen, skill, skill_tree, content_x, content_w):
        popup_w = content_w
        popup_h = 95
        popup_x = content_x
        popup_y = settings.WINDOW_HEIGHT - popup_h - 70

        popup_surf = pygame.Surface((popup_w, popup_h), pygame.SRCALPHA)
        popup_surf.fill((15, 15, 35, 240))
        screen.blit(popup_surf, (popup_x, popup_y))
        pygame.draw.rect(screen, settings.CYAN, (popup_x, popup_y, popup_w, popup_h), 1, border_radius=6)

        level = skill_tree.get_level(skill["id"])
        cost = skill_tree.get_upgrade_cost(self.hovered_skill)
        can_afford = skill_tree.skill_points >= cost

        draw_text(screen, t(skill["name"]), (popup_x + popup_w // 2, popup_y + 15), settings.WHITE, 15)
        desc_text = t(skill["desc"]).replace("\n", "  ")
        draw_text(screen, desc_text, (popup_x + popup_w // 2, popup_y + 38), settings.GRAY, 11)
        cost_color = settings.GOLD if can_afford else settings.RED
        line = f"Lv.{level}  |  Custo: {cost} SP"
        if can_afford:
            line += "  [Clique para upar]"
        draw_text(screen, line, (popup_x + popup_w // 2, popup_y + 62), cost_color, 11)
        if level == 0 and not can_afford:
            draw_text(screen, "Faltam SP para desbloquear", (popup_x + popup_w // 2, popup_y + 80), settings.RED, 10)

    def _draw_inventory(self, screen):
        player = self.game.player
        content_x = settings.WINDOW_WIDTH // 2 + 20
        item_w = (settings.WINDOW_WIDTH // 2 - 60) // 2
        item_h = 65

        draw_text(screen, "INVENTORY", (content_x + 10, 55), settings.WHITE, 22, center=False)

        if not player.inventory:
            draw_text(screen, "Empty", (content_x + 10, 90), settings.GRAY, 16, center=False)
            return

        sy = int(self.scroll_y)
        for i, item in enumerate(player.inventory):
            col = i % 2
            row = i // 2
            ix = content_x + 10 + col * (item_w + 10)
            iy = 80 + row * (item_h + 5) - sy

            if iy < 45 or iy > settings.WINDOW_HEIGHT:
                continue

            item_data = settings.CONSUMABLE_DATA.get(item["id"], {})
            color = item_data.get("color", settings.GRAY)

            item_rect = pygame.Rect(ix, iy, item_w, item_h)
            pygame.draw.rect(screen, (25, 25, 45), item_rect, border_radius=6)
            pygame.draw.rect(screen, color, item_rect, 1, border_radius=6)

            name = item_data.get("name", item["id"])
            count = item.get("count", 0)
            draw_text(screen, name, (ix + 10, iy + 8), color, 14, center=False)
            draw_text(screen, f"x{count}", (ix + item_w - 30, iy + 8), settings.WHITE, 13, center=False)

            use_rect = pygame.Rect(ix + item_w - 50, iy + 30, 45, 20)
            pygame.draw.rect(screen, (40, 100, 40), use_rect, border_radius=3)
            draw_text(screen, "Usar", (use_rect.centerx, use_rect.centery), settings.WHITE, 11)

            if self.hovered_item == item["id"]:
                desc = item_data.get("desc", "")
                draw_text(screen, desc, (ix + 10, iy + 48), settings.GRAY, 11, center=False)

    def _draw_equipment(self, screen):
        player = self.game.player
        content_x = settings.WINDOW_WIDTH // 2 + 20
        content_w = settings.WINDOW_WIDTH // 2 - 40

        draw_text(screen, "EQUIPMENT", (content_x + 10, 55), settings.WHITE, 22, center=False)

        sy = int(self.scroll_y)

        for slot_name, y_off in [("weapon", 0), ("shield", 90)]:
            slot_y = 80 + y_off - sy
            slot_w = content_w - 20
            slot_h = 70

            slot_rect = pygame.Rect(content_x + 10, slot_y, slot_w, slot_h)
            bg = (30, 30, 55) if self.hovered_equip_slot != slot_name else (35, 35, 65)
            pygame.draw.rect(screen, bg, slot_rect, border_radius=8)

            is_weapon = slot_name == "weapon"
            data_source = settings.EQUIPMENT_DATA["weapons"] if is_weapon else settings.EQUIPMENT_DATA["shields"]
            equipped_id = player.equipment.get(slot_name)
            item_data = data_source.get(equipped_id, {})

            border_color = settings.ORANGE if is_weapon else settings.BLUE
            pygame.draw.rect(screen, border_color, slot_rect, 2, border_radius=8)

            slot_label = "WEAPON" if is_weapon else "SHIELD"
            draw_text(screen, slot_label, (content_x + 20, slot_y + 5), border_color, 13, center=False)

            name = item_data.get("name", "Empty")
            draw_text(screen, name, (content_x + 20, slot_y + 22), settings.WHITE, 17, center=False)

            if is_weapon:
                mult = item_data.get("multiplier", 1.0)
                draw_text(screen, f"x{mult:.1f} ATK", (content_x + 20, slot_y + 42), settings.RED, 13, center=False)
                effect = item_data.get("effect")
                if effect:
                    draw_text(screen, f"Effect: {effect}", (content_x + 140, slot_y + 42), settings.YELLOW, 12, center=False)
            else:
                defense = item_data.get("defense", 0)
                draw_text(screen, f"+{defense} DEF", (content_x + 20, slot_y + 42), settings.BLUE, 13, center=False)
                effect = item_data.get("effect")
                if effect:
                    draw_text(screen, f"Effect: {effect}", (content_x + 140, slot_y + 42), settings.YELLOW, 12, center=False)

    def _draw_bar(self, screen, x, y, w, h, pct, fill_color, bg_color):
        pygame.draw.rect(screen, bg_color, (x, y, w, h))
        if pct > 0:
            pygame.draw.rect(screen, fill_color, (x, y, int(w * pct), h))
        pygame.draw.rect(screen, settings.LIGHT_GRAY, (x, y, w, h), 1)