import pygame

import settings
from utils import draw_text
from scenes.scene import Scene
from i18n import t


class UpgradesScene(Scene):
    overlay = True

    def __init__(self, game):
        super().__init__(game)
        self.hovered_idx = None

    def enter(self, prev_scene=None):
        self.hovered_idx = None
        self._sync_gold()

    def _sync_gold(self):
        self.game.gold = self.game.player.gold

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_u, pygame.K_ESCAPE):
                self._sync_gold()
                self.game.scene_manager.pop()
                return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)

        if event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)

    def _handle_click(self, pos):
        mx, my = pos
        panel_w = 320
        px = 20
        py = 20

        player = self.game.player
        upgrades = ["atk", "def", "hp", "range"]
        for i, utype in enumerate(upgrades):
            row_y = py + 80 + i * 70
            buy_rect = pygame.Rect(px + panel_w - 85, row_y + 17, 70, 26)
            if buy_rect.collidepoint(mx, my):
                if player.buy_upgrade(utype):
                    self.game.sfx.play("menu_select")
                    self._sync_gold()
                return

    def _update_hover(self, pos):
        self.hovered_idx = None
        mx, my = pos
        panel_w = 320
        px = 20
        py = 20

        upgrades = ["atk", "def", "hp", "range"]
        for i, utype in enumerate(upgrades):
            row_y = py + 80 + i * 70
            item_rect = pygame.Rect(px + 15, row_y, panel_w - 30, 60)
            if item_rect.collidepoint(mx, my):
                self.hovered_idx = i

    def update(self, dt):
        pass

    def draw(self, screen):
        # Draw background scene underneath
        if self.game.scene_manager.stack:
            self.game.scene_manager.stack[-1].draw(screen)
        else:
            gameplay = self.game.scene_manager.get("gameplay")
            if gameplay:
                gameplay.draw(screen)

        # Subtle dim overlay
        dim_overlay = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
        dim_overlay.fill((10, 10, 25, 120))
        screen.blit(dim_overlay, (0, 0))

        # Panel dimensions (Left aligned)
        panel_w = 320
        panel_h = 560
        px = 20
        py = 20
        player = self.game.player

        # Draw glassmorphic panel shadow/glow
        for glow_offset in range(4, 0, -1):
            glow_alpha = 15 - glow_offset * 3
            glow_surf = pygame.Surface((panel_w + glow_offset * 2, panel_h + glow_offset * 2), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (80, 100, 220, glow_alpha), (0, 0, glow_surf.get_width(), glow_surf.get_height()), border_radius=12 + glow_offset)
            screen.blit(glow_surf, (px - glow_offset, py - glow_offset))

        # Draw panel background
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((12, 14, 30, 235))
        screen.blit(panel, (px, py))
        
        # Border
        pygame.draw.rect(screen, settings.GOLD, (px, py, panel_w, panel_h), 2, border_radius=12)

        # Header Title
        draw_text(screen, t("upgrades_title"), (px + 20, py + 25), settings.WHITE, 22, center=False)
        
        tickets = getattr(player, "upgrade_tickets", 0)
        gold = player.gold
        
        # Tickets and Gold Indicators
        stats_str = t("upgrades_stats", tickets=tickets, gold=gold)
        draw_text(screen, stats_str, (px + 20, py + 50), settings.GOLD, 11, center=False)
        pygame.draw.line(screen, (60, 60, 90), (px + 15, py + 68), (px + panel_w - 15, py + 68), 1)

        # Draw Upgrades List
        upgrades = [
            ("atk", t("upgrade_atk_name"), t("upgrade_atk_desc"), settings.RED),
            ("def", t("upgrade_def_name"), t("upgrade_def_desc"), settings.BLUE),
            ("hp", t("upgrade_hp_name"), t("upgrade_hp_desc"), settings.GREEN),
            ("range", t("upgrade_range_name"), t("upgrade_range_desc"), settings.CYAN),
        ]

        for i, (utype, name, desc, color) in enumerate(upgrades):
            row_y = py + 80 + i * 70
            level = player.upgrades[utype]
            cost = player.get_upgrade_cost(utype)
            can_afford = player.gold >= cost

            card_rect = pygame.Rect(px + 15, row_y, panel_w - 30, 60)
            
            if self.hovered_idx == i:
                pygame.draw.rect(screen, (28, 30, 60), card_rect, border_radius=8)
                pygame.draw.rect(screen, color, card_rect, 2, border_radius=8)
            else:
                pygame.draw.rect(screen, (18, 20, 42), card_rect, border_radius=8)
                pygame.draw.rect(screen, (50, 50, 80), card_rect, 1, border_radius=8)

            # Left side color bar accent
            pygame.draw.rect(screen, color, (px + 15, row_y + 10, 4, 40), border_radius=2)

            # Draw Upgrade Info
            draw_text(screen, f"{name} (Lv.{level})", (px + 30, row_y + 14), color, 14, center=False)
            
            bonus_map = {"atk": 3 * level, "def": 2 * level, "hp": 15 * level, "range": level}
            draw_text(screen, f"Current Bonus: +{bonus_map[utype]}", (px + 30, row_y + 36), settings.LIGHT_GRAY, 11, center=False)

            # Buy Button
            buy_rect = pygame.Rect(px + panel_w - 85, row_y + 17, 70, 26)
            
            if tickets > 0:
                buy_color = settings.GREEN
                buy_text_color = settings.BLACK
                button_label = t("upgrades_free")
            else:
                buy_color = settings.GREEN if can_afford else settings.DARK_GRAY
                buy_text_color = settings.BLACK if can_afford else settings.GRAY
                button_label = f"{cost}g"

            bg_btn = buy_color
            pygame.draw.rect(screen, bg_btn, buy_rect, border_radius=4)
            draw_text(screen, button_label, buy_rect.center, buy_text_color, 12)

        # Draw Bottom Description/Details Box
        desc_box_rect = pygame.Rect(px + 15, py + 380, panel_w - 30, 145)
        pygame.draw.rect(screen, (10, 10, 20), desc_box_rect, border_radius=8)
        pygame.draw.rect(screen, (50, 50, 75), desc_box_rect, 1, border_radius=8)

        draw_text(screen, t("upgrades_projection_title"), (px + 25, py + 390), settings.GOLD, 11, center=False)
        pygame.draw.line(screen, (40, 40, 60), (px + 25, py + 403), (px + panel_w - 25, py + 403), 1)

        if self.hovered_idx is not None and self.hovered_idx < len(upgrades):
            utype, name, desc, color = upgrades[self.hovered_idx]
            level = player.upgrades[utype]
            cost = player.get_upgrade_cost(utype)
            
            cost_data = settings.UPGRADE_COSTS[utype]
            base_cost = cost_data["base_cost"]
            scale = cost_data["cost_scale"]
            
            formula_label = t("upgrades_formula_label", base_cost=base_cost, scale=scale)
            next_cost = int(base_cost * (scale ** (level + 1)))

            draw_text(screen, f"{name}: {desc}", (px + 25, py + 413), settings.WHITE, 11, center=False)
            draw_text(screen, t("upgrades_current_level_cost", level=level, next_cost=next_cost), (px + 25, py + 430), settings.LIGHT_GRAY, 11, center=False)
            
            # Mathematical Function graph description or representation
            draw_text(screen, t("upgrades_scaling_function"), (px + 25, py + 455), settings.CYAN, 11, center=False)
            draw_text(screen, formula_label, (px + 25, py + 472), settings.CYAN, 12, center=False)
            
            growth_txt = t("upgrades_exponential_rate", rate=int((scale - 1) * 100))
            draw_text(screen, growth_txt, (px + 25, py + 495), settings.GRAY, 10, center=False)
        else:
            draw_text(screen, t("upgrades_hover_hint"), (px + panel_w // 2, py + 450), settings.GRAY, 11)

        # Footer Instruction
        draw_text(screen, t("upgrades_close_hint"), (px + panel_w // 2, py + panel_h - 15), settings.GRAY, 11)
