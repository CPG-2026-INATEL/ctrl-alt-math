import pygame
import settings

class GameplayInput:
    def __init__(self, scene):
        self.scene = scene
        self.game = scene.game

    def handle_event(self, event):
        scene = self.scene
        game = self.game

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game.sfx.play("menu_select")
                game.scene_manager.switch("menu")
                return

            if scene.state == "WAVE_INTRO":
                scene._send_mp_command("begin_room")
                scene._begin_room()
                return

            if scene.state == "NO_COMBAT":
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    scene._send_mp_command("leave_no_combat")
                    scene._leave_no_combat_room()
                return

        if scene.state == "PLAYER_INPUT":
            self.handle_player_input(event)
        elif scene.state == "PLAYER_ACTION_SELECT":
            self.handle_action_input(event)

    def handle_player_input(self, event):
        scene = self.scene
        game = self.game

        if not scene._is_local_turn():
            return

        if event.type == pygame.MOUSEMOTION:
            scene._set_cursor_from_mouse(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            scene._set_cursor_from_mouse(event.pos)
            scene._confirm_player_cursor()

        elif event.type == pygame.KEYDOWN:
            dx, dy = 0, 0
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                dx = -1
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                dx = 1
            elif event.key == pygame.K_UP or event.key == pygame.K_w:
                dy = -1
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                dy = 1

            if dx != 0 or dy != 0:
                col = max(0, min(scene.grid.cols - 1, scene.cursor_col + dx))
                row = max(0, min(scene.grid.rows - 1, scene.cursor_row + dy))
                scene.cursor_col, scene.cursor_row = col, row
                scene._send_mp_command("cursor_abs", col=col, row=row)

            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                scene._send_mp_command("confirm")
                scene._confirm_player_cursor()

            elif event.key == pygame.K_r:
                scene._send_mp_command("rewind")
                scene._try_rewind()

    def handle_action_input(self, event):
        scene = self.scene
        game = self.game

        if not scene._is_local_turn():
            return

        if event.type == pygame.MOUSEMOTION:
            scene._set_cursor_from_mouse(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                scene._set_cursor_from_mouse(event.pos)
                scene._confirm_action_cursor()
            elif event.button == 3:
                scene._send_mp_command("cancel_action")
                scene.selected_skill = None
                scene.show_action_range = True

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_BACKSPACE:
                scene._send_mp_command("cancel_action")
                scene.selected_skill = None
                scene.show_action_range = True

            elif event.key == pygame.K_r:
                scene._send_mp_command("rewind")
                scene._try_rewind()

            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                scene._send_mp_command("confirm")
                scene._confirm_action_cursor()

            else:
                skill_id = None
                if event.key == pygame.K_1:
                    skill_id = "pitagoras"
                elif event.key == pygame.K_2:
                    skill_id = "reflexao"
                elif event.key == pygame.K_3:
                    skill_id = "integral"
                elif event.key == pygame.K_4:
                    skill_id = "fractal"

                if skill_id:
                    if skill_id == "pitagoras" and game.skill_tree.is_unlocked("pitagoras"):
                        scene._send_mp_command("select_skill", skill_id="pitagoras")
                        scene._toggle_skill("pitagoras")
                    elif skill_id == "reflexao" and game.skill_tree.is_unlocked("reflexao"):
                        scene._send_mp_command("select_skill", skill_id="reflexao")
                        scene._toggle_skill("reflexao")
                    elif skill_id == "integral" and game.skill_tree.is_unlocked("integral"):
                        scene._send_mp_command("select_skill", skill_id="integral")
                        scene._toggle_skill("integral")
                    elif skill_id == "fractal" and game.skill_tree.is_unlocked("fractal"):
                        scene._send_mp_command("select_skill", skill_id="fractal")
                        scene._toggle_skill("fractal")

    def set_cursor_from_mouse(self, pos):
        scene = self.scene
        # Calculate cell from camera-offset mouse coordinates
        cx = pos[0] + scene.camera_x
        cy = pos[1] + scene.camera_y
        col, row = scene.grid.to_grid(cx, cy)
        col = max(0, min(scene.grid.cols - 1, col))
        row = max(0, min(scene.grid.rows - 1, row))
        scene.cursor_col, scene.cursor_row = col, row
        scene._send_mp_command("cursor_abs", col=col, row=row)

    def toggle_skill(self, skill_id):
        scene = self.scene
        if scene.selected_skill == skill_id:
            scene.selected_skill = None
        else:
            scene.selected_skill = skill_id
        scene.show_action_range = True
