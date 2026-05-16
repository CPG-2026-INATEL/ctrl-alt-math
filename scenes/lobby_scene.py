import pygame
import socket
import threading

import settings
from i18n import t
from network import NetworkHost, NetworkClient, LANDiscovery
from scenes.scene import Scene
from utils import draw_text


class LobbyScene(Scene):
    overlay = False

    def __init__(self, game):
        super().__init__(game)
        self.mode = "choose"
        self.host = None
        self.client = None
        self.discovery = None
        self.scan_hosts = []
        self.selected_host = 0
        self.status = ""
        self.status_color = settings.GRAY
        self.connected = False
        self.player_index = 0
        self.host_ip = ""
        self.mode_options = [
            (t("lobby_host"), "host"),
            (t("lobby_join"), "join"),
            (t("lobby_back"), "back"),
        ]
        self.selected_option = 0
        self.ip_input = ""
        self.ip_editing = False
        self._start_delay = 0.0  # timer to delay host scene switch after broadcast

    def enter(self, prev_scene=None):
        self.mode = "choose"
        self.selected_option = 0
        self.status = ""
        self.connected = False
        self.ip_input = ""
        self.ip_editing = False
        self.scan_hosts = []
        self._start_delay = 0.0

    def _start_host(self):
        self.host = NetworkHost()
        try:
            self.host.start()
            ip = self.host.get_local_ip()
            self.host_ip = ip
            self.status = t("lobby_waiting", ip=ip)
            self.status_color = settings.GREEN
            self.mode = "hosting"
            self.player_index = 1
        except OSError as e:
            self.status = f"Error: {e}"
            self.status_color = settings.RED
            self.host = None

    def _start_join(self):
        self.mode = "join"
        self.ip_editing = True
        self.ip_input = ""
        self.status = t("lobby_enter_ip")
        self.status_color = settings.CYAN
        self.scan_hosts = []
        self.selected_host = 0

    def _scan_lan(self):
        self.discovery = LANDiscovery()
        self.scan_hosts = []
        self.status = t("lobby_scanning")
        self.status_color = settings.YELLOW
        self.discovery.start_scan()

    def _connect_to(self, ip):
        self.client = NetworkClient()
        try:
            self.client.connect(ip)
            self.connected = True
            self.status = t("lobby_connected")
            self.status_color = settings.GREEN
            self.mode = "connected"
            self.player_index = 2
        except (ConnectionError, OSError) as e:
            self.status = f"Error: {e}"
            self.status_color = settings.RED
            self.client = None

    def _start_game(self):
        if self.host:
            # Broadcast difficulty + seed so client uses same settings
            self.host.broadcast({
                "type": "start_game",
                "seed": int(pygame.time.get_ticks()),
                "difficulty": settings.DIFFICULTY,
            })
            self._start_delay = 0.25  # wait 250ms before switching
        else:
            # Client: transition immediately (driven by server message)
            self._do_enter_game()

    def _do_enter_game(self, difficulty=None):
        # Apply host difficulty on client side
        if difficulty:
            settings.DIFFICULTY = difficulty
        # Save mp references before reset wipes them
        mp_host = self.host
        mp_client = self.client
        mp_player_index = self.player_index
        self.game.reset_game_state()
        # Restore mp references after reset
        self.game.mp_host = mp_host
        self.game.mp_client = mp_client
        self.game.mp_player_index = mp_player_index
        self.game.mp_is_multiplayer = True
        # Go to the map so the normal room-selection flow works
        self.game.scene_manager.switch("map")

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if self.mode == "choose":
            if event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(self.mode_options)
                self.game.sfx.play("menu_select")
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(self.mode_options)
                self.game.sfx.play("menu_select")
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                _, action = self.mode_options[self.selected_option]
                self.game.sfx.play("menu_confirm")
                if action == "host":
                    self._start_host()
                elif action == "join":
                    self._start_join()
                elif action == "back":
                    self.game.scene_manager.switch("menu")

        elif self.mode == "hosting":
            if event.key == pygame.K_ESCAPE:
                if self.host:
                    self.host.stop()
                    self.host = None
                self.mode = "choose"
                self.status = ""
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.connected:
                    self._start_game()

        elif self.mode == "join":
            if event.key == pygame.K_ESCAPE:
                self.ip_editing = False
                self.mode = "choose"
                self.status = ""
                return
            if self.ip_editing:
                if event.key == pygame.K_RETURN:
                    if self.ip_input.strip():
                        self._connect_to(self.ip_input.strip())
                    self.ip_editing = False
                elif event.key == pygame.K_BACKSPACE:
                    self.ip_input = self.ip_input[:-1]
                elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    self._scan_lan()
                else:
                    ch = event.unicode
                    if ch and (ch.isdigit() or ch == "."):
                        self.ip_input += ch
            else:
                if event.key == pygame.K_UP:
                    self.selected_host = max(0, self.selected_host - 1)
                elif event.key == pygame.K_DOWN:
                    self.selected_host = min(len(self.scan_hosts) - 1, self.selected_host + 1) if self.scan_hosts else 0
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE) and self.scan_hosts:
                    self._connect_to(self.scan_hosts[self.selected_host])

        elif self.mode == "connected":
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.client:
                    self.client.send({"type": "client_ready"})
                    self.status = t("lobby_waiting_host")
                    self.status_color = settings.YELLOW
            elif event.key == pygame.K_ESCAPE:
                if self.client:
                    self.client.disconnect()
                    self.client = None
                self.mode = "choose"
                self.connected = False
                self.status = ""

    def update(self, dt):
        # Host: handle delayed scene switch so broadcast packet is flushed first
        if self._start_delay > 0:
            self._start_delay -= dt
            if self._start_delay <= 0:
                self._do_enter_game()
            return

        if self.host:
            msgs = self.host.poll()
            for msg in msgs:
                if msg.get("type") == "client_ready":
                    self.connected = True
                    self.status = t("lobby_player_joined")
                    self.status_color = settings.GREEN

        if self.client:
            msgs = self.client.poll()
            for msg in msgs:
                if msg.get("type") == "start_game":
                    difficulty = msg.get("difficulty")
                    self._do_enter_game(difficulty=difficulty)

        if self.discovery:
            self.scan_hosts = list(set(self.discovery.hosts))
            if self.discovery.scan_thread and not self.discovery.scan_thread.is_alive():
                self.discovery = None
                if self.scan_hosts:
                    self.status = t("lobby_found", n=len(self.scan_hosts))
                    self.status_color = settings.GREEN
                else:
                    self.status = t("lobby_no_hosts")
                    self.status_color = settings.RED

    def draw(self, screen):
        overlay = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
        overlay.fill(settings.DARK_BLUE)
        screen.blit(overlay, (0, 0))

        draw_text(screen, t("lobby_title"),
                  (settings.WINDOW_WIDTH // 2, 60), settings.CYAN, 36)

        if self.mode == "choose":
            for i, (label, _) in enumerate(self.mode_options):
                color = settings.GOLD if i == self.selected_option else settings.WHITE
                y = 180 + i * 50
                draw_text(screen, label, (settings.WINDOW_WIDTH // 2, y), color, 24)

        elif self.mode == "hosting":
            draw_text(screen, t("lobby_hosting"),
                      (settings.WINDOW_WIDTH // 2, 180), settings.GREEN, 28)
            if self.host_ip:
                draw_text(screen, self.host_ip,
                          (settings.WINDOW_WIDTH // 2, 240), settings.WHITE, 22)
            draw_text(screen, self.status,
                      (settings.WINDOW_WIDTH // 2, 300), self.status_color, 20)
            if self.connected:
                draw_text(screen, t("lobby_start_prompt"),
                          (settings.WINDOW_WIDTH // 2, 380), settings.GOLD, 24)
            draw_text(screen, t("lobby_esc_cancel"),
                      (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT - 40), settings.GRAY, 14)

        elif self.mode == "join":
            draw_text(screen, t("lobby_joining"),
                      (settings.WINDOW_WIDTH // 2, 180), settings.GREEN, 28)
            if self.ip_editing:
                draw_text(screen, t("lobby_enter_ip"),
                          (settings.WINDOW_WIDTH // 2, 240), settings.CYAN, 18)
                draw_text(screen, self.ip_input + "_",
                          (settings.WINDOW_WIDTH // 2, 280), settings.WHITE, 24)
                draw_text(screen, t("lobby_scan_hint"),
                          (settings.WINDOW_WIDTH // 2, 330), settings.GRAY, 14)
            elif self.scan_hosts:
                draw_text(screen, t("lobby_select_host"),
                          (settings.WINDOW_WIDTH // 2, 240), settings.CYAN, 18)
                for i, ip in enumerate(self.scan_hosts):
                    color = settings.GOLD if i == self.selected_host else settings.WHITE
                    draw_text(screen, ip,
                              (settings.WINDOW_WIDTH // 2, 280 + i * 30), color, 20)
            draw_text(screen, self.status,
                      (settings.WINDOW_WIDTH // 2, 400), self.status_color, 16)
            draw_text(screen, t("lobby_esc_cancel"),
                      (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT - 40), settings.GRAY, 14)

        elif self.mode == "connected":
            draw_text(screen, t("lobby_connected"),
                      (settings.WINDOW_WIDTH // 2, 220), settings.GREEN, 28)
            draw_text(screen, t("lobby_press_start"),
                      (settings.WINDOW_WIDTH // 2, 280), settings.GOLD, 24)