import pygame

import settings
from utils import draw_text
from scenes.scene import Scene
from i18n import t

SHOP_WEAPONS = 0
SHOP_SHIELDS = 1
SHOP_CONSUMABLES = 2

SHOP_TAB_LABELS = ["shop_tab_weapons", "shop_tab_shields", "shop_tab_consumables"]
SHOP_TAB_COLORS = [settings.RED, settings.BLUE, settings.GREEN]


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

    def enter(self, prev_scene=None):
        self.active_tab = SHOP_WEAPONS
        self.scroll_y = 0
        self.selected_item = None
        self.buy_feedback = ""
        self.buy_feedback_timer = 0
        self.buy_success = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_s, pygame.K_ESCAPE):
                self.game.scene_manager.pop()
                return
            if event.key == pygame.K_1:
                self.active_tab = SHOP_WEAPONS
                self.scroll_y = 0
                self.selected_item = None
            elif event.key == pygame.K_2:
                self.active_tab = SHOP_SHIELDS
                self.scroll_y = 0
                self.selected_item = None
            elif event.key == pygame.K_3:
                self.active_tab = SHOP_CONSUMABLES
                self.scroll_y = 0
                self.selected_item = None

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
        tab_w = settings.WINDOW_WIDTH // 3
        for i in range(3):
            tab_rect = pygame.Rect(i * tab_w, tab_y, tab_w, tab_h)
            if tab_rect.collidepoint(mx, my):
                self.active_tab = i
                self.scroll_y = 0
                self.selected_item = None
                return

        list_x = 20
        list_w = settings.WINDOW_WIDTH // 2 - 40
        sy = int(self.scroll_y)
        items = self._get_items()
        for i, item_data in enumerate(items):
            row_y = 50 + i * 65 - sy
            row_rect = pygame.Rect(list_x, row_y, list_w, 58)
            if row_rect.collidepoint(mx, my):
                self.selected_item = item_data["id"]
                return

        detail_x = settings.WINDOW_WIDTH // 2 + 20
        detail_w = settings.WINDOW_WIDTH // 2 - 40
        buy_y = settings.WINDOW_HEIGHT - 80
        buy_rect = pygame.Rect(detail_x, buy_y, 120, 32)
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
                self.buy_feedback_timer = 1.5
                self.buy_success = False
                return
            cost = data.get("cost", 0)
            sp_cost = data.get("sp_cost", 0)
            sp = self.game.skill_tree.skill_points if self.game.skill_tree else 0
            if player.gold < cost or sp < sp_cost:
                self.buy_feedback = t("shop_insufficient_funds")
                self.buy_feedback_timer = 1.5
                self.buy_success = False
                return
            player.gold -= cost
            if sp_cost > 0 and self.game.skill_tree:
                self.game.skill_tree.skill_points -= sp_cost
            player.equipment["weapon"] = item_id
            self.buy_feedback = t("shop_equipped_feedback", name=data['name'])
            self.buy_feedback_timer = 1.5
            self.buy_success = True
        elif self.active_tab == SHOP_SHIELDS:
            data = settings.EQUIPMENT_DATA["shields"].get(item_id)
            if not data:
                return
            if player.equipment.get("shield") == item_id:
                self.buy_feedback = t("shop_already_equipped")
                self.buy_feedback_timer = 1.5
                self.buy_success = False
                return
            cost = data.get("cost", 0)
            sp_cost = data.get("sp_cost", 0)
            sp = self.game.skill_tree.skill_points if self.game.skill_tree else 0
            if player.gold < cost or sp < sp_cost:
                self.buy_feedback = t("shop_insufficient_funds")
                self.buy_feedback_timer = 1.5
                self.buy_success = False
                return
            player.gold -= cost
            if sp_cost > 0 and self.game.skill_tree:
                self.game.skill_tree.skill_points -= sp_cost
            player.equipment["shield"] = item_id
            self.buy_feedback = t("shop_equipped_feedback", name=data['name'])
            self.buy_feedback_timer = 1.5
            self.buy_success = True
        elif self.active_tab == SHOP_CONSUMABLES:
            data = settings.CONSUMABLE_DATA.get(item_id)
            if not data:
                return
            cost = data.get("cost", 0)
            sp_cost = data.get("sp_cost", 0)
            sp = self.game.skill_tree.skill_points if self.game.skill_tree else 0
            if player.gold < cost or sp < sp_cost:
                self.buy_feedback = t("shop_insufficient_funds")
                self.buy_feedback_timer = 1.5
                self.buy_success = False
                return
            player.gold -= cost
            if sp_cost > 0 and self.game.skill_tree:
                self.game.skill_tree.skill_points -= sp_cost
            for inv_item in player.inventory:
                if inv_item["id"] == item_id:
                    inv_item["count"] = inv_item.get("count", 1) + 1
                    self.buy_feedback = t("shop_added_feedback", name=data['name'])
                    self.buy_feedback_timer = 1.5
                    self.buy_success = True
                    return
            player.inventory.append({"id": item_id, "count": 1})
            self.buy_feedback = t("shop_purchased_feedback", name=data['name'])
            self.buy_feedback_timer = 1.5
            self.buy_success = True
        game = self.game
        game.gold = player.gold

    def _update_hover(self, pos):
        pass

    def _get_items(self):
        if self.active_tab == SHOP_WEAPONS:
            return [{"id": wid, **settings.EQUIPMENT_DATA["weapons"][wid]} for wid in settings.SHOP_ITEMS["weapons"]]
        elif self.active_tab == SHOP_SHIELDS:
            return [{"id": sid, **settings.EQUIPMENT_DATA["shields"][sid]} for sid in settings.SHOP_ITEMS["shields"]]
        else:
            return [{"id": cid, **settings.CONSUMABLE_DATA[cid]} for cid in settings.SHOP_ITEMS["consumables"]]

    def _get_max_scroll(self):
        items = self._get_items()
        total_h = len(items) * 65
        visible_h = settings.WINDOW_HEIGHT - 120
        return max(0, total_h - visible_h)

    def update(self, dt):
        if self.buy_feedback_timer > 0:
            self.buy_feedback_timer -= dt

    def draw(self, screen):
        overlay = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 30, 230))
        screen.blit(overlay, (0, 0))

        self._draw_tabs(screen)

        list_x = 20
        list_w = settings.WINDOW_WIDTH // 2 - 40
        clip_rect = pygame.Rect(0, 45, settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT - 55)
        screen.set_clip(clip_rect)
        self._draw_list(screen, list_x, list_w)

        screen.set_clip(None)

        detail_x = settings.WINDOW_WIDTH // 2 + 20
        self._draw_detail(screen, detail_x)

        draw_text(screen, t("shop_gold", gold=self.game.player.gold), (settings.WINDOW_WIDTH // 2 + 30, settings.WINDOW_HEIGHT - 30), settings.GOLD, 14, center=False)
        sp = self.game.skill_tree.skill_points if self.game.skill_tree else 0
        draw_text(screen, f"SP: {sp}", (settings.WINDOW_WIDTH // 2 + 160, settings.WINDOW_HEIGHT - 30), settings.CYAN, 14, center=False)

    def _draw_tabs(self, screen):
        tab_y = 10
        tab_h = 30
        tab_w = settings.WINDOW_WIDTH // 3
        for i in range(3):
            tab_rect = pygame.Rect(i * tab_w, tab_y, tab_w, tab_h)
            is_active = (i == self.active_tab)
            bg_color = (35, 40, 70, 230) if is_active else (10, 10, 25, 180)
            
            tab_surf = pygame.Surface((tab_w, tab_h), pygame.SRCALPHA)
            pygame.draw.rect(tab_surf, bg_color, (0, 0, tab_w, tab_h), border_radius=4)
            screen.blit(tab_surf, tab_rect)
            
            border_color = SHOP_TAB_COLORS[i] if is_active else (50, 50, 70)
            pygame.draw.rect(screen, border_color, tab_rect, 2 if is_active else 1, border_radius=4)
            
            if is_active:
                pygame.draw.line(screen, SHOP_TAB_COLORS[i], (i * tab_w + 15, tab_y + tab_h - 3), ((i + 1) * tab_w - 15, tab_y + tab_h - 3), 3)

            label_font = pygame.font.Font(None, 18)
            label = label_font.render(t(SHOP_TAB_LABELS[i]), True, SHOP_TAB_COLORS[i] if is_active else (120, 120, 140))
            screen.blit(label, (tab_rect.centerx - label.get_width() // 2, tab_rect.centery - label.get_height() // 2))

    def _draw_list(self, screen, list_x, list_w):
        draw_text(screen, t("shop_title"), (list_x + 10, 48), settings.WHITE, 20, center=False)

        items = self._get_items()
        sy = int(self.scroll_y)
        tab_color = SHOP_TAB_COLORS[self.active_tab]

        for i, item_data in enumerate(items):
            row_y = 75 + i * 65 - sy
            if row_y < 40 or row_y > settings.WINDOW_HEIGHT:
                continue

            row_rect = pygame.Rect(list_x, row_y, list_w, 58)
            is_selected = self.selected_item == item_data["id"]
            is_equipped = self._is_equipped(item_data["id"])

            bg = (30, 30, 55) if is_selected else (20, 20, 40) if i % 2 == 0 else (15, 15, 35)
            pygame.draw.rect(screen, bg, row_rect, border_radius=6)
            if is_selected:
                pygame.draw.rect(screen, tab_color, row_rect, 2, border_radius=6)

            name_color = settings.WHITE if not is_equipped else (100, 100, 100)
            draw_text(screen, t(item_data.get("name", item_data["id"])), (list_x + 15, row_y + 8), name_color, 16, center=False)

            cost = item_data.get("cost", 0)
            sp_cost = item_data.get("sp_cost", 0)
            cost_str = f"{cost}g"
            if sp_cost > 0:
                cost_str += f" + {sp_cost}SP"
            can_afford = self.game.player.gold >= cost
            sp = self.game.skill_tree.skill_points if self.game.skill_tree else 0
            if sp_cost > 0:
                can_afford = can_afford and sp >= sp_cost
            cost_color = settings.GOLD if can_afford else (100, 100, 100)
            draw_text(screen, cost_str, (list_x + 15, row_y + 30), cost_color, 13, center=False)

            if is_equipped:
                draw_text(screen, t("shop_equipped_status"), (list_x + list_w - 90, row_y + 20), settings.CYAN, 12, center=False)

    def _is_equipped(self, item_id):
        if self.active_tab == SHOP_WEAPONS:
            return self.game.player.equipment.get("weapon") == item_id
        elif self.active_tab == SHOP_SHIELDS:
            return self.game.player.equipment.get("shield") == item_id
        return False

    def _draw_detail(self, screen, detail_x):
        detail_w = settings.WINDOW_WIDTH // 2 - 40

        if not self.selected_item:
            draw_text(screen, t("shop_select_prompt"), (detail_x + 10, 80), settings.GRAY, 16, center=False)
            return

        item_data = self._get_item_data(self.selected_item)
        if not item_data:
            return

        y = 55
        draw_text(screen, t(item_data.get("name", self.selected_item)), (detail_x + 10, y), settings.WHITE, 22, center=False)
        y += 35

        desc = item_data.get("desc", "")
        draw_text(screen, t(desc), (detail_x + 10, y), settings.LIGHT_GRAY, 14, center=False)
        y += 30

        pygame.draw.line(screen, (60, 60, 80), (detail_x + 10, y), (detail_x + detail_w - 10, y), 1)
        y += 10

        if self.active_tab == SHOP_WEAPONS:
            mult = item_data.get("multiplier", 1.0)
            draw_text(screen, t("shop_atk_multiplier", mult=f"{mult:.2f}"), (detail_x + 10, y), settings.RED, 16, center=False)
            y += 22
            effect = item_data.get("effect")
            if effect:
                effect_names = {
                    "burn": t("effect_burn"),
                    "slow": t("effect_slow"),
                    "stun": t("effect_stun"),
                    "aoe": t("effect_aoe"),
                    "poison": t("effect_poison")
                }
                draw_text(screen, t("shop_effect_label", effect=effect_names.get(effect, effect)), (detail_x + 10, y), settings.ORANGE, 14, center=False)
                y += 20
        elif self.active_tab == SHOP_SHIELDS:
            defense = item_data.get("defense", 0)
            draw_text(screen, t("shop_defense_bonus", defense=defense), (detail_x + 10, y), settings.BLUE, 16, center=False)
            y += 22
            effect = item_data.get("effect")
            if effect:
                effect_names = {
                    "reflect": t("effect_reflect")
                }
                draw_text(screen, t("shop_effect_label", effect=effect_names.get(effect, effect)), (detail_x + 10, y), settings.CYAN, 14, center=False)
                y += 20
        elif self.active_tab == SHOP_CONSUMABLES:
            value = item_data.get("value", 0)
            effect = item_data.get("effect", "")
            effect_labels = {
                "heal": t("effect_heal", value=value),
                "atk_buff": t("effect_atk_buff", value=value),
                "def_buff": t("effect_def_buff", value=value),
                "range_buff": t("effect_range_buff", value=value),
                "max_hp_buff": t("effect_max_hp_buff", value=value)
            }
            draw_text(screen, effect_labels.get(effect, f"{effect}: {value}"), (detail_x + 10, y), settings.GREEN, 16, center=False)
            y += 22
            scope = item_data.get("scope", "")
            scope_labels = {
                "instant": t("scope_instant"),
                "room": t("scope_room"),
                "turns": t("scope_turns", duration=item_data.get('duration', 0))
            }
            draw_text(screen, scope_labels.get(scope, scope), (detail_x + 10, y), settings.GRAY, 13, center=False)
            y += 20

        buy_y = settings.WINDOW_HEIGHT - 80
        cost = item_data.get("cost", 0)
        sp_cost = item_data.get("sp_cost", 0)
        can_afford = self.game.player.gold >= cost
        sp = self.game.skill_tree.skill_points if self.game.skill_tree else 0
        if sp_cost > 0:
            can_afford = can_afford and sp >= sp_cost
        is_equipped = self._is_equipped(self.selected_item)

        if is_equipped:
            pygame.draw.rect(screen, (60, 60, 60), pygame.Rect(detail_x, buy_y, 120, 32), border_radius=6)
            draw_text(screen, t("shop_equipped_status"), (detail_x + 12, buy_y + 8), settings.GRAY, 14, center=False)
        elif can_afford:
            pygame.draw.rect(screen, settings.GREEN, pygame.Rect(detail_x, buy_y, 120, 32), border_radius=6)
            cost_label = f"{cost}g"
            if sp_cost > 0:
                cost_label += f" +{sp_cost}SP"
            draw_text(screen, t("shop_buy_button", cost=cost_label), (detail_x + 8, buy_y + 8), settings.WHITE, 12, center=False)
        else:
            pygame.draw.rect(screen, (60, 30, 30), pygame.Rect(detail_x, buy_y, 120, 32), border_radius=6)
            draw_text(screen, f"{cost}g", (detail_x + 12, buy_y + 8), (150, 80, 80), 13, center=False)

        if self.buy_feedback_timer > 0:
            fb_color = settings.GREEN if self.buy_success else settings.RED
            draw_text(screen, self.buy_feedback, (detail_x, buy_y - 25), fb_color, 14, center=False)

    def _get_item_data(self, item_id):
        if self.active_tab == SHOP_WEAPONS:
            return settings.EQUIPMENT_DATA["weapons"].get(item_id)
        elif self.active_tab == SHOP_SHIELDS:
            return settings.EQUIPMENT_DATA["shields"].get(item_id)
        else:
            return settings.CONSUMABLE_DATA.get(item_id)