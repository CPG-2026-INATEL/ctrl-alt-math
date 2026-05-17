import pygame
import math
import random
import settings

class GameplayMathRenderer:
    def __init__(self, scene, renderer):
        self.scene = scene
        self.renderer = renderer
        self.game = scene.game

    def draw_math_highlights_and_predictions(self, temp, world_offset):
        scene = self.scene
        game = self.game

        # 1. Player Move Range Highlights
        if scene.state == "PLAYER_INPUT" and scene.show_move_range:
            pc = game.player.col
            pr = game.player.row
            reachable = scene.grid.get_reachable_cells(
                pc,
                pr,
                game.player.move_range,
                extra_blocked=scene._other_player_occupied_cells(game.player),
            )
            scene.grid.draw(temp, highlight_cells=reachable, highlight_color=settings.BLUE, offset=world_offset)

        # 2. Player Action Ranges and Skill Formulas (e.g. Pythagorean right-triangle drawing)
        if scene.state == "PLAYER_ACTION_SELECT" and scene.show_action_range:
            if scene.selected_skill == "pitagoras":
                cells = scene.grid.get_cells_in_radius(
                    game.player.col, game.player.row,
                    settings.PITAGORAS_RANGE
                )
                scene.grid.draw(temp, highlight_cells=cells, highlight_color=settings.YELLOW, offset=world_offset)
                
                pc_c, pc_r = game.player.col, game.player.row
                cc_c, cc_r = scene.cursor_col, scene.cursor_row
                corner_c, corner_r = cc_c, pc_r
                
                # Draw the neon right-triangle
                scene.grid.draw_triangle(temp,
                    pc_c, pc_r,
                    corner_c, corner_r,
                    cc_c, cc_r,
                    settings.YELLOW, 2, offset=world_offset)
                
                # Draw right-angle square indicator at corner
                if pc_c != cc_c and pc_r != cc_r:
                    cx, cy = scene.grid.to_pixel(corner_c, corner_r)
                    cx += world_offset[0]
                    cy += world_offset[1]
                    sgn_x = -1 if cc_c > pc_c else 1
                    sgn_y = 1 if cc_r > pc_r else -1
                    sq_sz = 8
                    pygame.draw.line(temp, settings.YELLOW, (cx, cy + sgn_y * sq_sz), (cx + sgn_x * sq_sz, cy + sgn_y * sq_sz), 1)
                    pygame.draw.line(temp, settings.YELLOW, (cx + sgn_x * sq_sz, cy), (cx + sgn_x * sq_sz, cy + sgn_y * sq_sz), 1)
                
                # Draw elegant formulas / side length labels
                dx = cc_c - pc_c
                dy = cc_r - pc_r
                eucl = math.sqrt(dx * dx + dy * dy)
                font = pygame.font.Font(None, 13)
                
                # Side a (horizontal) label
                if dx != 0:
                    px_a = (scene.grid.to_pixel(pc_c, pc_r)[0] + scene.grid.to_pixel(corner_c, corner_r)[0]) / 2 + world_offset[0]
                    py_a = scene.grid.to_pixel(pc_c, pc_r)[1] + world_offset[1] - 8
                    lbl_a = font.render(f"a={abs(dx)}", True, settings.LIGHT_GRAY)
                    temp.blit(lbl_a, (px_a - lbl_a.get_width() // 2, py_a))
                
                # Side b (vertical) label
                if dy != 0:
                    px_b = scene.grid.to_pixel(corner_c, corner_r)[0] + world_offset[0] + 6
                    py_b = (scene.grid.to_pixel(corner_c, corner_r)[1] + scene.grid.to_pixel(cc_c, cc_r)[1]) / 2 + world_offset[1]
                    lbl_b = font.render(f"b={abs(dy)}", True, settings.LIGHT_GRAY)
                    temp.blit(lbl_b, (px_b, py_b - lbl_b.get_height() // 2))
                
                # Side c (hypotenuse) label
                if dx != 0 and dy != 0:
                    px_c = (scene.grid.to_pixel(pc_c, pc_r)[0] + scene.grid.to_pixel(cc_c, cc_r)[0]) / 2 + world_offset[0] - 16
                    py_c = (scene.grid.to_pixel(pc_c, pc_r)[1] + scene.grid.to_pixel(cc_c, cc_r)[1]) / 2 + world_offset[1] - 12
                    lbl_c = font.render(f"c={eucl:.2f}", True, settings.GOLD)
                    temp.blit(lbl_c, (px_c, py_c))
            elif scene.selected_skill == "reflexao":
                cells = scene.grid.get_cells_in_radius(
                    game.player.col, game.player.row,
                    settings.REFLEXAO_RANGE
                )
                scene.grid.draw(temp, highlight_cells=cells, highlight_color=settings.CYAN, offset=world_offset)
            elif scene.selected_skill == "integral":
                st = game.skill_tree
                radius = st.get_skill_value("integral", "range", settings.INTEGRAL_RANGE)
                cells = scene.grid.get_cells_in_radius(
                    game.player.col, game.player.row, radius
                )
                scene.grid.draw(temp, highlight_cells=cells, highlight_color=(100, 255, 100), offset=world_offset)
            elif scene.selected_skill == "fractal":
                cells = scene.grid.get_cells_in_radius(
                    game.player.col, game.player.row, 1
                )
                scene.grid.draw(temp, highlight_cells=cells, highlight_color=(255, 180, 100), offset=world_offset)
            else:
                cells = scene.grid.get_cells_in_range(
                    game.player.col, game.player.row,
                    settings.BASIC_ATTACK_RANGE
                )
                scene.grid.draw(temp, highlight_cells=cells, highlight_color=settings.RED, offset=world_offset)

        # 3. Derivada velocity vectors & velocity formulas
        if game.skill_tree.is_unlocked("derivada"):
            for intent in scene.enemy_intents:
                if intent is None or intent.enemy.dead:
                    continue
                enemy = intent.enemy
                if intent.move_target and intent.move_target != (enemy.col, enemy.row):
                    d_col = intent.move_target[0] - enemy.col
                    d_row = intent.move_target[1] - enemy.row
                    # Draw neon velocity vector line & arrow
                    scene.grid.draw_vector_arrow(temp, enemy.col, enemy.row,
                                               intent.move_target[0], intent.move_target[1], settings.GREEN, 2, offset=world_offset)
                    # Midpoint coordinates for vector formula label
                    fx, fy = scene.grid.to_pixel(enemy.col, enemy.row)
                    tx, ty = scene.grid.to_pixel(intent.move_target[0], intent.move_target[1])
                    mx = (fx + tx) / 2 + world_offset[0]
                    my = (fy + ty) / 2 + world_offset[1] - 8
                    
                    font = pygame.font.Font(None, 12)
                    lbl_val = f"v = ({d_col:+d}, {d_row:+d})"
                    lbl_img = font.render(lbl_val, True, settings.GREEN)
                    temp.blit(lbl_img, (mx - lbl_img.get_width() // 2, my - lbl_img.get_height() // 2))
                else:
                    # Fallback to direction indicator if no path found
                    dc = game.player.col - enemy.col
                    dr = game.player.row - enemy.row
                    if dc != 0 or dr != 0:
                        length = math.sqrt(dc * dc + dr * dr)
                        ndc = dc / length
                        ndr = dr / length
                        end_c = enemy.col + ndc * 1.5
                        end_r = enemy.row + ndr * 1.5
                        scene.grid.draw_vector_arrow(temp, enemy.col, enemy.row,
                                                   int(end_c), int(end_r), settings.GREEN, 1, offset=world_offset)

        # 4. Bayes Heatmap and Percentage Probability Labels
        if game.skill_tree.is_unlocked("bayes"):
            pc = game.player.col
            pr = game.player.row
            font = pygame.font.Font(None, 11)
            for enemy in game.enemies:
                if enemy.dead:
                    continue
                dist = scene.grid.grid_distance(enemy.col, enemy.row, pc, pr)
                max_dist = enemy.attack_range
                if max_dist > 0 and dist <= max_dist:
                    proximity = 1.0 - (dist / max_dist)
                    intensity = int(40 + proximity * 60)
                    cells = scene.grid.get_cells_in_radius(enemy.col, enemy.row, 2)
                    for col, row in cells:
                        rect = scene.grid.cell_rect(col, row)
                        rect.x += world_offset[0]
                        rect.y += world_offset[1]
                        
                        # Glitch distortion when entropy > 50
                        cell_intensity = intensity
                        if game.entropy > 50 and random.random() < 0.2:
                            rect.x += random.randint(-3, 3)
                            rect.y += random.randint(-3, 3)
                            cell_intensity = int(intensity * random.uniform(0.3, 1.8))
                        
                        s = pygame.Surface((rect.width, rect.height))
                        s.set_alpha(max(5, min(120, cell_intensity // 3)))
                        s.fill(settings.PURPLE)
                        temp.blit(s, rect)
                        
                        p_val = int(proximity * 100)
                        lbl_bayes = font.render(f"P(T)={p_val}%", True, (220, 180, 255))
                        temp.blit(lbl_bayes, (rect.centerx - lbl_bayes.get_width() // 2, rect.centery - lbl_bayes.get_height() // 2))

        # 5. Game Theory: Threat Vectors and Nash Equilibrium safer tiles
        if game.skill_tree.is_unlocked("teoria_jogos"):
            pc = game.player.col
            pr = game.player.row
            
            # Red threat vectors pointing to player
            for enemy in game.enemies:
                if enemy.dead:
                    continue
                if scene.grid.grid_distance(enemy.col, enemy.row, pc, pr) <= enemy.attack_range:
                    scene.grid.draw_vector_arrow(temp, enemy.col, enemy.row,
                                               pc, pr, settings.RED, 1, offset=world_offset)
            
            # Evaluate candidates for safest Nash equilibrium
            reachable = scene.grid.get_reachable_cells(
                pc, pr, game.player.move_range,
                extra_blocked=scene._other_player_occupied_cells(game.player)
            )
            candidates = [(pc, pr)] + reachable
            safest_cell = None
            min_threat = 999999
            
            for cc, cr in candidates:
                threat_score = 0
                for enemy in game.enemies:
                    if enemy.dead:
                        continue
                    if scene.grid.grid_distance(enemy.col, enemy.row, cc, cr) <= enemy.attack_range:
                        threat_score += 1
                
                dist_to_player = scene.grid.grid_distance(pc, pr, cc, cr)
                eval_score = threat_score * 1000 + dist_to_player
                
                if eval_score < min_threat:
                    min_threat = eval_score
                    safest_cell = (cc, cr)
            
            if safest_cell:
                sc_col, sc_row = safest_cell
                rect = scene.grid.cell_rect(sc_col, sc_row)
                rect.x += world_offset[0]
                rect.y += world_offset[1]
                
                glow_alpha = int(100 + 60 * math.sin(scene.cursor_timer * 6))
                s = pygame.Surface((rect.width, rect.height))
                s.set_alpha(glow_alpha)
                s.fill(settings.CYAN)
                temp.blit(s, rect)
                pygame.draw.rect(temp, settings.CYAN, rect, 2)
                
                font = pygame.font.Font(None, 11)
                lbl_nash = font.render("NASH EQ", True, settings.WHITE)
                temp.blit(lbl_nash, (rect.centerx - lbl_nash.get_width() // 2, rect.centery - lbl_nash.get_height() // 2))
