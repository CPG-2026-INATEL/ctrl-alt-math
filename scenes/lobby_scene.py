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
        self.mode_options = [
            (t("lobby_host"), "host"),
            (t("lobby_join"), "join"),
            (t("lobby_back"), "back"),
        ]
        self.mode = "choose"
        self.selected_option = 0
        self.status = ""
        self.connected = False
        self.ip_input = ""
        self.ip_editing = False
        self.scan_hosts = []
        self._start_delay = 0.0

    def _text_rect(self, text, center, size, pad_x=30, pad_y=16):
        font = pygame.font.Font(None, size)
        rect = font.render(text, True, settings.WHITE).get_rect(center=center)
        return rect.inflate(pad_x, pad_y)

    def _choose_option_rect(self, index):
        label, _ = self.mode_options[index]
        return self._text_rect(label, (settings.WINDOW_WIDTH // 2, 180 + index * 50), 24)

    def _cancel_rect(self):
        return self._text_rect(t("lobby_esc_cancel"), (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT - 40), 14)

    def _start_rect(self):
        if self.mode == "hosting":
            return self._text_rect(t("lobby_start_prompt"), (settings.WINDOW_WIDTH // 2, 380), 24)
        return self._text_rect(t("lobby_press_start"), (settings.WINDOW_WIDTH // 2, 280), 24)

    def _join_input_rect(self):
        return self._text_rect(self.ip_input + "_", (settings.WINDOW_WIDTH // 2, 280), 24, 80, 20)

    def _scan_rect(self):
        return self._text_rect(t("lobby_scan_hint"), (settings.WINDOW_WIDTH // 2, 330), 14)

    def _host_rect(self, index, ip):
        return self._text_rect(ip, (settings.WINDOW_WIDTH // 2, 280 + index * 30), 20)

    def _start_host(self):
        self.host = NetworkHost()
        try:
            self.host.start()
            all_ips = self.host.get_all_local_ips()
            self.host_ip = all_ips[0] if all_ips else "?.?.?.?"
            self.host_all_ips = all_ips
            self.status = t("lobby_waiting", ip=self.host_ip)
            self.status_color = settings.GREEN
            self.mode = "hosting"
            self.player_index = 1
        except (OSError, RuntimeError) as e:
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

    def _parse_endpoint(self, text):
        raw = text.strip()
        if raw.startswith("tcp://"):
            raw = raw[len("tcp://"):]
        host = raw
        port = settings.LAN_PORT
        if ":" in raw:
            host, port_str = raw.rsplit(":", 1)
            if port_str.isdigit():
                port = int(port_str)
        return host.strip(), port

    def _connect_to(self, ip):
        self.client = NetworkClient()
        try:
            host, port = self._parse_endpoint(ip)
            self.client.connect(host, port)
            self.connected = True
            self.status = t("lobby_connected")
            self.status_color = settings.GREEN
            self.mode = "connected"
            self.player_index = 2
        except (ConnectionError, OSError, RuntimeError) as e:
            self.status = f"Error: {e}"
            self.status_color = settings.RED
            self.client = None

    def _start_game(self):
        if self.host:
            # Broadcast difficulty + seed so client uses same settings
            seed = int(pygame.time.get_ticks())
            self.game.seed = seed
            self.host.broadcast({
                "type": "start_game",
                "seed": seed,
                "difficulty": settings.DIFFICULTY,
            })
            self._start_delay = 0.25  # wait 250ms before switching
        else:
            # Client: transition immediately (driven by server message)
            self._do_enter_game()

    def _do_enter_game(self, difficulty=None, seed=None):
        # Apply host difficulty on client side
        if difficulty:
            settings.DIFFICULTY = difficulty
        if seed:
            self.game.seed = seed
        # Save mp references before reset wipes them
        mp_host = self.host
        mp_client = self.client
        mp_player_index = self.player_index
        mp_seed = getattr(self.game, "seed", None)
        self.game.reset_game_state()
        # Restore mp references after reset
        self.game.mp_host = mp_host
        self.game.mp_client = mp_client
        self.game.mp_player_index = mp_player_index
        self.game.seed = mp_seed
        self.game.mp_is_multiplayer = True
        # Go to the map so the normal room-selection flow works
        self.game.scene_manager.switch("map")

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            if self.mode == "choose":
                for i in range(len(self.mode_options)):
                    if self._choose_option_rect(i).collidepoint(event.pos):
                        self.selected_option = i
                        return
            elif self.mode == "join" and not self.ip_editing:
                for i, ip in enumerate(self.scan_hosts):
                    if self._host_rect(i, ip).collidepoint(event.pos):
                        self.selected_host = i
                        return
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.mode == "choose":
                for i, (_, action) in enumerate(self.mode_options):
                    if self._choose_option_rect(i).collidepoint(event.pos):
                        self.selected_option = i
                        self.game.sfx.play("menu_confirm")
                        if action == "host":
                            self._start_host()
                        elif action == "join":
                            self._start_join()
                        else:
                            self.game.scene_manager.switch("menu")
                        return
            elif self.mode == "hosting":
                if self.connected and self._start_rect().collidepoint(event.pos):
                    self._start_game()
                    return
                if self._cancel_rect().collidepoint(event.pos):
                    if self.host:
                        self.host.stop()
                        self.host = None
                    self.mode = "choose"
                    self.status = ""
                    return
            elif self.mode == "join":
                if self._cancel_rect().collidepoint(event.pos):
                    self.ip_editing = False
                    self.mode = "choose"
                    self.status = ""
                    return
                if self.ip_editing and self._scan_rect().collidepoint(event.pos):
                    self._scan_lan()
                    return
                if self.ip_editing and self._join_input_rect().collidepoint(event.pos):
                    self.ip_editing = True
                    return
                if not self.ip_editing:
                    for i, ip in enumerate(self.scan_hosts):
                        if self._host_rect(i, ip).collidepoint(event.pos):
                            self.selected_host = i
                            self._connect_to(ip)
                            return
            elif self.mode == "connected":
                if self._start_rect().collidepoint(event.pos):
                    if self.client:
                        self.client.send({"type": "client_ready"})
                        self.status = t("lobby_waiting_host")
                        self.status_color = settings.YELLOW
                    return
                if self._cancel_rect().collidepoint(event.pos):
                    if self.client:
                        self.client.disconnect()
                        self.client = None
                    self.mode = "choose"
                    self.connected = False
                    self.status = ""
                    return
            return

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
                    if ch and (ch.isalnum() or ch in ".:-/"):
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

            # Update client list for display
            self.connected_clients = self.host.get_connected_clients_info()
            if self.connected_clients and not self.connected:
                self.connected = True
                self.status = t("lobby_player_joined")
                self.status_color = settings.GREEN

        if self.client:
            msgs = self.client.poll()
            for msg in msgs:
                if msg.get("type") == "start_game":
                    difficulty = msg.get("difficulty")
                    seed = msg.get("seed")
                    self._do_enter_game(difficulty=difficulty, seed=seed)

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
            draw_text(screen, t("lobby_choose_help"),
                      (settings.WINDOW_WIDTH // 2, 360), settings.GRAY, 16)

        elif self.mode == "hosting":
            draw_text(screen, t("lobby_hosting"),
                      (settings.WINDOW_WIDTH // 2, 160), settings.GREEN, 28)
            # Show all local IPs so the user can pick the right one
            ips = getattr(self, "host_all_ips", [self.host_ip] if self.host_ip else [])
            draw_text(screen, t("lobby_share_ip"),
                      (settings.WINDOW_WIDTH // 2, 195), settings.LIGHT_GRAY, 14)
            for idx, ip in enumerate(ips):
                color = settings.WHITE if idx > 0 else settings.CYAN
                draw_text(screen, ip,
                          (settings.WINDOW_WIDTH // 2, 215 + idx * 24), color, 20)
            status_y = 215 + len(ips) * 24 + 10
            draw_text(screen, self.status,
                      (settings.WINDOW_WIDTH // 2, status_y), self.status_color, 18)

            # Show connected clients
            clients = getattr(self, "connected_clients", [])
            if clients:
                draw_text(screen, f"Connected: {len(clients)}",
                          (settings.WINDOW_WIDTH // 2, status_y + 25), settings.LIGHT_GRAY, 16)
                for i, (cid, ip) in enumerate(clients):
                    draw_text(screen, f"Player {cid} ({ip})",
                              (settings.WINDOW_WIDTH // 2, status_y + 45 + i * 20), settings.WHITE, 14)

            if self.connected:
                draw_text(screen, t("lobby_start_prompt"),
                          (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT - 100), settings.GOLD, 24)
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
                draw_text(screen, t("lobby_join_help"),
                          (settings.WINDOW_WIDTH // 2, 365), settings.LIGHT_GRAY, 15)
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
            draw_text(screen, t("lobby_connected_help"),
                      (settings.WINDOW_WIDTH // 2, 330), settings.LIGHT_GRAY, 15)
