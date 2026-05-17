import pygame

import settings
from utils import draw_text
from scenes.scene import Scene
from i18n import t


class InventoryDockScene(Scene):
    overlay = True

    def __init__(self, game):
        super().__init__(game)
        self.hovered_idx = None

    def enter(self, prev_scene=None):
        self.hovered_idx = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_i, pygame.K_ESCAPE):
                self.game.scene_manager.pop()
                return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)

        if event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)

    def _handle_click(self, pos):
        mx, my = pos
        panel_w = 320
        panel_h = 560
        px = settings.WINDOW_WIDTH - panel_w - 20
        py = 20

        player = self.game.player
        for i, item in enumerate(player.inventory):
            row_y = py + 80 + i * 70
            use_rect = pygame.Rect(px + panel_w - 85, row_y + 17, 60, 26)
            if use_rect.collidepoint(mx, my):
                item_data = settings.CONSUMABLE_DATA.get(item.get("id"), {})
                if item_data:
                    player.use_consumable(item["id"])
                    self.game.sfx.play("menu_select")
                    self.game.gold = player.gold
                    return

    def _update_hover(self, pos):
        self.hovered_idx = None
        mx, my = pos
        panel_w = 320
        panel_h = 560
        px = settings.WINDOW_WIDTH - panel_w - 20
        py = 20

        player = self.game.player
        for i, item in enumerate(player.inventory):
            row_y = py + 80 + i * 70
            item_rect = pygame.Rect(px + 15, row_y, panel_w - 30, 60)
            if item_rect.collidepoint(mx, my):
                self.hovered_idx = i

    def update(self, dt):
        pass

    def draw(self, screen):
        gameplay = self.game.scene_manager.get("gameplay")
        if gameplay:
            gameplay.draw(screen)

        # A beautiful subtle dim over the arena
        dim_overlay = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
        dim_overlay.fill((10, 10, 25, 120))
        screen.blit(dim_overlay, (0, 0))

        # Panel coordinates
        panel_w = 320
        panel_h = 560
        px = settings.WINDOW_WIDTH - panel_w - 20
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
        pygame.draw.rect(screen, (80, 100, 220), (px, py, panel_w, panel_h), 2, border_radius=12)

        # Header Title
        draw_text(screen, t("inv_title"), (px + 20, py + 25), settings.GOLD, 22, center=False)
        draw_text(screen, t("inv_subtitle"), (px + 20, py + 50), settings.GRAY, 11, center=False)
        pygame.draw.line(screen, (60, 60, 90), (px + 15, py + 68), (px + panel_w - 15, py + 68), 1)

        # Draw Items List
        if not player.inventory:
            draw_text(screen, t("inv_empty"), (px + panel_w // 2, py + 200), settings.GRAY, 16)
        else:
            for i, item in enumerate(player.inventory):
                row_y = py + 80 + i * 70
                item_data = settings.CONSUMABLE_DATA.get(item.get("id"), {})
                color = item_data.get("color", settings.GRAY)
                name = item_data.get("name", item.get("id", "?"))
                count = item.get("count", 0)

                card_rect = pygame.Rect(px + 15, row_y, panel_w - 30, 60)
                
                # Check hover state styling
                if self.hovered_idx == i:
                    pygame.draw.rect(screen, (28, 30, 60), card_rect, border_radius=8)
                    pygame.draw.rect(screen, color, card_rect, 2, border_radius=8)
                else:
                    pygame.draw.rect(screen, (18, 20, 42), card_rect, border_radius=8)
                    pygame.draw.rect(screen, (50, 50, 80), card_rect, 1, border_radius=8)

                # Left side item color bar accent
                pygame.draw.rect(screen, color, (px + 15, row_y + 10, 4, 40), border_radius=2)

                draw_text(screen, name, (px + 30, row_y + 12), color, 14, center=False)
                draw_text(screen, f"x{count}", (px + 30, row_y + 36), settings.LIGHT_GRAY, 12, center=False)

                # Use Button
                use_rect = pygame.Rect(px + panel_w - 85, row_y + 17, 60, 26)
                bg_btn = (40, 120, 50) if self.hovered_idx == i else (30, 75, 35)
                pygame.draw.rect(screen, bg_btn, use_rect, border_radius=4)
                draw_text(screen, t("inv_use_button"), use_rect.center, settings.WHITE, 12)

        # Draw Bottom Description/Details Box
        desc_box_rect = pygame.Rect(px + 15, py + 415, panel_w - 30, 110)
        pygame.draw.rect(screen, (10, 10, 20), desc_box_rect, border_radius=8)
        pygame.draw.rect(screen, (50, 50, 75), desc_box_rect, 1, border_radius=8)

        draw_text(screen, t("inv_details_title"), (px + 25, py + 425), settings.GOLD, 11, center=False)
        pygame.draw.line(screen, (40, 40, 60), (px + 25, py + 438), (px + panel_w - 25, py + 438), 1)

        if self.hovered_idx is not None and self.hovered_idx < len(player.inventory):
            hovered_item = player.inventory[self.hovered_idx]
            item_data = settings.CONSUMABLE_DATA.get(hovered_item.get("id"), {})
            desc = item_data.get("desc", "")
            effect = item_data.get("effect", "")
            
            # Simple text wrap / draw for description
            if len(desc) > 36:
                words = desc.split(' ')
                line1, line2 = "", ""
                for word in words:
                    if len(line1 + " " + word) <= 36:
                        line1 = (line1 + " " + word).strip()
                    else:
                        line2 = (line2 + " " + word).strip()
                draw_text(screen, line1, (px + 25, py + 448), settings.LIGHT_GRAY, 11, center=False)
                if line2:
                    draw_text(screen, line2, (px + 25, py + 462), settings.LIGHT_GRAY, 11, center=False)
            else:
                draw_text(screen, desc, (px + 25, py + 448), settings.LIGHT_GRAY, 11, center=False)

            # Mathematical metadata if present
            if effect:
                formula_label = t("inv_effect_formula", effect=effect)
                draw_text(screen, formula_label, (px + 25, py + 482), settings.CYAN, 10, center=False)
        else:
            draw_text(screen, t("inv_hover_hint"), (px + panel_w // 2, py + 460), settings.GRAY, 11)

        # Footer Instruction
        draw_text(screen, t("inv_close_hint"), (px + panel_w // 2, py + panel_h - 15), settings.GRAY, 11)
