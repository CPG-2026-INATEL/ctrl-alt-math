import pygame

import settings
from utils import draw_text
from scenes.scene import Scene
from i18n import t


class EquipDockScene(Scene):
    overlay = True

    def __init__(self, game):
        super().__init__(game)
        self.hovered_slot = None

    def enter(self, prev_scene=None):
        self.hovered_slot = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_e, pygame.K_ESCAPE):
                self.game.scene_manager.pop()
                return

        if event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)

    def _update_hover(self, pos):
        self.hovered_slot = None
        mx, my = pos
        panel_w = 320
        px = settings.WINDOW_WIDTH - panel_w - 20
        py = 20

        # We have 2 slots: weapon and shield
        slots = [("weapon", 0), ("shield", 90)]
        for slot_name, y_off in slots:
            slot_y = py + 80 + y_off
            slot_rect = pygame.Rect(px + 15, slot_y, panel_w - 30, 75)
            if slot_rect.collidepoint(mx, my):
                self.hovered_slot = slot_name

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

        # Panel coordinates (Right aligned)
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
        draw_text(screen, t("eq_title"), (px + 20, py + 25), settings.GOLD, 22, center=False)
        draw_text(screen, t("eq_subtitle"), (px + 20, py + 50), settings.GRAY, 11, center=False)
        pygame.draw.line(screen, (60, 60, 90), (px + 15, py + 68), (px + panel_w - 15, py + 68), 1)

        # Draw Equipment Slots
        slots = [
            ("weapon", t("eq_weapon_label"), 0, settings.ORANGE),
            ("shield", t("eq_shield_label"), 90, settings.BLUE),
        ]

        for slot_name, label, y_off, color in slots:
            slot_y = py + 80 + y_off
            slot_rect = pygame.Rect(px + 15, slot_y, panel_w - 30, 75)
            
            is_hovered = (self.hovered_slot == slot_name)
            bg = (28, 30, 60) if is_hovered else (18, 20, 42)
            border_w = 2 if is_hovered else 1
            
            pygame.draw.rect(screen, bg, slot_rect, border_radius=8)
            pygame.draw.rect(screen, color if is_hovered else (50, 50, 80), slot_rect, border_w, border_radius=8)

            # Accent bar
            pygame.draw.rect(screen, color, (px + 15, slot_y + 12, 4, 51), border_radius=2)

            # Slot label
            draw_text(screen, label, (px + 30, slot_y + 10), color, 12, center=False)

            is_weapon = slot_name == "weapon"
            data_source = settings.EQUIPMENT_DATA["weapons"] if is_weapon else settings.EQUIPMENT_DATA["shields"]
            equipped_id = player.equipment.get(slot_name)
            item_data = data_source.get(equipped_id, {})

            name = t(item_data.get("name", "eq_empty_slot"))
            draw_text(screen, name, (px + 30, slot_y + 26), settings.WHITE, 16, center=False)

            # Stats line
            if is_weapon:
                mult = item_data.get("multiplier", 1.0)
                draw_text(screen, t("eq_dmg_mult", mult=f"{mult:.1f}"), (px + 30, slot_y + 48), settings.RED, 12, center=False)
            else:
                defense = item_data.get("defense", 0)
                draw_text(screen, t("eq_base_def", defense=defense), (px + 30, slot_y + 48), settings.CYAN, 12, center=False)

        # Draw Bottom Description/Details Box
        desc_box_rect = pygame.Rect(px + 15, py + 380, panel_w - 30, 145)
        pygame.draw.rect(screen, (10, 10, 20), desc_box_rect, border_radius=8)
        pygame.draw.rect(screen, (50, 50, 75), desc_box_rect, 1, border_radius=8)

        draw_text(screen, t("eq_details_title"), (px + 25, py + 390), settings.GOLD, 11, center=False)
        pygame.draw.line(screen, (40, 40, 60), (px + 25, py + 403), (px + panel_w - 25, py + 403), 1)

        if self.hovered_slot is not None:
            slot_name = self.hovered_slot
            is_weapon = slot_name == "weapon"
            data_source = settings.EQUIPMENT_DATA["weapons"] if is_weapon else settings.EQUIPMENT_DATA["shields"]
            equipped_id = player.equipment.get(slot_name)
            item_data = data_source.get(equipped_id, {})

            desc = t(item_data.get("desc", "eq_empty_slot"))
            effect = item_data.get("effect", "Standard gear.")
            
            # Draw Description and formula
            if is_weapon:
                formula = f"Effective ATK = Base * {item_data.get('multiplier', 1.0):.1f}"
                note = "Weapon multiplier scales with upgrades directly."
            else:
                formula = f"Damage Taken = Max(0, Incoming - {item_data.get('defense', 0)})"
                note = "Shield defense lowers base damage per strike."

            draw_text(screen, t("eq_lore_prefix", desc=desc), (px + 25, py + 413), settings.WHITE, 11, center=False)
            draw_text(screen, t("eq_effect_prefix", effect=effect), (px + 25, py + 432), settings.LIGHT_GRAY, 11, center=False)
            
            draw_text(screen, t("eq_mechanics_title"), (px + 25, py + 458), settings.YELLOW, 11, center=False)
            draw_text(screen, formula, (px + 25, py + 475), settings.CYAN, 12, center=False)
            draw_text(screen, note, (px + 25, py + 495), settings.GRAY, 10, center=False)
        else:
            draw_text(screen, t("eq_hover_hint"), (px + panel_w // 2, py + 450), settings.GRAY, 11)

        # Footer Instruction
        draw_text(screen, t("eq_close_hint"), (px + panel_w // 2, py + panel_h - 15), settings.GRAY, 11)
