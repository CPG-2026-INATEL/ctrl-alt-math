import pygame
import math
import settings
from utils import draw_text
from i18n import t

class GameplayHUD:
    def __init__(self, scene, renderer):
        self.scene = scene
        self.renderer = renderer
        self.game = scene.game

    def draw_cursor_info(self, screen):
        scene = self.scene
        game = self.game

        if scene.state not in ("PLAYER_INPUT", "PLAYER_ACTION_SELECT"):
            return

        pc = game.player.col
        pr = game.player.row
        cc = scene.cursor_col
        cr = scene.cursor_row
        dx = cc - pc
        dy = cr - pr
        dist = abs(dx) + abs(dy)
        eucl = math.sqrt(dx * dx + dy * dy)

        is_pitagoras = (scene.state == "PLAYER_ACTION_SELECT" and scene.selected_skill == "pitagoras")
        is_reflexao = (scene.state == "PLAYER_ACTION_SELECT" and scene.selected_skill == "reflexao")

        # Glassmorphic Card Settings
        card_w = 280
        card_h = 245 if is_pitagoras else (225 if is_reflexao else 205)
        card_x = settings.WINDOW_WIDTH - card_w - 20
        if card_x < 0:
            card_x = 10
        card_y = settings.ARENA_OFFSET_Y + 5

        # Render glassmorphic card shadow / glow layers
        for glow_offset in range(3, 0, -1):
            glow_alpha = 10 - glow_offset * 2
            glow_surf = pygame.Surface((card_w + glow_offset * 2, card_h + glow_offset * 2), pygame.SRCALPHA)
            if is_pitagoras:
                glow_color = (255, 215, 0, glow_alpha)
            elif is_reflexao:
                glow_color = (0, 255, 255, glow_alpha)
            else:
                glow_color = (80, 100, 220, glow_alpha)
            pygame.draw.rect(glow_surf, glow_color, (0, 0, glow_surf.get_width(), glow_surf.get_height()), border_radius=10 + glow_offset)
            screen.blit(glow_surf, (card_x - glow_offset, card_y - glow_offset))

        # Main glass backdrop surface
        card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        card_surf.fill((8, 10, 22, 220))  # Ultra-dark translucent blue-black
        
        if is_pitagoras:
            border_color = (255, 215, 0, 160)
        elif is_reflexao:
            border_color = (0, 255, 255, 160)
        else:
            border_color = (80, 100, 220, 160)
            
        pygame.draw.rect(card_surf, border_color, (0, 0, card_w, card_h), 1, border_radius=10)
        screen.blit(card_surf, (card_x, card_y))

        # Header Title
        title_font = pygame.font.Font(None, 28)
        if is_pitagoras:
            title_text = "PYTHAGOREAN SCAN"
            title_color = settings.YELLOW
        elif is_reflexao:
            title_text = "REFLEXAO SCAN"
            title_color = settings.CYAN
        else:
            title_text = "COORDINATE ANALYZER"
            title_color = settings.CYAN

        title_img = title_font.render(title_text, True, title_color)
        screen.blit(title_img, (card_x + 12, card_y + 8))

        # Divider line
        pygame.draw.line(screen, (50, 55, 80), (card_x + 10, card_y + 32), (card_x + card_w - 10, card_y + 32), 1)

        # Standard lines
        font = pygame.font.Font(None, 24)
        
        label_color = settings.LIGHT_GRAY
        value_color = settings.WHITE

        lines = [
            (f"v = ({dx:+d}, {dy:+d})", label_color),
            (f"|v| = {dist}", value_color),
        ]

        if dist > 0:
            lines.append((f"||v|| = {eucl:.2f}", settings.YELLOW))

        # Get tile name
        tile_type = scene.grid.tile_types.get((cc, cr), 0)
        tile_name = "LOW"
        if tile_type == -1:
            tile_name = "HOLE"
        elif tile_type in (16, 61):
            tile_name = "HIGH"
        elif tile_type in (27, 11, 25, 24):
            tile_name = "STAIRS"
        lines.append((f"Tile: {tile_name}", settings.GRAY))

        # Reachable check
        reachable = scene.grid.get_reachable_cells(
            pc,
            pr,
            game.player.move_range,
            extra_blocked=scene._other_player_occupied_cells(game.player),
        )
        can_reach = (cc, cr) in reachable or (cc, cr) == (pc, pr)
        lines.append(("Reachable" if can_reach else "Blocked",
                       settings.GREEN if can_reach else settings.RED))

        # Render lines inside card
        text_y = card_y + 38
        for text, color in lines:
            img = font.render(text, True, color)
            screen.blit(img, (card_x + 12, text_y))
            text_y += 24

        # Draw formulas/debug at the bottom of the card with bigger text
        formula_font = pygame.font.Font(None, 26)
        if scene.state == "PLAYER_INPUT" and scene.show_move_range and (cc, cr) in reachable:
            move_label = formula_font.render(f"dpos({dx:+d},{dy:+d}) d={dist}", True, settings.BLUE)
            screen.blit(move_label, (card_x + 12, text_y + 4))

        if scene.state == "PLAYER_ACTION_SELECT":
            if scene.selected_skill == "pitagoras":
                pygame.draw.line(screen, (70, 70, 40), (card_x + 10, text_y + 2), (card_x + card_w - 10, text_y + 2), 1)
                text_y += 8
                formula_label = formula_font.render("a² + b² = c²", True, settings.YELLOW)
                value_label = formula_font.render(f"c = {eucl:.2f}", True, settings.GOLD)
                screen.blit(formula_label, (card_x + 12, text_y))
                screen.blit(value_label, (card_x + 12, text_y + 22))
            elif scene.selected_skill == "reflexao":
                pygame.draw.line(screen, (40, 70, 70), (card_x + 10, text_y + 2), (card_x + card_w - 10, text_y + 2), 1)
                text_y += 8
                formula_label = formula_font.render("theta_i = theta_r (reflect)", True, settings.CYAN)
                screen.blit(formula_label, (card_x + 12, text_y))

    def draw_turn_hud(self, screen):
        scene = self.scene
        game = self.game

        bar_y = settings.WINDOW_HEIGHT - settings.UI_BAR_HEIGHT
        
        # 1. Base bar panel: Futuristic dark-blue matte-glass style
        pygame.draw.rect(screen, (10, 12, 22), (0, bar_y, settings.WINDOW_WIDTH, settings.UI_BAR_HEIGHT))
        # Top neon border line
        pygame.draw.line(screen, (30, 180, 220), (0, bar_y), (settings.WINDOW_WIDTH, bar_y), 2)
        
        panel_y = bar_y + 6
        panel_h = 98

        # --- DYNAMIC PANEL WIDTHS ---
        total_w = settings.WINDOW_WIDTH
        edge_padding = 10
        gap = 10
        available_w = total_w - 2 * edge_padding - 4 * gap

        # Compute dynamic proportional widths
        w1 = int(available_w * 0.23)
        w2 = int(available_w * 0.18)
        w3 = int(available_w * 0.11)
        w4 = int(available_w * 0.28)
        w5 = available_w - (w1 + w2 + w3 + w4)  # Take all remaining space on the right

        # X coordinates
        x1 = edge_padding
        x2 = x1 + w1 + gap
        x3 = x2 + w2 + gap
        x4 = x3 + w3 + gap
        x5 = x4 + w4 + gap

        # Glassmorphic panels helper
        def draw_hud_panel(x, w, title=None, title_color=settings.GOLD):
            s = pygame.Surface((w, panel_h), pygame.SRCALPHA)
            pygame.draw.rect(s, (18, 22, 38, 220), (0, 0, w, panel_h), border_radius=6)
            pygame.draw.rect(s, (60, 85, 115, 120), (0, 0, w, panel_h), 1, border_radius=6)
            screen.blit(s, (x, panel_y))
            if title:
                draw_text(screen, title.upper(), (x + 8, panel_y + 8), title_color, 16, center=False)

        current_player = game.player
        hp_pct = current_player.hp / current_player.get_max_hp()
        rigor_pct = current_player.rigor / current_player.max_rigor
        entropy_pct = game.entropy / settings.MAX_ENTROPY
        exp_pct = current_player.exp / current_player.next_level_exp

        # --- PANEL 1: STATUS ---
        draw_hud_panel(x1, w1)
        player_label = scene._player_label(scene.active_player_idx)
        draw_text(screen, f"{player_label}  |  LVL {current_player.level}", (x1 + 8, panel_y + 7), settings.CYAN, 15, center=False)
        
        bar_w = w1 - 16
        hp_color = settings.GREEN if hp_pct > 0.5 else settings.ORANGE if hp_pct > 0.25 else settings.RED
        self.renderer._draw_bar_sleek(screen, x1 + 8, panel_y + 22, bar_w, 10, hp_pct, hp_color, (45, 15, 15))
        draw_text(screen, f"HP: {current_player.hp}/{current_player.get_max_hp()}", (x1 + w1 // 2, panel_y + 27), settings.WHITE, 13)

        self.renderer._draw_bar_sleek(screen, x1 + 8, panel_y + 40, bar_w, 10, rigor_pct, settings.BLUE, (15, 15, 45))
        draw_text(screen, f"{t('rigor')}: {current_player.rigor:.0f}/{current_player.max_rigor}", (x1 + w1 // 2, panel_y + 45), settings.WHITE, 13)

        entropy_color = settings.COLOR_ENTROPY_BAR if entropy_pct < 0.75 else settings.RED
        self.renderer._draw_bar_sleek(screen, x1 + 8, panel_y + 58, bar_w, 10, entropy_pct, entropy_color, (35, 10, 40))
        draw_text(screen, f"{t('entropy')}: {game.entropy:.0f}/{settings.MAX_ENTROPY}", (x1 + w1 // 2, panel_y + 63), settings.WHITE, 13)

        self.renderer._draw_bar_sleek(screen, x1 + 8, panel_y + 76, bar_w, 10, exp_pct, settings.GOLD, (30, 25, 10))
        draw_text(screen, f"EXP: {current_player.exp}/{current_player.next_level_exp} ({int(exp_pct*100)}%)", (x1 + w1 // 2, panel_y + 81), settings.WHITE, 12)

        # --- PANEL 2: COMBAT STATS ---
        draw_hud_panel(x2, w2, t("stats"), settings.GOLD)
        col1_x = x2 + 8
        col2_x = x2 + w2 // 2 + 4
        
        draw_text(screen, f"ATK: {current_player.get_attack_damage()}", (col1_x, panel_y + 22), settings.CYAN, 15, center=False)
        draw_text(screen, f"DEF: {current_player.get_defense()}", (col2_x, panel_y + 22), settings.CYAN, 15, center=False)
        
        draw_text(screen, f"CRIT: {int(settings.PLAYER_CRIT_CHANCE * 100)}%", (col1_x, panel_y + 39), settings.GOLD, 15, center=False)
        draw_text(screen, f"MULT: x{settings.PLAYER_CRIT_MULTIPLIER:.1f}", (col2_x, panel_y + 39), settings.GOLD, 15, center=False)
        
        sp_points = game.skill_tree.skill_points if game.skill_tree else 0
        draw_text(screen, f"GOLD: {current_player.gold}g", (col1_x, panel_y + 56), settings.GOLD, 15, center=False)
        draw_text(screen, f"SP: {sp_points}", (col2_x, panel_y + 56), settings.CYAN, 15, center=False)
        
        if len(scene.players) > 1:
            p1 = scene.players[0]
            p2 = scene.players[1]
            draw_text(screen, f"P1 HP: {p1.hp}/{p1.max_hp}", (col1_x, panel_y + 76), settings.CYAN, 14, center=False)
            draw_text(screen, f"P2 HP: {p2.hp}/{p2.max_hp}", (col2_x, panel_y + 76), settings.PURPLE, 14, center=False)
        else:
            draw_text(screen, f"DIFFICULTY: {settings.DIFFICULTY.upper()}", (x2 + w2 // 2, panel_y + 76), settings.LIGHT_GRAY, 14)

        # --- PANEL 3: GAME STATE & TURN ---
        draw_hud_panel(x3, w3)
        draw_text(screen, f"TURN {scene.turn_manager.turn_number}", (x3 + w3 // 2, panel_y + 12), settings.WHITE, 22)
        
        phase_text = "PLAYER MOVE"
        phase_symbol = "\u0394x"
        phase_color = settings.CYAN
        if scene.state in ("PLAYER_ACTION_SELECT", "RESOLVE_ACTION"):
            phase_text = "PLAYER ATTACK"
            phase_symbol = "f'(x)"
            phase_color = settings.RED
        elif scene.state == "RESOLVE_MOVE":
            phase_text = "PLAYER MOVE"
            phase_symbol = "\u0394x"
            phase_color = settings.CYAN
        elif scene.state == "LOCK_INDICATORS":
            phase_text = "LOCK AIM"
            phase_symbol = "!"
            phase_color = settings.ORANGE
        elif scene.state == "ENEMY_TURN":
            phase_color = settings.RED
            if scene.enemy_phase == "ATTACK":
                phase_text = "ENEMY ATTACK"
                phase_symbol = "!x"
            else:
                phase_text = "ENEMY MOVE"
                phase_symbol = "Ax"
        elif scene.state == "TURN_END":
            phase_text = "TURN END"
            phase_symbol = "="
            phase_color = settings.ORANGE
        elif scene.state == "VICTORY_TRANSITION":
            phase_text = "Q.E.D."
            phase_symbol = "[QED]"
            phase_color = settings.GOLD
        elif scene.state == "GAME_OVER_TRANSITION":
            phase_text = "FATAL ERROR"
            phase_symbol = "0/0"
            phase_color = settings.RED

        draw_text(screen, f"{phase_text} {phase_symbol}", (x3 + w3 // 2, panel_y + 38), phase_color, 16)
        
        mid_x = x3 + w3 // 2
        move_x = mid_x - 38
        act_x = mid_x + 18
        
        move_ready = scene.turn_manager.player_moved
        move_color = settings.GREEN if move_ready else (80, 80, 80)
        pygame.draw.circle(screen, move_color, (move_x, panel_y + 67), 5)
        draw_text(screen, "MOVE", (move_x + 8, panel_y + 68), settings.LIGHT_GRAY, 14, center=False)

        act_ready = scene.turn_manager.player_acted
        act_color = settings.GREEN if act_ready else (80, 80, 80)
        pygame.draw.circle(screen, act_color, (act_x, panel_y + 67), 5)
        draw_text(screen, "ACTION", (act_x + 8, panel_y + 68), settings.LIGHT_GRAY, 14, center=False)

        # --- PANEL 4: SKILLS & ACTIONS ---
        draw_hud_panel(x4, w4, t("actions"), settings.CYAN)
        
        def draw_skill_slot(slot_x, key_label, name_label, unlocked, active, cooldown, max_cooldown, cost, current_rigor, color):
            slot_rect = pygame.Rect(slot_x, panel_y + 24, 32, 32)
            if not unlocked:
                pygame.draw.rect(screen, (22, 22, 34), slot_rect, border_radius=4)
                pygame.draw.rect(screen, (40, 40, 60), slot_rect, 1, border_radius=4)
                draw_text(screen, "🔒", slot_rect.center, (80, 80, 100), 16)
                
                keycap_w = 30 if len(key_label) > 1 else 20
                keycap_x = slot_x + (32 - keycap_w) // 2
                keycap_y = panel_y + 61
                keycap_rect = pygame.Rect(keycap_x, keycap_y, keycap_w, 15)
                pygame.draw.rect(screen, (20, 22, 30), keycap_rect, border_radius=4)
                pygame.draw.rect(screen, (50, 55, 70), keycap_rect, 1, border_radius=4)
                draw_text(screen, key_label, keycap_rect.center, (80, 80, 100), 11)
                return

            pygame.draw.rect(screen, (14, 18, 30), slot_rect, border_radius=4)
            if active:
                pygame.draw.rect(screen, settings.GOLD, slot_rect, 2, border_radius=4)
                glow_rect = slot_rect.inflate(2, 2)
                pygame.draw.rect(screen, settings.CYAN, glow_rect, 1, border_radius=4)
            else:
                pygame.draw.rect(screen, (60, 80, 110), slot_rect, 1, border_radius=4)

            draw_text(screen, name_label, slot_rect.center, color, 13)

            if cooldown > 0:
                s_overlay = pygame.Surface((32, 32), pygame.SRCALPHA)
                s_overlay.fill((0, 0, 0, 190))
                screen.blit(s_overlay, slot_rect.topleft)
                draw_text(screen, f"{int(cooldown)} Rnd", slot_rect.center, settings.WHITE, 12)
            elif cost > current_rigor:
                s_overlay = pygame.Surface((32, 32), pygame.SRCALPHA)
                s_overlay.fill((100, 20, 20, 140))
                screen.blit(s_overlay, slot_rect.topleft)
                draw_text(screen, "⚡", slot_rect.center, settings.RED, 18)

            keycap_w = 30 if len(key_label) > 1 else 20
            keycap_x = slot_x + (32 - keycap_w) // 2
            keycap_y = panel_y + 61
            keycap_rect = pygame.Rect(keycap_x, keycap_y, keycap_w, 15)
            
            pygame.draw.rect(screen, (30, 36, 55), keycap_rect, border_radius=4)
            border_color = settings.GOLD if active else (80, 100, 130)
            pygame.draw.rect(screen, border_color, keycap_rect, 1, border_radius=4)
            key_color = settings.GOLD if active else settings.WHITE
            draw_text(screen, key_label, keycap_rect.center, key_color, 11)

        start_x = x4 + (w4 - 202) // 2
        
        atk_active = (scene.selected_skill is None) and (scene.state in ("PLAYER_ACTION_SELECT", "RESOLVE_ACTION"))
        draw_skill_slot(start_x, "LMB", "ATK", True, atk_active, 0, 0, 0, current_player.rigor, settings.RED)

        has_pitagoras = game.skill_tree.is_unlocked("pitagoras") if game.skill_tree else False
        pit_active = scene.selected_skill == "pitagoras"
        draw_skill_slot(start_x + 34, "1", "PIT", has_pitagoras, pit_active, current_player.pitagoras_cooldown, 1, settings.PITAGORAS_RIGOR_COST, current_player.rigor, settings.YELLOW)

        has_reflexao = game.skill_tree.is_unlocked("reflexao") if game.skill_tree else False
        ref_active = scene.selected_skill == "reflexao"
        draw_skill_slot(start_x + 68, "2", "REF", has_reflexao, ref_active, current_player.reflexao_cooldown, 3, settings.REFLEXAO_RIGOR_COST, current_player.rigor, settings.CYAN)

        has_integral = game.skill_tree.is_unlocked("integral") if game.skill_tree else False
        int_active = scene.selected_skill == "integral"
        draw_skill_slot(start_x + 102, "3", "INT", has_integral, int_active, current_player.integral_cooldown, 1, settings.INTEGRAL_RIGOR_COST, current_player.rigor, (100, 255, 100))

        has_fractal = game.skill_tree.is_unlocked("fractal") if game.skill_tree else False
        frac_active = scene.selected_skill == "fractal"
        draw_skill_slot(start_x + 136, "4", "FRA", has_fractal, frac_active, current_player.fractal_cooldown, 5, settings.FRACTAL_RIGOR_COST, current_player.rigor, (255, 180, 100))

        has_ctrlz = game.skill_tree.is_unlocked("ctrlz") if game.skill_tree else False
        ctrlz_cooldown = scene.turn_manager.rewind_cooldown_turns
        draw_skill_slot(start_x + 170, "R", "Z", has_ctrlz, False, ctrlz_cooldown, settings.REWIND_COOLDOWN_TURNS, 0, current_player.rigor, settings.PURPLE)

        draw_text(screen, "SKILLS & REWIND", (x4 + w4 // 2, panel_y + 84), settings.LIGHT_GRAY, 14)

        # --- PANEL 5: FEED LOGS ---
        draw_hud_panel(x5, w5)
        draw_text(screen, t("feed"), (x5 + w5 // 2, panel_y + 8), settings.GREEN, 15)
        
        log_y = panel_y + 22
        if scene.turn_log:
            font = pygame.font.Font(None, 18)
            max_lines = 4
            start_idx = max(0, len(scene.turn_log) - max_lines)
            for i, entry in enumerate(scene.turn_log[start_idx:start_idx + max_lines]):
                display_entry = entry
                max_chars = max(15, int((w5 - 16) / 7))
                if len(display_entry) > max_chars:
                    display_entry = display_entry[:max_chars-3] + "..."
                
                if "CRIT" in entry or "CRITICAL" in entry:
                    color = settings.GOLD
                elif "hit" in entry.lower() or "attack" in entry.lower():
                    color = settings.RED
                elif "Miss" in entry or "missed" in entry:
                    color = settings.GRAY
                elif "moved" in entry:
                    color = settings.LIGHT_GRAY
                elif "QED" in entry.upper() or "eliminated" in entry:
                    color = settings.GREEN
                else:
                    color = (180, 180, 220)

                img = font.render(display_entry, True, color)
                screen.blit(img, (x5 + 8, log_y + i * 16))
        else:
            font = pygame.font.Font(None, 18)
            img1 = font.render("SYSTEM: ACTIVE", True, settings.GREEN)
            screen.blit(img1, (x5 + 8, log_y + 10))
            img2 = font.render("AWAITING FORMULA", True, settings.GRAY)
            screen.blit(img2, (x5 + 8, log_y + 26))

        controls = "WASD/click move + confirm  |  1/2/3/4 skills  |  R rewind  |  Esc pause"
        if scene._is_true_coop():
            turn_owner = "HOST" if scene._current_player_owner() == "host" else "CLIENT"
            controls = f"{controls}   [ Turn: {turn_owner} {player_label} ]"
        controls_img = pygame.font.Font(None, 16).render(controls, True, settings.GRAY)
        screen.blit(controls_img, (12, bar_y + 104))
