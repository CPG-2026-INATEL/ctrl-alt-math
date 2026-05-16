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
            if event.key == pygame.K_1:
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
        scale = min(content_w / 600, content_h / 500)
        origin_x = content_x + 20
        origin_y = 80 - int(self.scroll_y)

        for skill in skill_tree.skills.values():
            sx = origin_x + int(skill["x"] * scale * 0.4) - 40
            sy = origin_y + int(skill["y"] * scale * 0.4) - 20
            node_rect = pygame.Rect(sx, sy, 80, 40)
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
                scale = min(content_w / 600, content_h / 500)
                origin_x = settings.WINDOW_WIDTH // 2 + 20 + 20
                origin_y = 80 - int(self.scroll_y)
                for skill in skill_tree.skills.values():
                    sx = origin_x + int(skill["x"] * scale * 0.4) - 40
                    sy = origin_y + int(skill["y"] * scale * 0.4) - 20
                    node_rect = pygame.Rect(sx, sy, 80, 40)
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
            bg_color = (30, 30, 60) if i == self.active_tab else (15, 15, 35)
            pygame.draw.rect(screen, bg_color, tab_rect, border_radius=4)
            border_color = TAB_COLORS[i] if i == self.active_tab else (60, 60, 80)
            pygame.draw.rect(screen, border_color, tab_rect, 2, border_radius=4)
            label_font = pygame.font.Font(None, 16)
            label = label_font.render(TAB_LABELS[i], True,
                                      TAB_COLORS[i] if i == self.active_tab else (120, 120, 140))
            screen.blit(label, (tab_rect.centerx - label.get_width() // 2,
                                tab_rect.centery - label.get_height() // 2))

    def _draw_left_panel(self, screen):
        panel_w = settings.WINDOW_WIDTH // 2
        panel_h = settings.WINDOW_HEIGHT - 50
        panel_y = 50

        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((15, 15, 35, 200))
        screen.blit(panel_surf, (0, panel_y))

        player = self.game.player
        lx = 20
        bar_w = panel_w - 40
        bar_h = 14
        content_x = lx
        content_right = panel_w - 20

        y = panel_y + 20

        sprite = player.get_current_sprite()
        sprite_size = 120
        center_x = panel_w // 2

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
        y += sprite_size + 12

        draw_text(screen, f"Lv.{player.level}", (center_x, y), settings.GOLD, 20)
        y += 30

        pygame.draw.line(screen, (50, 50, 70), (lx, y), (content_right, y), 1)
        y += 12

        hp_pct = max(0, player.hp / player.get_max_hp()) if player.get_max_hp() > 0 else 0
        self._draw_bar(screen, lx, y, bar_w, bar_h, hp_pct, settings.RED, (60, 20, 20))
        draw_text(screen, f"HP {player.hp}/{player.get_max_hp()}",
                 (lx + 4, y + 1), settings.WHITE, 12, center=False)
        y += bar_h + 8

        xp_pct = player.exp / player.next_level_exp if player.next_level_exp > 0 else 0
        self._draw_bar(screen, lx, y, bar_w, bar_h, xp_pct, settings.GOLD, (40, 40, 10))
        draw_text(screen, f"XP {player.exp}/{player.next_level_exp}",
                 (lx + 4, y + 1), settings.WHITE, 12, center=False)
        y += bar_h + 16

        col_w = (bar_w - 20) // 2
        draw_text(screen, f"ATK: {player.get_attack_damage()}", (lx, y), settings.RED, 16, center=False)
        draw_text(screen, f"DEF: {player.get_defense()}", (lx + col_w, y), settings.BLUE, 16, center=False)
        y += 22
        draw_text(screen, f"Range: {player.get_move_range()}", (lx, y), settings.CYAN, 16, center=False)
        draw_text(screen, f"Gold: {player.gold}", (lx + col_w, y), settings.GOLD, 16, center=False)
        y += 22

        sp = self.game.skill_tree.skill_points if self.game.skill_tree else 0
        draw_text(screen, f"SP: {sp}", (lx, y), settings.CYAN, 16, center=False)
        tickets = getattr(player, "upgrade_tickets", 0)
        draw_text(screen, f"Tickets: {tickets}", (lx + col_w, y), settings.GOLD, 16, center=False)
        y += 24

        pygame.draw.line(screen, (50, 50, 70), (lx, y), (content_right, y), 1)

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

            tickets = getattr(player, "upgrade_tickets", 0)
            if tickets > 0:
                buy_color = settings.GOLD
                buy_text_color = settings.BLACK
                button_label = "FREE"
            else:
                buy_color = settings.GREEN if can_afford else settings.DARK_GRAY
                buy_text_color = settings.WHITE if can_afford else settings.GRAY
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

        scale = min(content_w / 600, content_h / 500)
        origin_x = content_x + 20
        origin_y = 80 - int(self.scroll_y)

        draw_text(screen, "SKILLS", (content_x + 10, 55), settings.GOLD, 22, center=False)
        draw_text(screen, f"Points: {skill_tree.skill_points}", (content_x + content_w - 80, 55), settings.GOLD, 14, center=False)

        for skill in skill_tree.skills.values():
            sx = origin_x + int(skill["x"] * scale * 0.4) - 40
            sy = origin_y + int(skill["y"] * scale * 0.4) - 20
            level = skill_tree.get_level(skill["id"])
            unlocked = level > 0
            can_unlock = skill_tree.can_unlock(skill["id"])

            node_rect = pygame.Rect(sx, sy, 80, 40)
            if unlocked:
                bg = skill.get("color", settings.CYAN)
                bg_dark = (bg[0] // 3, bg[1] // 3, bg[2] // 3)
                pygame.draw.rect(screen, bg_dark, node_rect, border_radius=6)
                pygame.draw.rect(screen, bg, node_rect, 2, border_radius=6)
            elif can_unlock:
                pygame.draw.rect(screen, (30, 30, 50), node_rect, border_radius=6)
                pygame.draw.rect(screen, settings.GRAY, node_rect, 1, border_radius=6)
            else:
                pygame.draw.rect(screen, (15, 15, 25), node_rect, border_radius=6)
                pygame.draw.rect(screen, (40, 40, 50), node_rect, 1, border_radius=6)

            font = pygame.font.Font(None, 14)
            label = font.render(t(skill["name"])[:12], True,
                                settings.WHITE if unlocked else settings.GRAY)
            screen.blit(label, (node_rect.centerx - label.get_width() // 2,
                                 node_rect.centery - 8))
            lv_text = font.render(f"Lv.{level}", True, settings.GOLD if unlocked else settings.DARK_GRAY)
            screen.blit(lv_text, (node_rect.centerx - lv_text.get_width() // 2,
                                    node_rect.centery + 6))

            for prereq_id in skill.get("prereqs", []):
                prereq = skill_tree.skills.get(prereq_id)
                if prereq:
                    px = origin_x + int(prereq["x"] * scale * 0.4)
                    py = origin_y + int(prereq["y"] * scale * 0.4)
                    nx = origin_x + int(skill["x"] * scale * 0.4)
                    ny = origin_y + int(skill["y"] * scale * 0.4)
                    line_color = settings.GREEN if skill_tree.get_level(prereq_id) > 0 else (40, 40, 50)
                    pygame.draw.line(screen, line_color, (px, py), (nx, ny), 2)

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