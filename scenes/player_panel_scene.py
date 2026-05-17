import pygame
import math
import random

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
TAB_SUBTITLES = [
    "OPERATORS // INCREMENTAL NODES",
    "THEOREMS // ACTIVE DECK",
    "CONSUMABLES // FORMULA SET",
    "LOADOUT // EQUIPPED GEAR",
]
TAB_COLORS = [settings.ORANGE, settings.GOLD, settings.GREEN, settings.PURPLE]

MATH_EXPRESSIONS = [
    "f'(x) = dy/dx", "lim x->inf", "sum_i=1^n x_i",
    "E = mc^2", "integral f(x)dx", "x^2 + y^2 = r^2",
    "det(A) = ad - bc", "e^(i*pi) + 1 = 0", "a^2 + b^2 = c^2",
    "y = mx + b", "dx/dt = r*x", "delta = b^2 - 4ac",
    "||v|| = sqrt(x^2+y^2)", "A x = lambda x", "Q.E.D.",
]


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
        self.animation_time = 0.0
        self.bg_particles = []
        for _ in range(12):
            self.bg_particles.append({
                "pos": [random.randint(20, settings.WINDOW_WIDTH - 120), random.randint(50, settings.WINDOW_HEIGHT - 50)],
                "text": random.choice(MATH_EXPRESSIONS),
                "speed": random.uniform(8, 20),
                "scale": random.uniform(12, 18),
                "alpha": random.randint(30, 80),
            })

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
        tab_y = 8
        tab_h = 38
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
            content_w = settings.WINDOW_WIDTH // 2 - 40
            equip_area_y = 80 - int(self.scroll_y)
            slot_w = content_w - 20
            slot_h = 75
            for slot_name, y_off in [("weapon", 0), ("shield", 90)]:
                slot_rect = pygame.Rect(content_x + 10, equip_area_y + y_off, slot_w, slot_h)
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
        self.animation_time += dt
        for p in self.bg_particles:
            p["pos"][1] -= p["speed"] * dt
            if p["pos"][1] < -20:
                p["pos"][1] = settings.WINDOW_HEIGHT + 20
                p["pos"][0] = random.randint(20, settings.WINDOW_WIDTH - 120)
                p["alpha"] = random.randint(30, 80)
                p["text"] = random.choice(MATH_EXPRESSIONS)

    def draw(self, screen):
        overlay = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((6, 6, 18, 238))

        for x in range(0, settings.WINDOW_WIDTH, 40):
            pygame.draw.line(overlay, (20, 45, 90, 25), (x, 0), (x, settings.WINDOW_HEIGHT), 1)
        for y in range(0, settings.WINDOW_HEIGHT, 40):
            pygame.draw.line(overlay, (20, 45, 90, 25), (0, y), (settings.WINDOW_WIDTH, y), 1)

        center_x = settings.WINDOW_WIDTH // 2
        center_y = settings.WINDOW_HEIGHT // 2
        pygame.draw.line(overlay, (30, 60, 120, 50), (center_x, 0), (center_x, settings.WINDOW_HEIGHT), 2)
        pygame.draw.line(overlay, (30, 60, 120, 50), (0, center_y), (settings.WINDOW_WIDTH, center_y), 2)

        sine_pts = []
        cosine_pts = []
        for sx in range(0, settings.WINDOW_WIDTH, 8):
            y_sin = center_y + int(60 * math.sin(sx * 0.005 + self.animation_time * 1.1))
            y_cos = center_y + int(40 * math.cos(sx * 0.008 - self.animation_time * 0.7))
            sine_pts.append((sx, y_sin))
            cosine_pts.append((sx, y_cos))
        if len(sine_pts) > 1:
            pygame.draw.lines(overlay, (0, 180, 255, 20), False, sine_pts, 1)
        if len(cosine_pts) > 1:
            pygame.draw.lines(overlay, (180, 0, 255, 18), False, cosine_pts, 1)

        for p in self.bg_particles:
            font_size = max(11, int(p["scale"] * settings.UI_SCALE))
            font = pygame.font.Font(None, font_size)
            text_surf = font.render(p["text"], True, (50, 110, 210))
            text_surf.set_alpha(p["alpha"])
            overlay.blit(text_surf, p["pos"])

        scanner_y = int((self.animation_time * 80) % settings.WINDOW_HEIGHT)
        pygame.draw.line(overlay, (0, 200, 255, 25), (0, scanner_y), (settings.WINDOW_WIDTH, scanner_y), 2)

        screen.blit(overlay, (0, 0))

        self._draw_tabs(screen)
        self._draw_left_panel(screen)

        content_x = settings.WINDOW_WIDTH // 2 + 10
        content_w = settings.WINDOW_WIDTH // 2 - 20
        content_rect = pygame.Rect(content_x, 46, content_w, settings.WINDOW_HEIGHT - 60)

        glass_panel = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(glass_panel, (10, 11, 26, 215), content_rect, border_radius=10)
        tab_color = TAB_COLORS[self.active_tab]
        pygame.draw.rect(glass_panel, (tab_color[0], tab_color[1], tab_color[2], 60), content_rect, 1, border_radius=10)
        screen.blit(glass_panel, (0, 0))

        content_clip = pygame.Rect(content_x + 4, 55, content_w - 8, settings.WINDOW_HEIGHT - 125)
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

        self._draw_bottom_stats(screen)
        pulse_alpha = int(128 + 127 * math.sin(self.animation_time * 4))
        esc_font = pygame.font.Font(None, 13)
        esc_text = esc_font.render("// PRESS [ESC] OR [TAB] TO CLOSE", True, (120, 130, 150))
        esc_text.set_alpha(pulse_alpha)
        screen.blit(esc_text, (settings.WINDOW_WIDTH // 2 - esc_text.get_width() // 2, settings.WINDOW_HEIGHT - 22))

    def _draw_tabs(self, screen):
        tab_y = 8
        tab_h = 38
        tab_w = settings.WINDOW_WIDTH // 4

        tab_surf = pygame.Surface((settings.WINDOW_WIDTH, tab_h + 4), pygame.SRCALPHA)

        for i in range(4):
            is_active = (i == self.active_tab)
            color = TAB_COLORS[i]

            x_start = i * tab_w
            x_end = (i + 1) * tab_w

            pts = [
                (x_start + 10, 0),
                (x_end - 10, 0),
                (x_end - 2, tab_h),
                (x_start + 2, tab_h),
            ]

            bg_color = (color[0], color[1], color[2], 50) if is_active else (10, 11, 24, 210)
            pygame.draw.polygon(tab_surf, bg_color, pts)

            border_color = color if is_active else (40, 45, 70, 160)
            pygame.draw.polygon(tab_surf, border_color, pts, 2 if is_active else 1)

            if is_active:
                pygame.draw.polygon(tab_surf, color, [
                    (x_start + 16, tab_h - 4),
                    (x_end - 16, tab_h - 4),
                    (x_end - 13, tab_h + 1),
                    (x_start + 13, tab_h + 1),
                ])

            label_font = pygame.font.Font(None, int(16 * settings.UI_SCALE))
            label = label_font.render(TAB_LABELS[i], True, color if is_active else (110, 110, 130))
            tab_surf.blit(label, (x_start + tab_w // 2 - label.get_width() // 2, 4))

            sub_font = pygame.font.Font(None, int(10 * settings.UI_SCALE))
            sub = sub_font.render(TAB_SUBTITLES[i], True,
                                  (color[0] // 2 + 50, color[1] // 2 + 50, color[2] // 2 + 50) if is_active else (70, 70, 85))
            tab_surf.blit(sub, (x_start + tab_w // 2 - sub.get_width() // 2, 21))

        screen.blit(tab_surf, (0, tab_y))

    def _draw_left_panel(self, screen):
        panel_w = settings.WINDOW_WIDTH // 2
        panel_h = settings.WINDOW_HEIGHT - 50
        panel_y = 50

        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (12, 12, 28, 220), (0, 0, panel_w, panel_h), border_radius=10)
        screen.blit(panel_surf, (0, panel_y))

        player = self.game.player
        lx = 25
        bar_w = panel_w - 50
        bar_h = 14
        content_right = panel_w - 25

        y = panel_y + 16

        sprite = player.get_current_sprite()
        sprite_size = 100
        center_x = panel_w // 2
        cy = y + sprite_size // 2

        time_val = self.animation_time

        r1 = sprite_size // 2 + 8
        pygame.draw.circle(screen, (0, 80, 80, 70), (center_x, cy), r1, 1)
        for d_idx in range(3):
            ang = time_val * 1.5 + d_idx * (2 * math.pi / 3)
            dx = int(center_x + r1 * math.cos(ang))
            dy = int(cy + r1 * math.sin(ang))
            pygame.draw.circle(screen, settings.CYAN, (dx, dy), 3)

        r2 = sprite_size // 2 + 16
        pygame.draw.circle(screen, (80, 60, 0, 70), (center_x, cy), r2, 1)
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
        y += sprite_size + 12

        name_card = pygame.Rect(center_x - 55, y, 110, 22)
        pygame.draw.rect(screen, (25, 35, 55, 200), name_card, border_radius=10)
        pygame.draw.rect(screen, settings.GOLD, name_card, 1, border_radius=10)
        draw_text(screen, f"Lv.{player.level}", (center_x, y + 11), settings.GOLD, 14)
        y += 30

        pygame.draw.line(screen, (40, 40, 60), (lx, y), (content_right, y), 1)
        y += 10

        hp_pct = max(0, player.hp / player.get_max_hp()) if player.get_max_hp() > 0 else 0
        self._draw_bar(screen, lx, y, bar_w, bar_h, hp_pct, settings.RED, (60, 20, 20))
        draw_text(screen, f"HP {player.hp}/{player.get_max_hp()}",
                 (lx + 8, y + 1), settings.WHITE, 11, center=False)
        y += bar_h + 6

        xp_pct = player.exp / player.next_level_exp if player.next_level_exp > 0 else 0
        self._draw_bar(screen, lx, y, bar_w, bar_h, xp_pct, settings.GOLD, (40, 40, 10))
        draw_text(screen, f"XP {player.exp}/{player.next_level_exp}",
                 (lx + 8, y + 1), settings.WHITE, 11, center=False)
        y += bar_h + 12

        col_w = (bar_w - 16) // 2
        badge_h = 22

        stats_data = [
            [(f"ATK: {player.get_attack_damage()}", settings.RED, (35, 12, 12)),
             (f"DEF: {player.get_defense()}", settings.BLUE, (12, 12, 35))],
            [(f"RNG: {player.get_move_range()}", settings.CYAN, (12, 35, 35)),
             (f"GLD: {player.gold}", settings.GOLD, (35, 35, 12))],
        ]
        for row in stats_data:
            for j, (text, text_color, bg) in enumerate(row):
                bx = lx + j * (col_w + 16)
                self._draw_pill_badge(screen, bx, y, col_w, badge_h, text, text_color, bg)
            y += badge_h + 6

        sp = self.game.skill_tree.skill_points if self.game.skill_tree else 0
        tickets = getattr(player, "upgrade_tickets", 0)
        self._draw_pill_badge(screen, lx, y, col_w, badge_h, f"SP: {sp}", settings.PURPLE, (20, 12, 35))
        self._draw_pill_badge(screen, lx + col_w + 16, y, col_w, badge_h, f"TKT: {tickets}", settings.GOLD, (35, 25, 12))
        y += badge_h + 12

        pygame.draw.line(screen, (40, 40, 60), (lx, y), (content_right, y), 1)

    def _draw_pill_badge(self, screen, x, y, w, h, text, text_color, bg_tint):
        badge_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(badge_surf, (*bg_tint, 200), (0, 0, w, h), border_radius=int(h // 2))
        pygame.draw.rect(badge_surf, text_color, (0, 0, w, h), 1, border_radius=int(h // 2))
        screen.blit(badge_surf, (x, y))
        draw_text(screen, text, (x + w // 2, y + h // 2), text_color, 12)

    def _draw_row_brackets(self, screen, rect, color):
        bw, bh = 6, 6
        pygame.draw.line(screen, color, (rect.left - 1, rect.top - 1), (rect.left + bw, rect.top - 1), 2)
        pygame.draw.line(screen, color, (rect.left - 1, rect.top - 1), (rect.left - 1, rect.top + bh), 2)
        pygame.draw.line(screen, color, (rect.right + 1, rect.top - 1), (rect.right - bw, rect.top - 1), 2)
        pygame.draw.line(screen, color, (rect.right + 1, rect.top - 1), (rect.right + 1, rect.top + bh), 2)
        pygame.draw.line(screen, color, (rect.left - 1, rect.bottom + 1), (rect.left + bw, rect.bottom + 1), 2)
        pygame.draw.line(screen, color, (rect.left - 1, rect.bottom + 1), (rect.left - 1, rect.bottom - bh), 2)
        pygame.draw.line(screen, color, (rect.right + 1, rect.bottom + 1), (rect.right - bw, rect.bottom + 1), 2)
        pygame.draw.line(screen, color, (rect.right + 1, rect.bottom + 1), (rect.right + 1, rect.bottom - bh), 2)

    def _draw_neon_scrollbar(self, screen, content_x, content_y, content_h, visible_h, total_h, color):
        if total_h <= visible_h:
            return
        sb_x = content_x + content_h - 6
        sb_y = content_y
        sb_h = visible_h
        sb_w = 4
        pygame.draw.rect(screen, (20, 22, 45, 150), (sb_x, sb_y, sb_w, sb_h), border_radius=2)
        visible_ratio = visible_h / total_h
        thumb_h = max(16, int(sb_h * visible_ratio))
        scroll_ratio = self.scroll_y / (total_h - visible_h) if total_h > visible_h else 0
        thumb_y = sb_y + int((sb_h - thumb_h) * scroll_ratio)
        pygame.draw.rect(screen, color, (sb_x - 1, thumb_y, sb_w + 2, thumb_h), border_radius=3)
        glow = pygame.Surface((sb_w + 4, thumb_h + 2), pygame.SRCALPHA)
        pygame.draw.rect(glow, (color[0], color[1], color[2], 80), (0, 0, sb_w + 4, thumb_h + 2), 1, border_radius=4)
        screen.blit(glow, (sb_x - 2, thumb_y - 1))

    def _draw_upgrades(self, screen):
        player = self.game.player
        content_x = settings.WINDOW_WIDTH // 2 + 20
        content_w = settings.WINDOW_WIDTH // 2 - 40

        tab_color = TAB_COLORS[TAB_UPGRADES]
        draw_text(screen, "UPGRADES", (content_x + 10, 55), settings.WHITE, 20, center=False)
        tickets = getattr(player, "upgrade_tickets", 0)
        if tickets > 0:
            draw_text(screen, f"Tickets: {tickets}", (content_x + content_w - 120, 55), settings.GOLD, 13, center=False)

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

            row_rect = pygame.Rect(content_x + 5, row_y + 2, content_w - 10, 70)
            row_surf = pygame.Surface((row_rect.width, row_rect.height), pygame.SRCALPHA)
            bg_color = (color[0] // 6, color[1] // 6, color[2] // 6, 200) if self.hovered_upgrade == utype else ((18, 19, 40, 190) if i % 2 == 0 else (14, 15, 33, 190))
            pygame.draw.rect(row_surf, bg_color, (0, 0, row_rect.width, row_rect.height), border_radius=8)
            border_col = color if self.hovered_upgrade == utype else (40, 45, 75, 120)
            pygame.draw.rect(row_surf, border_col, (0, 0, row_rect.width, row_rect.height), 2 if self.hovered_upgrade == utype else 1, border_radius=8)
            screen.blit(row_surf, row_rect)

            if self.hovered_upgrade == utype:
                self._draw_row_brackets(screen, row_rect, color)

            draw_text(screen, f"{name}", (content_x + 20, row_y + 8), color, 16, center=False)
            draw_text(screen, f"Lv.{level}", (content_x + 90, row_y + 8), settings.WHITE, 14, center=False)
            draw_text(screen, desc, (content_x + 20, row_y + 28), settings.GRAY, 11, center=False)

            bonus_map = {"atk": 3 * level, "def": 2 * level, "hp": 15 * level, "range": level}
            draw_text(screen, f"+{bonus_map[utype]}", (content_x + 20, row_y + 44), settings.GOLD, 12, center=False)

            if tickets > 0:
                buy_color = settings.GREEN
                buy_text_color = settings.BLACK
                button_label = "FREE"
            else:
                buy_color = settings.GREEN if can_afford else settings.DARK_GRAY
                buy_text_color = settings.BLACK if can_afford else settings.GRAY
                button_label = f"{cost}g"

            buy_rect = pygame.Rect(content_x + content_w - 80, row_y + 30, 70, 26)
            pygame.draw.rect(screen, buy_color, buy_rect, border_radius=4)
            draw_text(screen, button_label, (buy_rect.centerx, buy_rect.centery + 1), buy_text_color, 13)

        total_h = len(upgrade_info) * 80
        visible_h = settings.WINDOW_HEIGHT - 130
        self._draw_neon_scrollbar(screen, content_x, 80, content_w, visible_h, total_h, tab_color)

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

        draw_text(screen, "SKILLS", (content_x + 10, 55), settings.GOLD, 20, center=False)
        draw_text(screen, f"Points: {skill_tree.skill_points}", (content_x + content_w - 80, 55), settings.GOLD, 13, center=False)

        for skill in skill_tree.skills.values():
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

                    if is_prereq_unlocked:
                        progress = (self.animation_time * 0.8) % 1.0
                        dot_x = int(px + (nx - px) * progress)
                        dot_y = int(py + (ny - py) * progress)
                        pygame.draw.circle(screen, settings.GOLD, (dot_x, dot_y), 4)
                        pygame.draw.circle(screen, settings.WHITE, (dot_x, dot_y), 2)

        for skill in skill_tree.skills.values():
            sx = offset_x + int(skill["x"] * scale) - node_w // 2
            sy = offset_y + int(skill["y"] * scale) - node_h // 2
            level = skill_tree.get_level(skill["id"])
            unlocked = level > 0
            can_unlock = skill_tree.can_unlock(skill["id"])

            node_rect = pygame.Rect(sx, sy, node_w, node_h)

            if unlocked:
                bg = skill.get("color", settings.CYAN)
                glow_alpha = int(30 + 20 * math.sin(self.animation_time * 2))
                for g in range(3, 0, -1):
                    gs = pygame.Surface((node_w + g * 6, node_h + g * 6), pygame.SRCALPHA)
                    pygame.draw.rect(gs, (*bg, glow_alpha // g), (0, 0, gs.get_width(), gs.get_height()), border_radius=6 + g)
                    screen.blit(gs, (sx - g * 3, sy - g * 3))
                bg_dark = (bg[0] // 3, bg[1] // 3, bg[2] // 3)
                pygame.draw.rect(screen, bg_dark, node_rect, border_radius=6)
                pygame.draw.rect(screen, bg, node_rect, 2, border_radius=6)
            elif can_unlock:
                pygame.draw.rect(screen, (30, 30, 50), node_rect, border_radius=6)
                pygame.draw.rect(screen, settings.GRAY, node_rect, 1, border_radius=6)
            else:
                pygame.draw.rect(screen, (15, 15, 25), node_rect, border_radius=6)
                pygame.draw.rect(screen, (40, 40, 50), node_rect, 1, border_radius=6)

            font = pygame.font.Font(None, int(12 * settings.UI_SCALE))
            label = font.render(t(skill["name"])[:12], True,
                                settings.WHITE if unlocked else settings.GRAY)
            screen.blit(label, (node_rect.centerx - label.get_width() // 2,
                                 node_rect.centery - int(6 * settings.UI_SCALE)))
            lv_text = pygame.font.Font(None, int(10 * settings.UI_SCALE)).render(f"Lv.{level}", True, settings.GOLD if unlocked else settings.DARK_GRAY)
            screen.blit(lv_text, (node_rect.centerx - lv_text.get_width() // 2,
                                    node_rect.centery + int(3 * settings.UI_SCALE)))

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

        tab_color = TAB_COLORS[TAB_INVENTORY]
        draw_text(screen, "INVENTORY", (content_x + 10, 55), settings.WHITE, 20, center=False)

        if not player.inventory:
            draw_text(screen, "Empty", (content_x + 10, 90), settings.GRAY, 16, center=False)
            return

        sy = int(self.scroll_y)
        for i, item in enumerate(player.inventory):
            col = i % 2
            row = i // 2
            ix = content_x + 10 + col * (item_w + 10)
            iy = 80 + row * (item_h + 8) - sy

            if iy < 45 or iy > settings.WINDOW_HEIGHT:
                continue

            item_data = settings.CONSUMABLE_DATA.get(item["id"], {})
            color = item_data.get("color", settings.GRAY)

            item_rect = pygame.Rect(ix, iy, item_w, item_h)
            card_surf = pygame.Surface((item_rect.width, item_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(card_surf, (18, 19, 40, 210), (0, 0, item_rect.width, item_rect.height), border_radius=8)
            border_col = color if self.hovered_item == item["id"] else (40, 45, 75, 120)
            pygame.draw.rect(card_surf, border_col, (0, 0, item_rect.width, item_rect.height), 2 if self.hovered_item == item["id"] else 1, border_radius=8)
            screen.blit(card_surf, item_rect)

            pygame.draw.rect(screen, color, (ix, iy + 5, 3, item_h - 10), border_radius=1)

            name = t(item_data.get("name", item["id"]))
            count = item.get("count", 0)
            draw_text(screen, name, (ix + 12, iy + 8), color, 13, center=False)
            draw_text(screen, f"x{count}", (ix + item_w - 25, iy + 8), settings.WHITE, 12, center=False)

            use_rect = pygame.Rect(ix + item_w - 50, iy + 30, 44, 20)
            use_col = (25, 80, 35, 210) if self.hovered_item == item["id"] else (20, 55, 25, 180)
            use_surf = pygame.Surface((44, 20), pygame.SRCALPHA)
            pygame.draw.rect(use_surf, use_col, (0, 0, 44, 20), border_radius=4)
            screen.blit(use_surf, use_rect)
            draw_text(screen, t("inv_use_button"), (use_rect.centerx, use_rect.centery + 1), settings.WHITE, 10)

            if self.hovered_item == item["id"]:
                desc = t(item_data.get("desc", ""))
                draw_text(screen, desc, (ix + 12, iy + 48), settings.GRAY, 10, center=False)

        total_h = max(1, (len(player.inventory) + 1) // 2) * (item_h + 8)
        visible_h = settings.WINDOW_HEIGHT - 130
        self._draw_neon_scrollbar(screen, content_x, 80, settings.WINDOW_WIDTH // 2 - 40, visible_h, total_h, tab_color)

    def _draw_equipment(self, screen):
        player = self.game.player
        content_x = settings.WINDOW_WIDTH // 2 + 20
        content_w = settings.WINDOW_WIDTH // 2 - 40

        draw_text(screen, "EQUIPMENT", (content_x + 10, 55), settings.WHITE, 20, center=False)

        sy = int(self.scroll_y)

        for slot_name, y_off in [("weapon", 0), ("shield", 90)]:
            slot_y = 80 + y_off - sy
            slot_w = content_w - 20
            slot_h = 75

            is_weapon = slot_name == "weapon"
            data_source = settings.EQUIPMENT_DATA["weapons"] if is_weapon else settings.EQUIPMENT_DATA["shields"]
            equipped_id = player.equipment.get(slot_name)
            item_data = data_source.get(equipped_id, {})
            border_color = settings.ORANGE if is_weapon else settings.BLUE

            slot_rect = pygame.Rect(content_x + 10, slot_y, slot_w, slot_h)
            slot_surf = pygame.Surface((slot_w, slot_h), pygame.SRCALPHA)
            is_hovered = self.hovered_equip_slot == slot_name
            bg = (border_color[0] // 6, border_color[1] // 6, border_color[2] // 6, 200) if is_hovered else (16, 17, 38, 210)
            pygame.draw.rect(slot_surf, bg, (0, 0, slot_w, slot_h), border_radius=10)
            border = border_color if is_hovered else (40, 45, 75, 120)
            pygame.draw.rect(slot_surf, border, (0, 0, slot_w, slot_h), 2 if is_hovered else 1, border_radius=10)
            screen.blit(slot_surf, slot_rect)

            pygame.draw.rect(screen, border_color, (content_x + 10, slot_y + 10, 3, slot_h - 20), border_radius=1)

            if is_hovered:
                self._draw_row_brackets(screen, slot_rect, border_color)

            slot_label = "WEAPON" if is_weapon else "SHIELD"
            draw_text(screen, slot_label, (content_x + 22, slot_y + 6), border_color, 12, center=False)

            name = t(item_data.get("name", "eq_empty_slot"))
            draw_text(screen, name, (content_x + 22, slot_y + 22), settings.WHITE, 16, center=False)

            if is_weapon:
                mult = item_data.get("multiplier", 1.0)
                draw_text(screen, f"x{mult:.1f} ATK", (content_x + 22, slot_y + 42), settings.RED, 12, center=False)
                effect = item_data.get("effect")
                if effect:
                    draw_text(screen, f"Effect: {effect}", (content_x + 140, slot_y + 42), settings.YELLOW, 11, center=False)
            else:
                defense = item_data.get("defense", 0)
                draw_text(screen, f"+{defense} DEF", (content_x + 22, slot_y + 42), settings.BLUE, 12, center=False)
                effect = item_data.get("effect")
                if effect:
                    draw_text(screen, f"Effect: {effect}", (content_x + 140, slot_y + 42), settings.YELLOW, 11, center=False)

    def _draw_bottom_stats(self, screen):
        sp = self.game.skill_tree.skill_points if self.game.skill_tree else 0
        gold = self.game.player.gold
        y = settings.WINDOW_HEIGHT - 46

        gold_surf = pygame.Surface((110, 26), pygame.SRCALPHA)
        pygame.draw.rect(gold_surf, (20, 20, 10, 180), (0, 0, 110, 26), border_radius=13)
        pygame.draw.rect(gold_surf, settings.GOLD, (0, 0, 110, 26), 1, border_radius=13)
        screen.blit(gold_surf, (20, y))
        draw_text(screen, f"G {gold}", (75, y + 10), settings.GOLD, 14)

        sp_surf = pygame.Surface((90, 26), pygame.SRCALPHA)
        pygame.draw.rect(sp_surf, (10, 20, 20, 180), (0, 0, 90, 26), border_radius=13)
        pygame.draw.rect(sp_surf, settings.CYAN, (0, 0, 90, 26), 1, border_radius=13)
        screen.blit(sp_surf, (140, y))
        draw_text(screen, f"SP {sp}", (185, y + 10), settings.CYAN, 14)

    def _draw_bar(self, screen, x, y, w, h, pct, fill_color, bg_color):
        pygame.draw.rect(screen, bg_color, (x, y, w, h))
        if pct > 0:
            pygame.draw.rect(screen, fill_color, (x, y, int(w * pct), h))
        pygame.draw.rect(screen, settings.LIGHT_GRAY, (x, y, w, h), 1)