import pygame

import settings
from utils import draw_text
from scenes.scene import Scene


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
        panel_w = 340
        panel_h = self._panel_height()
        px = (settings.WINDOW_WIDTH - panel_w) // 2
        py = (settings.WINDOW_HEIGHT - panel_h) // 2

        player = self.game.player
        for i, item in enumerate(player.inventory):
            row_y = py + 60 + i * 50
            use_rect = pygame.Rect(px + panel_w - 65, row_y + 12, 52, 24)
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
        panel_w = 340
        panel_h = self._panel_height()
        px = (settings.WINDOW_WIDTH - panel_w) // 2
        py = (settings.WINDOW_HEIGHT - panel_h) // 2

        player = self.game.player
        for i, item in enumerate(player.inventory):
            row_y = py + 60 + i * 50
            item_rect = pygame.Rect(px + 10, row_y, panel_w - 20, 46)
            if item_rect.collidepoint(mx, my):
                self.hovered_idx = i

    def _panel_height(self):
        count = len(self.game.player.inventory)
        if count == 0:
            return 180
        return max(180, 80 + count * 50)

    def update(self, dt):
        pass

    def draw(self, screen):
        gameplay = self.game.scene_manager.get("gameplay")
        if gameplay:
            gameplay.draw(screen)

        dim_overlay = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
        dim_overlay.fill((10, 10, 25, 160))
        screen.blit(dim_overlay, (0, 0))
        panel_w = 340
        panel_h = self._panel_height()
        px = (settings.WINDOW_WIDTH - panel_w) // 2
        py = (settings.WINDOW_HEIGHT - panel_h) // 2

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((8, 8, 24, 240))
        screen.blit(panel, (px, py))
        pygame.draw.rect(screen, (80, 80, 120), (px, py, panel_w, panel_h), 2, border_radius=8)

        draw_text(screen, "INVENTORY", (px + panel_w // 2, py + 20), settings.WHITE, 20)
        pygame.draw.line(screen, (60, 60, 90), (px + 15, py + 42), (px + panel_w - 15, py + 42), 1)

        if not player.inventory:
            draw_text(screen, "Vazio", (px + panel_w // 2, py + panel_h // 2), settings.GRAY, 16)
            return

        for i, item in enumerate(player.inventory):
            row_y = py + 60 + i * 50
            item_data = settings.CONSUMABLE_DATA.get(item.get("id"), {})
            color = item_data.get("color", settings.GRAY)
            name = item_data.get("name", item.get("id", "?"))
            count = item.get("count", 0)
            desc = item_data.get("desc", "")
            effect = item_data.get("effect", "")

            if self.hovered_idx == i:
                hover_rect = pygame.Rect(px + 8, row_y, panel_w - 16, 46)
                pygame.draw.rect(screen, (30, 30, 50), hover_rect, border_radius=4)

            draw_text(screen, name, (px + 18, row_y + 8), color, 15, center=False)
            draw_text(screen, f"x{count}", (px + 18, row_y + 28), settings.GRAY, 12, center=False)

            use_rect = pygame.Rect(px + panel_w - 65, row_y + 12, 52, 24)
            bg = (40, 100, 40) if self.hovered_idx == i else (30, 60, 30)
            pygame.draw.rect(screen, bg, use_rect, border_radius=4)
            draw_text(screen, "Usar", use_rect.center, settings.WHITE, 12)

            if self.hovered_idx == i and desc:
                draw_text(screen, desc, (px + panel_w // 2, row_y + 44), settings.LIGHT_GRAY, 11)

        draw_text(screen, "I/ESC fechar", (px + panel_w // 2, py + panel_h - 14), settings.GRAY, 11)
