import pygame
import math
import random

import settings
from utils import draw_text
from scenes.scene import Scene
from i18n import t

SHOP_WEAPONS = 0
SHOP_SHIELDS = 1
SHOP_CONSUMABLES = 2

SHOP_TAB_LABELS = ["shop_tab_weapons", "shop_tab_shields", "shop_tab_consumables"]
SHOP_TAB_SUBTITLES = [
    "OPERATORS // ALGEBRAIC DECK",
    "BARRIERS // GEOMETRIC WALLS",
    "FORMULAS // NUMERICAL SETS"
]
SHOP_TAB_COLORS = [settings.RED, settings.BLUE, settings.GREEN]

MATH_EXPRESSIONS = [
    "f(x) = dy/dx",
    "lim x->inf",
    "sum_i=1^n x_i",
    "E = mc^2",
    "integral f(x)dx",
    "P(A|B) = P(B|A)P(A)/P(B)",
    "x^2 + y^2 = r^2",
    "det(A) = ad - bc",
    "e^(i*pi) + 1 = 0",
    "a^2 + b^2 = c^2",
    "f'(x) = 0",
    "Q.E.D.",
    "y = mx + b",
    "dx/dt = r*x*(1 - x/K)",
    "H = -sum P(x)log P(x)",
    "delta = b^2 - 4ac",
    "||v|| = sqrt(x^2 + y^2)",
    "A x = lambda x"
]

class ShopScene(Scene):
    overlay = True

    def __init__(self, game):
        super().__init__(game)
        self.active_tab = SHOP_WEAPONS
        self.scroll_y = 0
        self.selected_item = None
        self.buy_feedback = ""
        self.buy_feedback_timer = 0
        self.buy_success = False
        
        self.hovered_item_row = None
        self.buy_button_hovered = False
        self.animation_time = 0.0
        
        # Drifting background mathematical particles
        self.bg_particles = []
        for _ in range(15):
            self.bg_particles.append({
                "pos": [random.randint(20, settings.WINDOW_WIDTH - 120), random.randint(50, settings.WINDOW_HEIGHT - 50)],
                "text": random.choice(MATH_EXPRESSIONS),
                "speed": random.uniform(10, 25),
                "scale": random.uniform(14, 20),
                "alpha": random.randint(40, 95)
            })

    def enter(self, prev_scene=None):
        self.active_tab = SHOP_WEAPONS
        self.scroll_y = 0
        self.selected_item = None
        self.buy_feedback = ""
        self.buy_feedback_timer = 0
        self.buy_success = False
        self.hovered_item_row = None
        self.buy_button_hovered = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_s, pygame.K_ESCAPE):
                self.game.sfx.play("menu_select")
                self.game.scene_manager.pop()
                return
            if event.key == pygame.K_1:
                if self.active_tab != SHOP_WEAPONS:
                    self.active_tab = SHOP_WEAPONS
                    self.scroll_y = 0
                    self.selected_item = None
                    self.game.sfx.play("menu_select")
            elif event.key == pygame.K_2:
                if self.active_tab != SHOP_SHIELDS:
                    self.active_tab = SHOP_SHIELDS
                    self.scroll_y = 0
                    self.selected_item = None
                    self.game.sfx.play("menu_select")
            elif event.key == pygame.K_3:
                if self.active_tab != SHOP_CONSUMABLES:
                    self.active_tab = SHOP_CONSUMABLES
                    self.scroll_y = 0
                    self.selected_item = None
                    self.game.sfx.play("menu_select")

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
        tab_h = 36
        tab_w = settings.WINDOW_WIDTH // 3
        for i in range(3):
            tab_rect = pygame.Rect(i * tab_w, tab_y, tab_w, tab_h)
            if tab_rect.collidepoint(mx, my):
                if self.active_tab != i:
                    self.active_tab = i
                    self.scroll_y = 0
                    self.selected_item = None
                    self.game.sfx.play("menu_select")
                return

        list_x = 20
        list_w = settings.WINDOW_WIDTH // 2 - 40
        sy = int(self.scroll_y)
        items = self._get_items()
        for i, item_data in enumerate(items):
            row_y = 95 + i * 65 - sy
            if 95 <= row_y <= 405 or 95 <= row_y + 58 <= 405:
                row_rect = pygame.Rect(list_x + 10, row_y, list_w - 20, 58)
                if row_rect.collidepoint(mx, my):
                    if self.selected_item != item_data["id"]:
                        self.selected_item = item_data["id"]
                        self.game.sfx.play("menu_confirm")
                    return

        detail_x = settings.WINDOW_WIDTH // 2 + 20
        detail_w = settings.WINDOW_WIDTH // 2 - 40
        buy_y = settings.WINDOW_HEIGHT - 85
        buy_rect = pygame.Rect(detail_x + 10, buy_y, detail_w - 20, 48)
        if buy_rect.collidepoint(mx, my) and self.selected_item:
            self._try_buy(self.selected_item)

    def _try_buy(self, item_id):
        player = self.game.player
        if self.active_tab == SHOP_WEAPONS:
            data = settings.EQUIPMENT_DATA["weapons"].get(item_id)
            if not data:
                return
            if player.equipment.get("weapon") == item_id:
                self.buy_feedback = t("shop_already_equipped")
                self.buy_feedback_timer = 1.8
                self.buy_success = False
                self.game.sfx.play("hit")
                return
            cost = data.get("cost", 0)
            sp_cost = data.get("sp_cost", 0)
            sp = self.game.skill_tree.skill_points if self.game.skill_tree else 0
            if player.gold < cost or sp < sp_cost:
                self.buy_feedback = t("shop_insufficient_funds")
                self.buy_feedback_timer = 1.8
                self.buy_success = False
                self.game.sfx.play("hit")
                return
            player.gold -= cost
            if sp_cost > 0 and self.game.skill_tree:
                self.game.skill_tree.skill_points -= sp_cost
            player.equipment["weapon"] = item_id
            self.buy_feedback = t("shop_equipped_feedback", name=t(data['name']))
            self.buy_feedback_timer = 1.8
            self.buy_success = True
            self.game.sfx.play("skill_unlock")
        elif self.active_tab == SHOP_SHIELDS:
            data = settings.EQUIPMENT_DATA["shields"].get(item_id)
            if not data:
                return
            if player.equipment.get("shield") == item_id:
                self.buy_feedback = t("shop_already_equipped")
                self.buy_feedback_timer = 1.8
                self.buy_success = False
                self.game.sfx.play("hit")
                return
            cost = data.get("cost", 0)
            sp_cost = data.get("sp_cost", 0)
            sp = self.game.skill_tree.skill_points if self.game.skill_tree else 0
            if player.gold < cost or sp < sp_cost:
                self.buy_feedback = t("shop_insufficient_funds")
                self.buy_feedback_timer = 1.8
                self.buy_success = False
                self.game.sfx.play("hit")
                return
            player.gold -= cost
            if sp_cost > 0 and self.game.skill_tree:
                self.game.skill_tree.skill_points -= sp_cost
            player.equipment["shield"] = item_id
            self.buy_feedback = t("shop_equipped_feedback", name=t(data['name']))
            self.buy_feedback_timer = 1.8
            self.buy_success = True
            self.game.sfx.play("skill_unlock")
        elif self.active_tab == SHOP_CONSUMABLES:
            data = settings.CONSUMABLE_DATA.get(item_id)
            if not data:
                return
            cost = data.get("cost", 0)
            sp_cost = data.get("sp_cost", 0)
            sp = self.game.skill_tree.skill_points if self.game.skill_tree else 0
            if player.gold < cost or sp < sp_cost:
                self.buy_feedback = t("shop_insufficient_funds")
                self.buy_feedback_timer = 1.8
                self.buy_success = False
                self.game.sfx.play("hit")
                return
            player.gold -= cost
            if sp_cost > 0 and self.game.skill_tree:
                self.game.skill_tree.skill_points -= sp_cost
            for inv_item in player.inventory:
                if inv_item["id"] == item_id:
                    inv_item["count"] = inv_item.get("count", 1) + 1
                    self.buy_feedback = t("shop_added_feedback", name=t(data['name']))
                    self.buy_feedback_timer = 1.8
                    self.buy_success = True
                    self.game.sfx.play("menu_confirm")
                    game = self.game
                    game.gold = player.gold
                    return
            player.inventory.append({"id": item_id, "count": 1})
            self.buy_feedback = t("shop_purchased_feedback", name=t(data['name']))
            self.buy_feedback_timer = 1.8
            self.buy_success = True
            self.game.sfx.play("menu_confirm")
        game = self.game
        game.gold = player.gold

    def _update_hover(self, pos):
        mx, my = pos
        
        # Left item rows hover inside bounded viewport
        list_x = 20
        list_w = settings.WINDOW_WIDTH // 2 - 40
        sy = int(self.scroll_y)
        items = self._get_items()
        
        old_hover = self.hovered_item_row
        self.hovered_item_row = None
        
        for i, item_data in enumerate(items):
            row_y = 95 + i * 65 - sy
            if 95 <= row_y <= 405 or 95 <= row_y + 58 <= 405:
                row_rect = pygame.Rect(list_x + 10, row_y, list_w - 20, 58)
                if row_rect.collidepoint(mx, my):
                    self.hovered_item_row = item_data["id"]
                    if old_hover != self.hovered_item_row:
                        self.game.sfx.play("menu_select")
                    break
                
        # Buy button hover
        detail_x = settings.WINDOW_WIDTH // 2 + 20
        detail_w = settings.WINDOW_WIDTH // 2 - 40
        buy_y = settings.WINDOW_HEIGHT - 85
        buy_rect = pygame.Rect(detail_x + 10, buy_y, detail_w - 20, 48)
        old_buy_hover = self.buy_button_hovered
        self.buy_button_hovered = buy_rect.collidepoint(mx, my) and self.selected_item is not None
        if self.buy_button_hovered and not old_buy_hover:
            self.game.sfx.play("menu_select")

    def _get_items(self):
        if self.active_tab == SHOP_WEAPONS:
            return [{"id": wid, **settings.EQUIPMENT_DATA["weapons"][wid]} for wid in settings.SHOP_ITEMS["weapons"]]
        elif self.active_tab == SHOP_SHIELDS:
            return [{"id": sid, **settings.EQUIPMENT_DATA["shields"][sid]} for sid in settings.SHOP_ITEMS["shields"]]
        else:
            return [{"id": cid, **settings.CONSUMABLE_DATA[cid]} for cid in settings.SHOP_ITEMS["consumables"]]

    def _get_max_scroll(self):
        items = self._get_items()
        total_h = len(items) * 65 + 10
        visible_h = 310  # Height of bounded item viewport
        return max(0, total_h - visible_h)

    def update(self, dt):
        self.animation_time += dt
        if self.buy_feedback_timer > 0:
            self.buy_feedback_timer -= dt
            
        # Update background mathematical drift
        for p in self.bg_particles:
            p["pos"][1] -= p["speed"] * dt
            if p["pos"][1] < -20:
                p["pos"][1] = settings.WINDOW_HEIGHT + 20
                p["pos"][0] = random.randint(20, settings.WINDOW_WIDTH - 120)
                p["alpha"] = random.randint(40, 95)
                p["text"] = random.choice(MATH_EXPRESSIONS)

    def draw(self, screen):
        # 1. Base Glassmorphic Overlay surface
        overlay = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((6, 6, 18, 238)) # Clean deep retro blue-black translucent back
        
        # 2. Draw Faint Mathematical Blueprint Grid
        for x in range(0, settings.WINDOW_WIDTH, 40):
            pygame.draw.line(overlay, (20, 45, 90, 35), (x, 0), (x, settings.WINDOW_HEIGHT), 1)
        for y in range(0, settings.WINDOW_HEIGHT, 40):
            pygame.draw.line(overlay, (20, 45, 90, 35), (0, y), (settings.WINDOW_WIDTH, y), 1)
            
        # Draw grid coordinate axes
        center_x = settings.WINDOW_WIDTH // 2
        center_y = settings.WINDOW_HEIGHT // 2
        pygame.draw.line(overlay, (30, 60, 120, 65), (center_x, 0), (center_x, settings.WINDOW_HEIGHT), 2)
        pygame.draw.line(overlay, (30, 60, 120, 65), (0, center_y), (settings.WINDOW_WIDTH, center_y), 2)
        # Minor coordinate markers
        for cx in range(0, settings.WINDOW_WIDTH, 40):
            pygame.draw.line(overlay, (50, 80, 150, 90), (cx, center_y - 4), (cx, center_y + 4), 1)
        for cy in range(0, settings.WINDOW_HEIGHT, 40):
            pygame.draw.line(overlay, (50, 80, 150, 90), (center_x - 4, cy), (center_x + 4, cy), 1)
            
        # 3. Dynamic Sine/Cosine Wave lines drifting in background
        sine_pts = []
        cosine_pts = []
        for sx in range(0, settings.WINDOW_WIDTH, 8):
            y_sin = center_y + int(70 * math.sin(sx * 0.005 + self.animation_time * 1.1))
            y_cos = center_y + int(50 * math.cos(sx * 0.008 - self.animation_time * 0.7))
            sine_pts.append((sx, y_sin))
            cosine_pts.append((sx, y_cos))
        if len(sine_pts) > 1:
            pygame.draw.lines(overlay, (0, 180, 255, 30), False, sine_pts, 1)
        if len(cosine_pts) > 1:
            pygame.draw.lines(overlay, (180, 0, 255, 25), False, cosine_pts, 1)
            
        # 4. Draw Drifting Mathematical Expression particles
        for p in self.bg_particles:
            font_size = max(13, int(p["scale"] * settings.UI_SCALE))
            font = pygame.font.Font(None, font_size)
            text_surf = font.render(p["text"], True, (60, 130, 230))
            text_surf.set_alpha(p["alpha"])
            overlay.blit(text_surf, p["pos"])
            
        # 5. Glowing Cyan laser scanner line sweep
        scanner_y = int((self.animation_time * 90) % settings.WINDOW_HEIGHT)
        pygame.draw.line(overlay, (0, 220, 255, 32), (0, scanner_y), (settings.WINDOW_WIDTH, scanner_y), 2)
        # Scanner sweep glow
        glow_surf = pygame.Surface((settings.WINDOW_WIDTH, 12), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (0, 220, 255, 7), (0, 0, settings.WINDOW_WIDTH, 12))
        overlay.blit(glow_surf, (0, scanner_y - 6))

        # Blit background elements to main screen
        screen.blit(overlay, (0, 0))

        # Draw tabs & slanted sci-fi buttons
        self._draw_tabs(screen)

        # 6. Setup Left & Right Glassmorphic container panels
        list_x = 20
        list_w = settings.WINDOW_WIDTH // 2 - 40
        list_rect = pygame.Rect(list_x, 50, list_w, settings.WINDOW_HEIGHT - 60)
        
        detail_x = settings.WINDOW_WIDTH // 2 + 20
        detail_w = settings.WINDOW_WIDTH // 2 - 40
        detail_rect = pygame.Rect(detail_x, 50, detail_w, settings.WINDOW_HEIGHT - 60)
        
        # Transparent glass bodies
        panel_overlay = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(panel_overlay, (12, 14, 30, 205), list_rect, border_radius=10)
        pygame.draw.rect(panel_overlay, (10, 11, 26, 215), detail_rect, border_radius=10)
        
        # Subtle glowing panel borders
        pygame.draw.rect(panel_overlay, (50, 70, 140, 85), list_rect, 1, border_radius=10)
        pygame.draw.rect(panel_overlay, (50, 70, 140, 85), detail_rect, 1, border_radius=10)
        screen.blit(panel_overlay, (0, 0))

        # 7. Draw List Content with Bounded Scroll Clip (95 to 400)
        clip_rect = pygame.Rect(list_x, 95, list_w, 310)
        screen.set_clip(clip_rect)
        self._draw_list(screen, list_x, list_w)
        screen.set_clip(None)

        # 8. Draw Telemetry & Real-Time Equipment Analytics Dashboard (Left-hand Bottom)
        self._draw_telemetry_dashboard(screen, list_x, list_w)

        # 9. Draw Futuristic detail panel elements
        self._draw_detail(screen, detail_x)

        # 10. Bottom stats HUD panel display
        sp = self.game.skill_tree.skill_points if self.game.skill_tree else 0
        gold_badge_y = settings.WINDOW_HEIGHT - 48
        
        # Gold badge
        gold_surf = pygame.Surface((130, 30), pygame.SRCALPHA)
        pygame.draw.rect(gold_surf, (20, 20, 10, 180), (0, 0, 130, 30), border_radius=15)
        pygame.draw.rect(gold_surf, settings.GOLD, (0, 0, 130, 30), 1, border_radius=15)
        screen.blit(gold_surf, (list_x + 10, gold_badge_y))
        draw_text(screen, f"[G] {self.game.player.gold}", (list_x + 75, gold_badge_y + 11), settings.GOLD, 16, center=True)
        
        # SP badge
        sp_surf = pygame.Surface((110, 30), pygame.SRCALPHA)
        pygame.draw.rect(sp_surf, (10, 20, 20, 180), (0, 0, 110, 30), border_radius=15)
        pygame.draw.rect(sp_surf, settings.CYAN, (0, 0, 110, 30), 1, border_radius=15)
        screen.blit(sp_surf, (list_x + 150, gold_badge_y))
        draw_text(screen, f"[SP] {sp}", (list_x + 205, gold_badge_y + 11), settings.CYAN, 16, center=True)

        # Pulsing ESC hint at the bottom center of the console
        pulse_alpha = int(128 + 127 * math.sin(self.animation_time * 4))
        esc_font = pygame.font.Font(None, 14)
        esc_text = esc_font.render("// PRESS [ESC] OR [S] TO CLOSE FORBIDDEN ARCHIVE", True, (130, 140, 160))
        esc_text.set_alpha(pulse_alpha)
        screen.blit(esc_text, (settings.WINDOW_WIDTH // 2 - esc_text.get_width() // 2, settings.WINDOW_HEIGHT - 24))

    def _draw_tabs(self, screen):
        tab_y = 10
        tab_h = 36
        tab_w = settings.WINDOW_WIDTH // 3
        
        tab_surf = pygame.Surface((settings.WINDOW_WIDTH, tab_h + 2), pygame.SRCALPHA)
        
        for i in range(3):
            is_active = (i == self.active_tab)
            color = SHOP_TAB_COLORS[i]
            
            x_start = i * tab_w
            x_end = (i + 1) * tab_w
            
            # Draw slanted cyber polygon trapezoid tabs
            pts = [
                (x_start + 12, 0),
                (x_end - 12, 0),
                (x_end - 2, tab_h),
                (x_start + 2, tab_h)
            ]
            
            bg_color = (color[0], color[1], color[2], 55) if is_active else (14, 15, 30, 210)
            pygame.draw.polygon(tab_surf, bg_color, pts)
            
            border_color = color if is_active else (45, 50, 75, 160)
            pygame.draw.polygon(tab_surf, border_color, pts, 2 if is_active else 1)
            
            # Active indicator glowing block
            if is_active:
                pygame.draw.polygon(tab_surf, color, [
                    (x_start + 18, tab_h - 4),
                    (x_end - 18, tab_h - 4),
                    (x_end - 15, tab_h - 1),
                    (x_start + 15, tab_h - 1)
                ])
                
            # Text layout inside tabs
            label_font = pygame.font.Font(None, int(17 * settings.UI_SCALE))
            label = label_font.render(t(SHOP_TAB_LABELS[i]), True, color if is_active else (120, 120, 140))
            tab_surf.blit(label, (x_start + tab_w // 2 - label.get_width() // 2, 5))
            
            sub_font = pygame.font.Font(None, int(11 * settings.UI_SCALE))
            sub = sub_font.render(SHOP_TAB_SUBTITLES[i], True, (color[0]//2 + 60, color[1]//2 + 60, color[2]//2 + 60) if is_active else (75, 75, 90))
            tab_surf.blit(sub, (x_start + tab_w // 2 - sub.get_width() // 2, 20))
            
        screen.blit(tab_surf, (0, tab_y))

    def _draw_list(self, screen, list_x, list_w):
        # Decorative Title
        title_y = 60
        draw_text(screen, t("shop_title"), (list_x + 15, title_y), settings.WHITE, 22, center=False)
        tab_color = SHOP_TAB_COLORS[self.active_tab]
        # Decorative title line
        pygame.draw.line(screen, tab_color, (list_x + 15, title_y + 20), (list_x + 160, title_y + 20), 2)
        pygame.draw.line(screen, (50, 50, 80, 100), (list_x + 160, title_y + 20), (list_x + list_w - 20, title_y + 20), 1)

        items = self._get_items()
        sy = int(self.scroll_y)

        for i, item_data in enumerate(items):
            row_y = 95 + i * 65 - sy
            if row_y < 40 or row_y > 415: # strictly bound inside item list clip frame
                continue

            row_rect = pygame.Rect(list_x + 10, row_y, list_w - 20, 58)
            is_selected = self.selected_item == item_data["id"]
            is_hovered = self.hovered_item_row == item_data["id"]
            is_equipped = self._is_equipped(item_data["id"])

            # Cyber row backgrounds
            if is_selected:
                bg = (tab_color[0] // 6, tab_color[1] // 6, tab_color[2] // 6, 210)
            elif is_hovered:
                bg = (24, 26, 52, 220)
            else:
                bg = (14, 15, 33, 190) if i % 2 == 0 else (10, 11, 26, 190)
                
            row_surf = pygame.Surface((row_rect.width, row_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(row_surf, bg, (0, 0, row_rect.width, row_rect.height), border_radius=8)
            
            # Glowing borders
            border_color = tab_color if is_selected else (tab_color[0]//2 + 50, tab_color[1]//2 + 50, tab_color[2]//2 + 50, 120) if is_hovered else (45, 45, 75, 120)
            pygame.draw.rect(row_surf, border_color, (0, 0, row_rect.width, row_rect.height), 2 if is_selected else 1, border_radius=8)
            
            screen.blit(row_surf, row_rect)

            # Selected Glowing Cyber Brackets
            if is_selected:
                bw, bh = 8, 8
                # Draw sharp brackets at outer corners
                pygame.draw.line(screen, tab_color, (row_rect.left - 1, row_rect.top - 1), (row_rect.left + bw, row_rect.top - 1), 2)
                pygame.draw.line(screen, tab_color, (row_rect.left - 1, row_rect.top - 1), (row_rect.left - 1, row_rect.top + bh), 2)
                
                pygame.draw.line(screen, tab_color, (row_rect.right + 1, row_rect.top - 1), (row_rect.right - bw, row_rect.top - 1), 2)
                pygame.draw.line(screen, tab_color, (row_rect.right + 1, row_rect.top - 1), (row_rect.right + 1, row_rect.top + bh), 2)
                
                pygame.draw.line(screen, tab_color, (row_rect.left - 1, row_rect.bottom + 1), (row_rect.left + bw, row_rect.bottom + 1), 2)
                pygame.draw.line(screen, tab_color, (row_rect.left - 1, row_rect.bottom + 1), (row_rect.left - 1, row_rect.bottom - bh), 2)
                
                pygame.draw.line(screen, tab_color, (row_rect.right + 1, row_rect.bottom + 1), (row_rect.right - bw, row_rect.bottom + 1), 2)
                pygame.draw.line(screen, tab_color, (row_rect.right + 1, row_rect.bottom + 1), (row_rect.right + 1, row_rect.bottom - bh), 2)

            name_color = settings.WHITE if not is_equipped else (130, 140, 160)
            draw_text(screen, t(item_data.get("name", item_data["id"])), (list_x + 25, row_y + 6), name_color, 18, center=False)

            cost = item_data.get("cost", 0)
            sp_cost = item_data.get("sp_cost", 0)
            cost_str = f"{cost}g"
            if sp_cost > 0:
                cost_str += f" + {sp_cost}SP"
                
            can_afford = self.game.player.gold >= cost
            sp = self.game.skill_tree.skill_points if self.game.skill_tree else 0
            if sp_cost > 0:
                can_afford = can_afford and sp >= sp_cost
                
            cost_color = settings.GOLD if can_afford else (180, 80, 80)
            draw_text(screen, cost_str, (list_x + 25, row_y + 28), cost_color, 16, center=False)

            # Draw Real-time Cyber coefficient and formula stats badges directly on the row to fill empty row space!
            badge_x = list_x + list_w - 110
            if self.active_tab == SHOP_WEAPONS:
                mult = item_data.get("multiplier", 1.0)
                badge_text = f"x{mult:.2f} ATK"
                badge_color = settings.RED
            elif self.active_tab == SHOP_SHIELDS:
                defense = item_data.get("defense", 0)
                badge_text = f"+{defense} DEF"
                badge_color = settings.BLUE
            else:
                value = item_data.get("value", 0)
                effect = item_data.get("effect", "")
                if effect == "heal":
                    badge_text = f"+{value} HP"
                elif effect == "atk_buff":
                    badge_text = f"+{value} ATK"
                elif effect == "def_buff":
                    badge_text = f"+{value} DEF"
                else:
                    badge_text = f"+{value} VAL"
                badge_color = settings.GREEN

            if is_equipped:
                # Equipped Row badge
                equipped_surf = pygame.Surface((90, 22), pygame.SRCALPHA)
                pygame.draw.rect(equipped_surf, (20, 80, 100, 120), (0, 0, 90, 22), border_radius=4)
                pygame.draw.rect(equipped_surf, settings.CYAN, (0, 0, 90, 22), 1, border_radius=4)
                screen.blit(equipped_surf, (badge_x, row_y + 6))
                draw_text(screen, t("shop_equipped_status"), (badge_x + 45, row_y + 14), settings.CYAN, 12, center=True)
                
                # Show stat coefficient badge below
                self._draw_row_stat_badge(screen, badge_x, row_y + 32, badge_text, badge_color)
            else:
                # Show centered stat coefficient badge
                self._draw_row_stat_badge(screen, badge_x, row_y + 17, badge_text, badge_color)

        # 11. Glowing Neon Scrollbar (strictly bound within item list viewport)
        max_scroll = self._get_max_scroll()
        if max_scroll > 0:
            scrollbar_x = list_x + list_w - 8
            scrollbar_y = 95
            scrollbar_h = 305
            scrollbar_w = 4
            
            pygame.draw.rect(screen, (20, 22, 45, 150), (scrollbar_x, scrollbar_y, scrollbar_w, scrollbar_h), border_radius=2)
            
            visible_ratio = 300 / (len(items) * 65 + 10)
            thumb_h = max(20, int(scrollbar_h * visible_ratio))
            scroll_ratio = self.scroll_y / max_scroll
            thumb_y = scrollbar_y + int((scrollbar_h - thumb_h) * scroll_ratio)
            
            pygame.draw.rect(screen, tab_color, (scrollbar_x - 1, thumb_y, scrollbar_w + 2, thumb_h), border_radius=3)
            glow_thumb = pygame.Surface((scrollbar_w + 4, thumb_h + 2), pygame.SRCALPHA)
            pygame.draw.rect(glow_thumb, (tab_color[0], tab_color[1], tab_color[2], 100), (0, 0, scrollbar_w + 4, thumb_h + 2), 1, border_radius=4)
            screen.blit(glow_thumb, (scrollbar_x - 2, thumb_y - 1))

    def _draw_row_stat_badge(self, screen, x, y, text, color):
        badge_surf = pygame.Surface((90, 22), pygame.SRCALPHA)
        pygame.draw.rect(badge_surf, (color[0]//5, color[1]//5, color[2]//5, 180), (0, 0, 90, 22), border_radius=4)
        pygame.draw.rect(badge_surf, color, (0, 0, 90, 22), 1, border_radius=4)
        screen.blit(badge_surf, (x, y))
        draw_text(screen, text, (x + 45, y + 9), color, 13, center=True)

    def _draw_telemetry_dashboard(self, screen, list_x, list_w):
        y_dash = 415
        h_dash = 215
        dash_rect = pygame.Rect(list_x + 10, y_dash, list_w - 20, h_dash)
        
        # Dashboard frame
        dash_surf = pygame.Surface((dash_rect.width, dash_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(dash_surf, (8, 9, 22, 230), (0, 0, dash_rect.width, dash_rect.height), border_radius=8)
        
        tab_color = SHOP_TAB_COLORS[self.active_tab]
        pygame.draw.rect(dash_surf, (tab_color[0], tab_color[1], tab_color[2], 75), (0, 0, dash_rect.width, dash_rect.height), 1, border_radius=8)
        screen.blit(dash_surf, dash_rect)
        
        # Dashboard Title
        font_tiny = pygame.font.Font(None, int(13 * settings.UI_SCALE))
        draw_text(screen, "EQUIPMENT TELEMETRY // SYSTEM ANALYTICS", (dash_rect.left + 12, dash_rect.top + 8), settings.GRAY, 12, center=False)
        pygame.draw.line(screen, (40, 50, 80, 100), (dash_rect.left + 12, dash_rect.top + 22), (dash_rect.right - 12, dash_rect.top + 22), 1)
        
        # Calculate active system combat formulas live
        player = self.game.player
        base_atk = settings.PLAYER_ATTACK_DAMAGE + player.upgrades["atk"] * settings.UPGRADE_PER_LEVEL["atk"]
        weapon_id = player.equipment.get("weapon")
        weapon_data = settings.EQUIPMENT_DATA["weapons"].get(weapon_id) if weapon_id else None
        weapon_name = t(weapon_data["name"]) if weapon_data else "UNARMED"
        weapon_mult = weapon_data.get("multiplier", 1.0) if weapon_data else 1.0
        eff_atk = base_atk * weapon_mult + player._buff_sum("atk_buff")
        
        base_def = player.upgrades["def"] * settings.UPGRADE_PER_LEVEL["def"]
        shield_id = player.equipment.get("shield")
        shield_data = settings.EQUIPMENT_DATA["shields"].get(shield_id) if shield_id else None
        shield_name = t(shield_data["name"]) if shield_data else "NONE"
        shield_def = shield_data.get("defense", 0) if shield_data else 0
        eff_def = base_def + shield_def + player._buff_sum("def_buff")

        # Left Column: Loaded details
        col1_x = dash_rect.left + 12
        draw_text(screen, f"WEAPON: {weapon_name.upper()}", (col1_x, dash_rect.top + 30), settings.WHITE, 13, center=False)
        draw_text(screen, f"FACTOR: x{weapon_mult:.2f} ATK", (col1_x, dash_rect.top + 48), settings.RED, 13, center=False)
        
        draw_text(screen, f"SHIELD: {shield_name.upper()}", (col1_x, dash_rect.top + 70), settings.WHITE, 13, center=False)
        draw_text(screen, f"INTEGRITY: +{shield_def} DEF", (col1_x, dash_rect.top + 88), settings.BLUE, 13, center=False)
        
        # Right Column: Dynamic Combat Formulas
        col2_x = dash_rect.left + 165
        draw_text(screen, "f(DMG) = base * mult", (col2_x, dash_rect.top + 30), settings.GRAY, 12, center=False)
        draw_text(screen, f"  = {base_atk} * {weapon_mult:.2f} = {eff_atk:.1f}", (col2_x, dash_rect.top + 48), settings.RED, 14, center=False)
        
        draw_text(screen, "g(DEF) = base + shield", (col2_x, dash_rect.top + 70), settings.GRAY, 12, center=False)
        draw_text(screen, f"  = {base_def} + {shield_def} = {eff_def}", (col2_x, dash_rect.top + 88), settings.BLUE, 14, center=False)
        
        # Bottom Oscilloscope Grid
        osc_y = dash_rect.top + 108
        osc_h = 95
        osc_rect = pygame.Rect(dash_rect.left + 10, osc_y, dash_rect.width - 20, osc_h)
        
        # Dark grid background for wave
        pygame.draw.rect(screen, (5, 6, 16, 255), osc_rect, border_radius=4)
        pygame.draw.rect(screen, (30, 45, 80, 110), osc_rect, 1, border_radius=4)
        
        # Central green dotted axis
        pygame.draw.line(screen, (20, 60, 40, 75), (osc_rect.left, osc_rect.centery), (osc_rect.right, osc_rect.centery), 1)
        
        # Draw unique quantum waveform per selected item
        wave_pts = []
        iid = self.selected_item
        anim_t = self.animation_time
        
        for sx in range(osc_rect.left + 2, osc_rect.right - 2, 3):
            rel_x = (sx - osc_rect.left) / osc_rect.width  # 0.0 to 1.0 normalized
            phase = rel_x * math.pi * 2 - anim_t * 3.0
            wave_y = osc_rect.centery
            
            # --- WEAPONS: Unique quantum signatures ---
            if iid == "linear_blade":
                # Sharp triangular sawtooth - clean linear strikes
                wave_y += int(28 * (2 * abs(2 * (rel_x * 4 + anim_t * 0.5) % 1 - 1) - 1))
                
            elif iid == "fiery_tangent":
                # Tangent-like bursts with clipped asymptotes
                tan_val = math.tan(phase * 1.5)
                wave_y += int(22 * math.tanh(tan_val * 0.4))
                
            elif iid == "cryo_bisector":
                # Dual-frequency interference - two waves bisecting
                w1 = math.sin(phase * 2.0)
                w2 = math.sin(phase * 3.5 + 1.2)
                wave_y += int(18 * (w1 * w2))
                
            elif iid == "fractal_thunder_axe":
                # Chaotic multi-harmonic with noise-like texture
                wave_y += int(15 * math.sin(phase * 1.7) + 10 * math.sin(phase * 5.3 + anim_t) + 5 * math.sin(phase * 13.1))
                
            elif iid == "singularity_staff":
                # Spiral helix projection - circular oscillation
                wave_y += int(25 * math.sin(phase) * math.cos(phase * 0.7 + anim_t * 0.5))
                
            elif iid == "null_matrix_dagger":
                # Square wave / step function - digital precision
                wave_y += int(24 * (1 if math.sin(phase * 2.5) > 0 else -1))
                
            elif iid == "max_modulus_axe":
                # Absolute value modulus wave - sharp peaks
                wave_y += int(26 * abs(math.sin(phase * 1.8)) - 13)
                
            # --- SHIELDS: Defensive quantum patterns ---
            elif iid == "cartesian_plane_shield":
                # Grid-based step function - structured barrier
                grid_x = int(rel_x * 8)
                grid_y = int(math.sin(grid_x * 0.8 + anim_t) * 20)
                wave_y += grid_y
                
            elif iid == "orthogonal_barrier":
                # Orthogonal pulse wave - right-angle oscillations
                pulse = math.sin(phase * 2.0)
                wave_y += int(22 * (1 if pulse > 0.3 else (-1 if pulse < -0.3 else 0)))
                
            elif iid == "reflection_matrix":
                # Bouncing wave - reflects off boundaries
                bounce = abs(2 * (rel_x * 3 + anim_t * 0.4) % 2 - 1)
                wave_y += int(24 * (2 * bounce - 1))
                
            elif iid == "steel_axiom_shield":
                # Golden ratio spiral - fibonacci-based oscillation
                phi = (1 + math.sqrt(5)) / 2
                wave_y += int(20 * math.sin(phase * phi) * math.cos(phase / phi + anim_t * 0.3))
                
            # --- ITEMS/CONSUMABLES: Formula-based waves ---
            elif iid == "linear_hp_formula":
                # Linear ramp with periodic reset
                ramp = (rel_x * 4 + anim_t * 0.3) % 1
                wave_y += int(28 * (2 * ramp - 1))
                
            elif iid == "riemann_hp_sum":
                # Staircase Riemann sum approximation
                steps = 6
                step_val = int(rel_x * steps) / steps
                wave_y += int(22 * math.sin(step_val * math.pi * 2 + anim_t))
                
            elif iid == "force_derivative":
                # Derivative/slope - rate of change visualization
                base = math.sin(rel_x * math.pi * 3 + anim_t)
                deriv = math.cos(rel_x * math.pi * 3 + anim_t) * 3 * math.pi
                wave_y += int(15 * deriv / (1 + abs(deriv) * 0.1))
                
            elif iid == "defense_constant":
                # Flat line with occasional defense spikes
                spike = 1 if math.sin(anim_t * 2.5 + rel_x * 10) > 0.95 else 0
                wave_y += int(20 * spike * math.sin(rel_x * math.pi * 4))
                
            elif iid == "translation_vector":
                # Traveling pulse wave - moving energy packet
                pulse_pos = (anim_t * 0.3) % 1
                dist_from_pulse = abs(rel_x - pulse_pos)
                wave_y += int(28 * math.exp(-dist_from_pulse * 15) * math.sin(dist_from_pulse * 30))
                
            elif iid == "vitality_integral":
                # Accumulating integral wave - area under curve
                integral = 0
                for step in range(int(rel_x * 20) + 1):
                    x_step = step / 20
                    integral += math.sin(x_step * math.pi * 2 + anim_t) * 0.05
                wave_y += int(25 * integral)
                
            else:
                # Default: smooth sine wave
                wave_y += int(20 * math.sin(phase))
            
            wave_y = max(osc_rect.top + 4, min(osc_rect.bottom - 4, wave_y))
            wave_pts.append((sx, wave_y))
            
        if len(wave_pts) > 1:
            pygame.draw.lines(screen, tab_color, False, wave_pts, 2)
            
        # Coherence % label - unique per item
        coherence_base = {
            "linear_blade": 96.5, "fiery_tangent": 91.2, "cryo_bisector": 94.8,
            "fractal_thunder_axe": 88.3, "singularity_staff": 97.1, "null_matrix_dagger": 93.7,
            "max_modulus_axe": 90.5, "cartesian_plane_shield": 95.4, "orthogonal_barrier": 92.8,
            "reflection_matrix": 96.0, "steel_axiom_shield": 94.2, "linear_hp_formula": 98.1,
            "riemann_hp_sum": 93.5, "force_derivative": 91.8, "defense_constant": 97.6,
            "translation_vector": 95.0, "vitality_integral": 94.5
        }.get(iid, 94.0)
        coherence = coherence_base + 3.0 * math.sin(self.animation_time * 2.0 + hash(iid) % 100 * 0.1)
        lbl_coherence = font_tiny.render(f"QUANTUM COHERENCE: {coherence:.2f}% // RES_OK", True, tab_color)
        screen.blit(lbl_coherence, (osc_rect.left + 8, osc_rect.top + 6))

    def _is_equipped(self, item_id):
        if self.active_tab == SHOP_WEAPONS:
            return self.game.player.equipment.get("weapon") == item_id
        elif self.active_tab == SHOP_SHIELDS:
            return self.game.player.equipment.get("shield") == item_id
        return False

    def _draw_detail(self, screen, detail_x):
        detail_w = settings.WINDOW_WIDTH // 2 - 40
        tab_color = SHOP_TAB_COLORS[self.active_tab]

        # 12. Scanning Hologram visualizer frame
        visualizer_rect = pygame.Rect(detail_x + 15, 60, detail_w - 30, 180)
        pygame.draw.rect(screen, (8, 8, 22, 220), visualizer_rect, border_radius=8)
        pygame.draw.rect(screen, (tab_color[0], tab_color[1], tab_color[2], 80), visualizer_rect, 1, border_radius=8)

        # Faint internal grid coordinates
        for vx in range(visualizer_rect.left + 15, visualizer_rect.right, 15):
            pygame.draw.line(screen, (30, 45, 90, 30), (vx, visualizer_rect.top), (vx, visualizer_rect.bottom), 1)
        for vy in range(visualizer_rect.top + 15, visualizer_rect.bottom, 15):
            pygame.draw.line(screen, (30, 45, 90, 30), (visualizer_rect.left, vy), (visualizer_rect.right, vy), 1)

        # Corner readouts inside visualizer
        font_tiny = pygame.font.Font(None, int(13 * settings.UI_SCALE))
        
        img_tl = font_tiny.render("DIAGNOSTIC // HOLO_MESH", True, (100, 115, 145))
        screen.blit(img_tl, (visualizer_rect.left + 8, visualizer_rect.top + 5))
        
        ref_label = f"REF_ID: 0x{id(self.selected_item) & 0xFFFF:04X}" if self.selected_item else "REF_ID: NONE"
        img_tr = font_tiny.render(ref_label, True, (100, 115, 145))
        screen.blit(img_tr, (visualizer_rect.right - img_tr.get_width() - 8, visualizer_rect.top + 5))
        
        img_bl = font_tiny.render("RENDER: WIREFRAME_3D", True, (100, 115, 145))
        screen.blit(img_bl, (visualizer_rect.left + 8, visualizer_rect.bottom - 13))
        
        img_br = font_tiny.render("SYS: RUNNING_OK", True, (100, 115, 145))
        screen.blit(img_br, (visualizer_rect.right - img_br.get_width() - 8, visualizer_rect.bottom - 13))

        # Check prompt first
        if not self.selected_item:
            draw_text(screen, t("shop_select_prompt"), (visualizer_rect.centerx, visualizer_rect.centery), settings.GRAY, 18)
            return

        item_data = self._get_item_data(self.selected_item)
        if not item_data:
            return

        # 13. Draw Animated UNIQUE 3D projection meshes for each item
        overlay_mesh = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
        cx, cy = visualizer_rect.centerx, visualizer_rect.centery
        scale_3d = 140
        dist = 2.0
        
        time_val = self.animation_time
        angle_x = time_val * 0.4
        angle_y = time_val * 0.6
        angle_z = time_val * 0.2
        
        def project_3d(x, y, z):
            cos_a, sin_a = math.cos(angle_x), math.sin(angle_x)
            ry, rz = y * cos_a - z * sin_a, y * sin_a + z * cos_a
            cos_a, sin_a = math.cos(angle_y), math.sin(angle_y)
            rx, rz = x * cos_a + rz * sin_a, -x * sin_a + rz * cos_a
            cos_a, sin_a = math.cos(angle_z), math.sin(angle_z)
            rx, ry = rx * cos_a - ry * sin_a, rx * sin_a + ry * cos_a
            
            px = int(cx + (rx * scale_3d) / (rz + dist))
            py = int(cy + (ry * scale_3d) / (rz + dist))
            return px, py

        iid = self.selected_item
        
        # --- WEAPONS TAB ---
        if iid == "linear_blade":
            vertices = [
                (0, 0, 1.2),       # 0: tip
                (0.16, 0, 0),      # 1: right blade edge
                (0, 0.16, 0),      # 2: front blade face
                (-0.16, 0, 0),     # 3: left blade edge
                (0, -0.16, 0),     # 4: back blade face
                (0, 0, -0.55),     # 5: blade base
                (-0.48, 0, -0.55), # 6: guard left
                (0.48, 0, -0.55),  # 7: guard right
                (0, 0.2, -0.55),   # 8: guard top
                (0, -0.2, -0.55),  # 9: guard bottom
                (0, 0, -1.0),      # 10: hilt base
                (0, 0, -1.15)      # 11: pommel
            ]
            edges = [
                (0, 1), (0, 2), (0, 3), (0, 4), # tip to sides
                (5, 1), (5, 2), (5, 3), (5, 4), # base to sides
                (1, 2), (2, 3), (3, 4), (4, 1), # side rings
                (6, 7), (8, 9),                 # cross guard lines
                (5, 6), (5, 7), (5, 8), (5, 9), # blade base to guard
                (5, 10), (10, 11)               # hilt grip & pommel
            ]
            self._project_and_draw_wireframe(overlay_mesh, cx, cy, scale_3d, dist, vertices, edges, tab_color, angle_x, angle_y, angle_z)
            
        elif iid == "fiery_tangent":
            circle_pts = []
            for i in range(16):
                ang = (i * 2 * math.pi) / 16
                circle_pts.append(project_3d(0.62 * math.cos(ang), 0.62 * math.sin(ang), 0))
            pygame.draw.lines(overlay_mesh, tab_color, True, circle_pts, 2)
            
            for angle_offset in [0, 2*math.pi/3, 4*math.pi/3]:
                theta = self.animation_time * 1.5 + angle_offset
                cx_pt, cy_pt = 0.62 * math.cos(theta), 0.62 * math.sin(theta)
                tx, ty = -math.sin(theta), math.cos(theta)
                ex_pt, ey_pt = cx_pt + tx * 0.4, cy_pt + ty * 0.4
                
                p1 = project_3d(cx_pt, cy_pt, 0)
                p2 = project_3d(ex_pt, ey_pt, 0)
                
                pygame.draw.line(overlay_mesh, settings.ORANGE, p1, p2, 2)
                pygame.draw.circle(overlay_mesh, settings.WHITE, p2, 4)
                
        elif iid == "cryo_bisector":
            vertices = [
                (-0.16, 0, 0.85),       # 0: tip
                (-0.65, -0.5, -0.5),    # 1: base 1
                (-0.65, 0.5, -0.5),     # 2: base 2
                (-0.16, 0.5, -0.5),     # 3: bisect base front
                (-0.16, -0.5, -0.5),    # 4: bisect base back
                (0.16, 0, 0.85),        # 5: tip
                (0.65, -0.5, -0.5),     # 6: base 1
                (0.65, 0.5, -0.5),      # 7: base 2
                (0.16, 0.5, -0.5),      # 8: bisect base front
                (0.16, -0.5, -0.5)      # 9: bisect base back
            ]
            edges = [
                (0, 1), (0, 2), (0, 3), (0, 4),
                (1, 2), (2, 3), (3, 4), (4, 1),
                (5, 6), (5, 7), (5, 8), (5, 9),
                (6, 7), (7, 8), (8, 9), (9, 6)
            ]
            self._project_and_draw_wireframe(overlay_mesh, cx, cy, scale_3d, dist, vertices, edges, tab_color, angle_x, angle_y, angle_z)
            
            p_pl1 = project_3d(0, -0.7, -0.55)
            p_pl2 = project_3d(0, 0.7, -0.55)
            p_pl3 = project_3d(0, 0.7, 0.95)
            p_pl4 = project_3d(0, -0.7, 0.95)
            pygame.draw.lines(overlay_mesh, (100, 180, 255, 60), True, [p_pl1, p_pl2, p_pl3, p_pl4], 1)
            
        elif iid == "fractal_thunder_axe":
            p_h1 = project_3d(0, 0, -0.9)
            p_h2 = project_3d(0, 0, 0.45)
            p_soc = project_3d(0, 0.13, 0.2)
            p_bl1 = project_3d(-0.45, 0, 0.32)
            p_bl2 = project_3d(-0.45, 0, -0.13)
            
            pygame.draw.line(overlay_mesh, tab_color, p_h1, p_h2, 2)
            pygame.draw.line(overlay_mesh, tab_color, p_h2, p_bl1, 2)
            pygame.draw.line(overlay_mesh, tab_color, p_bl1, p_bl2, 2)
            pygame.draw.line(overlay_mesh, tab_color, p_bl2, p_soc, 2)
            
            random.seed(42)
            for b in range(3):
                bz = 0.3 - b * 0.2
                bx, by = -0.45, 0.0
                current_p = project_3d(bx, by, bz)
                for step in range(3):
                    next_x = bx - 0.16
                    next_y = by + random.uniform(-0.14, 0.14) * math.sin(self.animation_time * 6 + step)
                    next_z = bz + random.uniform(-0.1, 0.1)
                    
                    next_p = project_3d(next_x, next_y, next_z)
                    pygame.draw.line(overlay_mesh, settings.CYAN, current_p, next_p, 1)
                    
                    bx, by, bz = next_x, next_y, next_z
                    current_p = next_p
                    
        elif iid == "singularity_staff":
            rings = [(0.9, 0.4), (0.65, 0.13), (0.4, -0.13), (0.2, -0.4)]
            for R, Z in rings:
                ring_pts = []
                for i in range(12):
                    ang = (i * 2 * math.pi) / 12
                    ring_pts.append(project_3d(R * math.cos(ang), R * math.sin(ang), Z))
                pygame.draw.lines(overlay_mesh, tab_color, True, ring_pts, 1)
                
            for m in range(8):
                ang = (m * 2 * math.pi) / 8
                cos_a, sin_a = math.cos(ang), math.sin(ang)
                pts = []
                for R, Z in rings:
                    pts.append(project_3d(R * cos_a, R * sin_a, Z))
                pts.append(project_3d(0, 0, -0.85))
                pygame.draw.lines(overlay_mesh, settings.PURPLE, False, pts, 1)
                
        elif iid == "null_matrix_dagger":
            vertices = []
            for x in [-0.65, 0.0, 0.65]:
                for y in [-0.65, 0.0, 0.65]:
                    for z in [-0.65, 0.0, 0.65]:
                        vertices.append((x, y, z))
            edges = []
            for i in range(27):
                x1, y1, z1 = vertices[i]
                for j in range(i + 1, 27):
                    x2, y2, z2 = vertices[j]
                    diff = sum(1 for k in range(3) if vertices[i][k] != vertices[j][k])
                    if diff == 1:
                        dist_3d = math.sqrt((x1-x2)**2 + (y1-y2)**2 + (z1-z2)**2)
                        if dist_3d < 0.72:
                            if (x1 == 0 and y1 == 0 and z1 == 0) or (x2 == 0 and y2 == 0 and z2 == 0):
                                continue
                            edges.append((i, j))
            self._project_and_draw_wireframe(overlay_mesh, cx, cy, scale_3d, dist, vertices, edges, tab_color, angle_x, angle_y, angle_z)
            
        elif iid == "max_modulus_axe":
            vertices = [
                (0, 0, -0.95),        # 0: Handle bottom
                (0, 0, 0.75),         # 1: Handle top
                (0, 0.1, 0.45),       # 2: Socket top left
                (0, -0.1, 0.45),      # 3: Socket top right
                (0, -0.1, 0.06),      # 4: Socket bottom right
                (0, 0.1, 0.06),       # 5: Socket bottom left
                (-0.65, 0, 0.65),     # 6: Left blade outer top
                (-0.65, 0, -0.13),    # 7: Left blade outer bottom
                (0.65, 0, 0.65),      # 8: Right blade outer top
                (0.65, 0, -0.13)      # 9: Right blade outer bottom
            ]
            edges = [
                (0, 1),
                (2, 3), (3, 4), (4, 5), (5, 2),
                (2, 6), (5, 7), (6, 7),
                (3, 8), (4, 9), (8, 9)
            ]
            self._project_and_draw_wireframe(overlay_mesh, cx, cy, scale_3d, dist, vertices, edges, tab_color, angle_x, angle_y, angle_z)

        # --- SHIELDS TAB ---
        elif iid == "cartesian_plane_shield":
            grid_vals = [-0.65, -0.32, 0.0, 0.32, 0.65]
            for x in grid_vals:
                p1 = project_3d(x, -0.65, 0)
                p2 = project_3d(x, 0.65, 0)
                col = settings.CYAN if x == 0.0 else (50, 70, 120, 100)
                pygame.draw.line(overlay_mesh, col, p1, p2, 2 if x == 0.0 else 1)
            for y in grid_vals:
                p1 = project_3d(-0.65, y, 0)
                p2 = project_3d(0.65, y, 0)
                col = settings.CYAN if y == 0.0 else (50, 70, 120, 100)
                pygame.draw.line(overlay_mesh, col, p1, p2, 2 if y == 0.0 else 1)
                
        elif iid == "orthogonal_barrier":
            vertices = [
                (0, 0, 0),          # 0: origin
                (0.7, 0, 0),        # 1: X axis
                (0, 0.7, 0),        # 2: Y axis
                (0, 0, 0.7),        # 3: Z axis
                (0.7, 0.7, 0),      # 4: XY boundary
                (0, 0.7, 0.7),      # 5: YZ boundary
                (0.7, 0, 0.7),      # 6: XZ boundary
                (0.35, 0, 0),
                (0, 0.35, 0),
                (0, 0, 0.35),
                (0.35, 0.7, 0),
                (0.7, 0.35, 0),
                (0, 0.35, 0.7),
                (0, 0.7, 0.35),
                (0.35, 0, 0.7),
                (0.7, 0, 0.35)
            ]
            edges = [
                (0, 1), (0, 2), (0, 3),
                (1, 4), (2, 4),
                (2, 5), (3, 5),
                (1, 6), (3, 6),
                (7, 10), (8, 11),
                (8, 12), (9, 13),
                (7, 14), (9, 15)
            ]
            self._project_and_draw_wireframe(overlay_mesh, cx, cy, scale_3d, dist, vertices, edges, tab_color, angle_x, angle_y, angle_z)
            
        elif iid == "reflection_matrix":
            for Z in [-0.45, 0.45]:
                p1 = project_3d(-0.7, -0.7, Z)
                p2 = project_3d(0.7, -0.7, Z)
                p3 = project_3d(0.7, 0.7, Z)
                p4 = project_3d(-0.7, 0.7, Z)
                pygame.draw.lines(overlay_mesh, tab_color, True, [p1, p2, p3, p4], 1)
                
            time_cycle = (self.animation_time * 0.9) % 2.0
            if time_cycle < 1.0:
                v_start = (0.55, -0.55, 0.45)
                v_end = (-0.55, 0.55, -0.45)
                t_val = time_cycle
                cx_pt = v_start[0] + (v_end[0] - v_start[0]) * t_val
                cy_pt = v_start[1] + (v_end[1] - v_start[1]) * t_val
                cz_pt = v_start[2] + (v_end[2] - v_start[2]) * t_val
                
                p_s = project_3d(v_start[0], v_start[1], v_start[2])
                p_c = project_3d(cx_pt, cy_pt, cz_pt)
                pygame.draw.line(overlay_mesh, settings.GOLD, p_s, p_c, 2)
                pygame.draw.circle(overlay_mesh, settings.WHITE, p_c, 4)
            else:
                v_start = (0.55, -0.55, 0.45)
                v_mid = (-0.55, 0.55, -0.45)
                v_end = (-1.0, -0.13, 0.45)
                t_val = time_cycle - 1.0
                cx_pt = v_mid[0] + (v_end[0] - v_mid[0]) * t_val
                cy_pt = v_mid[1] + (v_end[1] - v_mid[1]) * t_val
                cz_pt = v_mid[2] + (v_end[2] - v_mid[2]) * t_val
                
                p_s = project_3d(v_start[0], v_start[1], v_start[2])
                p_m = project_3d(v_mid[0], v_mid[1], v_mid[2])
                p_c = project_3d(cx_pt, cy_pt, cz_pt)
                pygame.draw.line(overlay_mesh, settings.GOLD, p_s, p_m, 2)
                pygame.draw.line(overlay_mesh, settings.YELLOW, p_m, p_c, 2)
                pygame.draw.circle(overlay_mesh, settings.WHITE, p_c, 4)
                
        elif iid == "steel_axiom_shield":
            phi = (1.0 + math.sqrt(5.0)) / 2.0
            s_val = 0.52
            vertices = []
            for x in [-1, 1]:
                for y in [-1, 1]:
                    for z in [-1, 1]:
                        vertices.append((x*s_val, y*s_val, z*s_val))
            for i in [-1, 1]:
                for j in [-1, 1]:
                    vertices.append((0, i*s_val/phi, j*s_val*phi))
                    vertices.append((i*s_val/phi, j*s_val*phi, 0))
                    vertices.append((i*s_val*phi, 0, j*s_val/phi))
            edges = []
            for i in range(20):
                for j in range(i + 1, 20):
                    x1, y1, z1 = vertices[i]
                    x2, y2, z2 = vertices[j]
                    dist_3d = math.sqrt((x1-x2)**2 + (y1-y2)**2 + (z1-z2)**2)
                    if dist_3d < 0.75:
                        edges.append((i, j))
            self._project_and_draw_wireframe(overlay_mesh, cx, cy, scale_3d, dist, vertices, edges, tab_color, angle_x, angle_y, angle_z)

        # --- ITEMS (CONSUMABLES) TAB ---
        elif iid == "linear_hp_formula":
            pygame.draw.line(overlay_mesh, settings.GRAY, project_3d(-0.75, 0, 0), project_3d(0.75, 0, 0), 1)
            pygame.draw.line(overlay_mesh, settings.GRAY, project_3d(0, -0.75, 0), project_3d(0, 0.75, 0), 1)
            pygame.draw.line(overlay_mesh, tab_color, project_3d(-0.7, -0.1, 0), project_3d(0.7, 0.6, 0), 2)
            
            x_pos = 0.5 * math.sin(self.animation_time * 2.2)
            y_pos = 0.5 * x_pos + 0.2
            p_dot = project_3d(x_pos, y_pos, 0)
            p_px = project_3d(x_pos, 0, 0)
            p_py = project_3d(0, y_pos, 0)
            pygame.draw.line(overlay_mesh, (110, 110, 110, 110), p_dot, p_px, 1)
            pygame.draw.line(overlay_mesh, (110, 110, 110, 110), p_dot, p_py, 1)
            pygame.draw.circle(overlay_mesh, settings.WHITE, p_dot, 4)
            
        elif iid == "riemann_hp_sum":
            curve_pts = []
            for i in range(24):
                cx_val = -0.75 + (i * 1.5) / 23
                cy_val = 0.38 * math.cos(cx_val * 3.0) + 0.18
                curve_pts.append(project_3d(cx_val, cy_val, 0))
            pygame.draw.lines(overlay_mesh, settings.WHITE, False, curve_pts, 2)
            
            n_blocks = 4
            b_width = 1.5 / n_blocks
            for b in range(n_blocks):
                lx_val = -0.75 + b * b_width
                rx_val = lx_val + b_width
                mx_val = (lx_val + rx_val) / 2.0
                h_val = 0.38 * math.cos(mx_val * 3.0) + 0.18
                
                p_bl = project_3d(lx_val, 0, 0)
                p_tl = project_3d(lx_val, h_val, 0)
                p_tr = project_3d(rx_val, h_val, 0)
                p_br = project_3d(rx_val, 0, 0)
                
                pygame.draw.lines(overlay_mesh, tab_color, True, [p_bl, p_tl, p_tr, p_br], 1)
                pygame.draw.polygon(overlay_mesh, (tab_color[0], tab_color[1], tab_color[2], 30), [p_bl, p_tl, p_tr, p_br])
                
        elif iid == "force_derivative":
            curve_pts = []
            for i in range(24):
                cx_val = -0.75 + (i * 1.5) / 23
                cy_val = (cx_val ** 3) - 0.55 * cx_val
                curve_pts.append(project_3d(cx_val, cy_val, 0))
            pygame.draw.lines(overlay_mesh, settings.WHITE, False, curve_pts, 2)
            
            t_val = 0.58 * math.sin(self.animation_time * 1.6)
            cy_val = (t_val ** 3) - 0.55 * t_val
            p_dot = project_3d(t_val, cy_val, 0)
            
            slope = 3 * (t_val ** 2) - 0.55
            dx = 0.22
            dy = dx * slope
            
            p_tan1 = project_3d(t_val - dx, cy_val - dy, 0)
            p_tan2 = project_3d(t_val + dx, cy_val + dy, 0)
            pygame.draw.line(overlay_mesh, settings.ORANGE, p_tan1, p_tan2, 2)
            pygame.draw.circle(overlay_mesh, settings.WHITE, p_dot, 4)
            
        elif iid == "defense_constant":
            vertices = []
            edges = []
            R_major = 0.55
            r_minor = 0.2
            n_u = 8
            n_v = 8
            for u in range(n_u):
                theta = (u * 2 * math.pi) / n_u
                for v in range(n_v):
                    phi = (v * 2 * math.pi) / n_v
                    x = (R_major + r_minor * math.cos(phi)) * math.cos(theta)
                    y = (R_major + r_minor * math.cos(phi)) * math.sin(theta)
                    z = r_minor * math.sin(phi)
                    vertices.append((x, y, z))
            for u in range(n_u):
                for v in range(n_v):
                    idx = u * n_v + v
                    next_u = ((u + 1) % n_u) * n_v + v
                    next_v = u * n_v + ((v + 1) % n_v)
                    edges.append((idx, next_u))
                    edges.append((idx, next_v))
            self._project_and_draw_wireframe(overlay_mesh, cx, cy, scale_3d, dist, vertices, edges, tab_color, angle_x, angle_y, angle_z)
            
        elif iid == "translation_vector":
            box_v = []
            for x in [-0.55, 0.55]:
                for y in [-0.55, 0.55]:
                    for z in [-0.55, 0.55]:
                        box_v.append((x, y, z))
            box_e = []
            for i in range(8):
                for j in range(i + 1, 8):
                    if sum(1 for k in range(3) if box_v[i][k] != box_v[j][k]) == 1:
                        box_e.append((i, j))
            for start, end in box_e:
                pygame.draw.line(overlay_mesh, (80, 85, 110, 60), project_3d(*box_v[start]), project_3d(*box_v[end]), 1)
                
            offset = 0.35 * math.sin(self.animation_time * 2.8)
            p_base = project_3d(-0.25 + offset, -0.25 + offset, -0.25 + offset)
            p_tip = project_3d(0.25 + offset, 0.25 + offset, 0.25 + offset)
            pygame.draw.line(overlay_mesh, tab_color, p_base, p_tip, 3)
            pygame.draw.circle(overlay_mesh, settings.WHITE, p_tip, 5)
            
        elif iid == "vitality_integral":
            curve_pts = []
            for i in range(24):
                cx_val = -0.75 + (i * 1.5) / 23
                cy_val = 0.38 * math.cos(cx_val * 2.5) + 0.18
                curve_pts.append(project_3d(cx_val, cy_val, 0))
            pygame.draw.lines(overlay_mesh, settings.WHITE, False, curve_pts, 2)
            
            pygame.draw.line(overlay_mesh, settings.GRAY, project_3d(-0.45, 0, 0), project_3d(-0.45, 0.38*math.cos(-0.45*2.5)+0.18, 0), 1)
            pygame.draw.line(overlay_mesh, settings.GRAY, project_3d(0.45, 0, 0), project_3d(0.45, 0.38*math.cos(0.45*2.5)+0.18, 0), 1)
            
            for step in range(8):
                curr_x = -0.45 + (step * 0.9) / 7
                curr_y = 0.38 * math.cos(curr_x * 2.5) + 0.18
                pygame.draw.line(overlay_mesh, (tab_color[0], tab_color[1], tab_color[2], 90), project_3d(curr_x, 0, 0), project_3d(curr_x, curr_y, 0), 1)

        screen.blit(overlay_mesh, (0, 0))

        # 14. Text content info layout
        y = 255
        draw_text(screen, t(item_data.get("name", self.selected_item)), (detail_x + 15, y), settings.WHITE, 24, center=False)
        pygame.draw.line(screen, tab_color, (detail_x + 15, y + 26), (detail_x + 140, y + 26), 2)
        y += 36

        desc = t(item_data.get("desc", ""))
        draw_text(screen, desc, (detail_x + 15, y), settings.LIGHT_GRAY, 16, center=False)
        y += 42

        pygame.draw.line(screen, (50, 50, 75, 100), (detail_x + 15, y), (detail_x + detail_w - 15, y), 1)
        y += 10

        # 15. Stat Progress Gauges & comparative meters
        if self.active_tab == SHOP_WEAPONS:
            mult = item_data.get("multiplier", 1.0)
            mult_pct = (mult - 1.0) / 0.20
            draw_text(screen, "OPERATIONAL CAPACITY // ALGEBRAIC FACTOR", (detail_x + 15, y), settings.GRAY, 13, center=False)
            self._draw_neon_bar(screen, detail_x + 15, y + 18, detail_w - 30, 10, mult_pct, settings.RED)
            draw_text(screen, t("shop_atk_multiplier", mult=f"{mult:.2f}"), (detail_x + 15, y + 34), settings.RED, 16, center=False)
            y += 54
            
            effect = item_data.get("effect")
            if effect:
                effect_names = {
                    "burn": t("effect_burn"),
                    "slow": t("effect_slow"),
                    "stun": t("effect_stun"),
                    "aoe": t("effect_aoe"),
                    "poison": t("effect_poison")
                }
                draw_text(screen, t("shop_effect_label", effect=effect_names.get(effect, effect)), (detail_x + 15, y), settings.ORANGE, 15, center=False)
                y += 24
        elif self.active_tab == SHOP_SHIELDS:
            defense = item_data.get("defense", 0)
            def_pct = defense / 10.0
            draw_text(screen, "BARRIER INTEGRITY // SPATIAL DEFENSE", (detail_x + 15, y), settings.GRAY, 13, center=False)
            self._draw_neon_bar(screen, detail_x + 15, y + 18, detail_w - 30, 10, def_pct, settings.BLUE)
            draw_text(screen, t("shop_defense_bonus", defense=defense), (detail_x + 15, y + 34), settings.BLUE, 16, center=False)
            y += 54
            
            effect = item_data.get("effect")
            if effect:
                effect_names = {
                    "reflect": t("effect_reflect")
                }
                draw_text(screen, t("shop_effect_label", effect=effect_names.get(effect, effect)), (detail_x + 15, y), settings.CYAN, 15, center=False)
                y += 24
        elif self.active_tab == SHOP_CONSUMABLES:
            value = item_data.get("value", 0)
            val_pct = value / 80.0
            draw_text(screen, "INTEGRAL VOLUME // RESTORATION STRENGTH", (detail_x + 15, y), settings.GRAY, 13, center=False)
            self._draw_neon_bar(screen, detail_x + 15, y + 18, detail_w - 30, 10, val_pct, settings.GREEN)
            
            effect = item_data.get("effect", "")
            effect_labels = {
                "heal": t("effect_heal", value=value),
                "atk_buff": t("effect_atk_buff", value=value),
                "def_buff": t("effect_def_buff", value=value),
                "range_buff": t("effect_range_buff", value=value),
                "max_hp_buff": t("effect_max_hp_buff", value=value)
            }
            draw_text(screen, effect_labels.get(effect, f"{effect}: {value}"), (detail_x + 15, y + 34), settings.GREEN, 16, center=False)
            y += 54
            
            scope = item_data.get("scope", "")
            scope_labels = {
                "instant": t("scope_instant"),
                "room": t("scope_room"),
                "turns": t("scope_turns", duration=item_data.get('duration', 0))
            }
            draw_text(screen, scope_labels.get(scope, scope), (detail_x + 15, y), settings.GRAY, 14, center=False)
            y += 24

        # 16. Premium full-width Buy Button
        buy_y = settings.WINDOW_HEIGHT - 85
        cost = item_data.get("cost", 0)
        sp_cost = item_data.get("sp_cost", 0)
        
        can_afford = self.game.player.gold >= cost
        sp = self.game.skill_tree.skill_points if self.game.skill_tree else 0
        if sp_cost > 0:
            can_afford = can_afford and sp >= sp_cost
            
        is_equipped = self._is_equipped(self.selected_item)

        cost_label = f"{cost}g"
        if sp_cost > 0:
            cost_label += f" + {sp_cost}SP"

        buy_rect = pygame.Rect(detail_x + 15, buy_y, detail_w - 30, 48)
        btn_overlay = pygame.Surface((buy_rect.width, buy_rect.height), pygame.SRCALPHA)

        if is_equipped:
            pygame.draw.rect(btn_overlay, (24, 25, 36, 170), (0, 0, buy_rect.width, buy_rect.height), border_radius=8)
            pygame.draw.rect(screen, (50, 70, 100), buy_rect, 1, border_radius=8)
            screen.blit(btn_overlay, buy_rect)
            draw_text(screen, "[ ALREADY OPERATIONAL IN SYSTEM ]", (buy_rect.centerx, buy_rect.centery + 1), (130, 140, 160), 14)
        elif can_afford:
            bg_val = (25, 95, 45, 230) if self.buy_button_hovered else (15, 65, 25, 200)
            border_val = (100, 255, 140) if self.buy_button_hovered else (50, 255, 100)
            
            pygame.draw.rect(btn_overlay, bg_val, (0, 0, buy_rect.width, buy_rect.height), border_radius=8)
            pygame.draw.rect(screen, border_val, buy_rect, 2 if self.buy_button_hovered else 1, border_radius=8)
            screen.blit(btn_overlay, buy_rect)
            
            lbl = f"DECRYPT THEOREM // BUY FOR {cost_label.upper()}"
            lbl_color = settings.WHITE if self.buy_button_hovered else (220, 255, 220)
            draw_text(screen, f"[ {lbl} ]", (buy_rect.centerx, buy_rect.centery + 1), lbl_color, 14)
        else:
            pygame.draw.rect(btn_overlay, (55, 16, 16, 180), (0, 0, buy_rect.width, buy_rect.height), border_radius=8)
            pygame.draw.rect(screen, (160, 45, 45), buy_rect, 1, border_radius=8)
            screen.blit(btn_overlay, buy_rect)
            draw_text(screen, f"[ INSUFFICIENT SEED CREDITS // NEED {cost_label.upper()} ]", (buy_rect.centerx, buy_rect.centery + 1), (190, 100, 100), 13)

        # 17. Flash decrypted feedback text
        if self.buy_feedback_timer > 0:
            fb_color = settings.GREEN if self.buy_success else settings.RED
            fb_text = f"// SYSTEM READOUT: {self.buy_feedback.upper()}"
            draw_text(screen, fb_text, (detail_x + 15, buy_y - 26), fb_color, 13, center=False)

    def _project_and_draw_wireframe(self, screen, cx, cy, scale_3d, dist, vertices, edges, color, angle_x, angle_y, angle_z, draw_dots=True):
        projected = []
        for x, y, z in vertices:
            cos_a, sin_a = math.cos(angle_x), math.sin(angle_x)
            ry, rz = y * cos_a - z * sin_a, y * sin_a + z * cos_a
            cos_a, sin_a = math.cos(angle_y), math.sin(angle_y)
            rx, rz = x * cos_a + rz * sin_a, -x * sin_a + rz * cos_a
            cos_a, sin_a = math.cos(angle_z), math.sin(angle_z)
            rx, ry = rx * cos_a - ry * sin_a, rx * sin_a + ry * cos_a
            
            px = int(cx + (rx * scale_3d) / (rz + dist))
            py = int(cy + (ry * scale_3d) / (rz + dist))
            projected.append((px, py))
            
        for start, end in edges:
            if 0 <= start < len(projected) and 0 <= end < len(projected):
                pygame.draw.line(screen, color, projected[start], projected[end], 2)
                
        if draw_dots:
            for px, py in projected:
                pygame.draw.circle(screen, settings.WHITE, (px, py), 3)

    def _draw_neon_bar(self, screen, x, y, w, h, pct, color):
        pygame.draw.rect(screen, (12, 13, 30, 225), (x, y, w, h), border_radius=h//2)
        pygame.draw.rect(screen, (35, 45, 75, 120), (x, y, w, h), 1, border_radius=h//2)
        
        if pct > 0:
            fill_w = int(w * min(1.0, max(0.0, pct)))
            if fill_w > 0:
                glow = pygame.Surface((fill_w, h), pygame.SRCALPHA)
                pygame.draw.rect(glow, (color[0], color[1], color[2], 90), (0, 0, fill_w, h), border_radius=h//2)
                screen.blit(glow, (x, y))
                pygame.draw.rect(screen, color, (x, y, fill_w, h), border_radius=h//2)

    def _get_item_data(self, item_id):
        if self.active_tab == SHOP_WEAPONS:
            return settings.EQUIPMENT_DATA["weapons"].get(item_id)
        elif self.active_tab == SHOP_SHIELDS:
            return settings.EQUIPMENT_DATA["shields"].get(item_id)
        else:
            return settings.CONSUMABLE_DATA.get(item_id)