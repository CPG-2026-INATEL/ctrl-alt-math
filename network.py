"""
network.py – WebSocket-based multiplayer networking for Ctrl+Alt+Math.

Architecture (mirrors danqzq/gdg-ws1):
  NetworkHost  – runs an asyncio WebSocket server in a daemon thread.
                 All clients connect to it; it broadcasts to all of them.
  NetworkClient – connects to the host's WebSocket server.
  LANDiscovery  – finds hosts on the local network (UDP broadcast + TCP scan).

Messages are newline-terminated JSON strings, same as before, so the rest of
the game code (lobby_scene, map_scene, gameplay_scene) does not need to change.
"""

import asyncio
import json
import socket
import threading
import time

import settings

LAN_PORT           = settings.LAN_PORT            # 5555  – WebSocket game port
LAN_DISCOVERY_PORT = settings.LAN_DISCOVERY_PORT  # 5556  – UDP discovery
LAN_BUFFER_SIZE    = settings.LAN_BUFFER_SIZE
LAN_TIMEOUT        = settings.LAN_TIMEOUT


# ---------------------------------------------------------------------------
# NetworkHost
# ---------------------------------------------------------------------------

class NetworkHost:
    def __init__(self, port=LAN_PORT):
        self.port        = port
        self.running     = False
        self.lock        = threading.Lock()
        self.inbox       = []          # incoming messages from clients
        self._websockets = set()       # connected WebSocket objects
        self._loop       = None        # asyncio event loop in the server thread
        self._next_id    = 1
        self._client_ids = {}          # websocket -> int id
        # Keep legacy attributes and keep them updated
        self.clients    = []           # List of connected websockets
        self.client_ids = {}           # dict: cid -> websocket

    def _log(self, msg):
        if getattr(settings, 'DEBUG_NETWORK', False):
            print(f"[Host] {msg}")

    # ------------------------------------------------------------------ start

    def start(self):
        self._log(f"Initializing host on port {self.port}...")
        self._ensure_firewall_rules()
        self.running = True
        
        # Log all available IPs for debugging
        all_ips = self.get_all_local_ips()
        self._log(f"Detected local IPs: {', '.join(all_ips)}")
        self._log(f"Primary IP (suggested): {self.get_local_ip()}")

        # Start asyncio loop in a daemon thread
        self._loop = asyncio.new_event_loop()
        t = threading.Thread(target=self._run_loop, daemon=True)
        t.start()
        # Discovery responder (UDP, no asyncio needed)
        dt = threading.Thread(target=self._discovery_loop, daemon=True)
        dt.start()
        self._log("Host network threads are active.")
        self._log("Host threads started.")

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._serve())

    async def _serve(self):
        import websockets
        self._log(f"WebSocket server binding to 0.0.0.0 (all interfaces) on port {self.port}")
        try:
            async with websockets.serve(self._handle_client, "0.0.0.0", self.port):
                while self.running:
                    await asyncio.sleep(0.05)
        except Exception as e:
            self._log(f"Server error: {e}")

    async def _handle_client(self, websocket):
        addr = websocket.remote_address[0] if websocket.remote_address else "unknown"
        with self.lock:
            cid = self._next_id
            self._next_id += 1
            self._client_ids[websocket] = cid
            self._websockets.add(websocket)
            self.clients.append(websocket)
            self.client_ids[cid] = websocket
        
        self._log(f"Client {cid} connected from {addr}. Total: {len(self._websockets)}")
        
        # Send initial handshake
        await websocket.send(json.dumps({"type": "assign_id", "id": cid}))
        await websocket.send(json.dumps({"type": "player_index",
                                          "index": len(self._websockets)}))
        try:
            async for raw in websocket:
                try:
                    msg = json.loads(raw)
                    self._log(f"Recv from {cid}: {msg.get('type')}")
                    msg["_from"] = cid
                    with self.lock:
                        self.inbox.append(msg)
                except json.JSONDecodeError:
                    self._log(f"JSON error from {cid}")
        except Exception as e:
            self._log(f"Error handling client {cid}: {e}")
        finally:
            with self.lock:
                self._websockets.discard(websocket)
                self._client_ids.pop(websocket, None)
                if websocket in self.clients:
                    self.clients.remove(websocket)
                self.client_ids.pop(cid, None)
            self._log(f"Client {cid} disconnected. Remaining: {len(self._websockets)}")

    # ------------------------------------------------------------------ send

    def broadcast(self, msg):
        """Send msg to every connected client (fire-and-forget)."""
        if not self._loop or not self.running:
            return
        raw = json.dumps(msg)
        self._log(f"Broadcasting message type: {msg.get('type')} ({len(raw)} bytes)")
        async def _do():
            targets = set(self._websockets)
            for ws in targets:
                try:
                    await ws.send(raw)
                except Exception as e:
                    self._log(f"Broadcast error to a client: {e}")
        asyncio.run_coroutine_threadsafe(_do(), self._loop)

    def send_to(self, cid, msg):
        if not self._loop or not self.running:
            return
        raw = json.dumps(msg)
        async def _do():
            with self.lock:
                targets = [ws for ws, c in self._client_ids.items() if c == cid]
            for ws in targets:
                try:
                    await ws.send(raw)
                except Exception:
                    pass
        asyncio.run_coroutine_threadsafe(_do(), self._loop)

    def poll(self):
        with self.lock:
            msgs = list(self.inbox)
            self.inbox.clear()
        return msgs

    def get_connected_clients_info(self):
        """Returns a list of (cid, ip) for all connected clients."""
        with self.lock:
            info = []
            for ws, cid in self._client_ids.items():
                try:
                    ip = ws.remote_address[0] if ws.remote_address else "unknown"
                    info.append((cid, ip))
                except Exception:
                    info.append((cid, "unknown"))
            return info

    # ------------------------------------------------------------------ stop

    def stop(self):
        self.running = False
        # Do not call self._loop.stop() here; it causes RuntimeError.
        # Setting self.running = False makes _serve() return, finishing run_until_complete().

    # ------------------------------------------------------------------ util

    def get_local_ip(self):
        ips = self.get_all_local_ips()
        return ips[0] if ips else "127.0.0.1"

    def get_all_local_ips(self):
        ips = set()
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None):
                ip = info[4][0]
                if ip.startswith("127.") or ":" in ip:
                    continue
                ips.add(ip)
        except OSError:
            pass
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ips.add(s.getsockname()[0])
            s.close()
        except OSError:
            pass

        def _rank(ip):
            if ip.startswith("192.168."): return 0
            if ip.startswith("10."):      return 1
            if ip.startswith("172."):     return 2
            return 3

        return sorted(ips, key=_rank) or ["127.0.0.1"]

    # ------------------------------------------------------------------ firewall

    def _ensure_firewall_rules(self):
        import subprocess, sys
        if sys.platform != "win32":
            return
        self._log("Checking firewall rules...")
        rules = [
            ("CtrlAltMath-TCP-In",  "TCP", str(LAN_PORT)),
            ("CtrlAltMath-UDP-In",  "UDP", str(LAN_DISCOVERY_PORT)),
            ("CtrlAltMath-UDP2-In", "UDP", str(LAN_DISCOVERY_PORT + 1)),
        ]
        for name, proto, port in rules:
            try:
                res = subprocess.run(
                    ["netsh", "advfirewall", "firewall", "add", "rule",
                     f"name={name}", "dir=in", "action=allow",
                     f"protocol={proto}", f"localport={port}",
                     "enable=yes", "profile=any"],
                    capture_output=True, timeout=3
                )
                if res.returncode == 0:
                    self._log(f"Firewall rule added: {name}")
                else:
                    self._log(f"Firewall rule note: {name} (may require Admin or already exists)")
            except Exception as e:
                self._log(f"Firewall setup error for {name}: {e}")

    # ------------------------------------------------------------------ discovery (UDP)

    def _discovery_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("", LAN_DISCOVERY_PORT))
        except OSError:
            return
        sock.settimeout(1.0)
        while self.running:
            try:
                data, addr = sock.recvfrom(256)
                text = data.decode("utf-8", errors="ignore")
                if text.startswith("DISCOVER_REQUEST"):
                    self._log(f"Discovery request from {addr[0]}")
                    reply_port = LAN_DISCOVERY_PORT + 1
                    if ":" in text:
                        try:
                            reply_port = int(text.split(":", 1)[1])
                        except ValueError:
                            pass
                    sock.sendto(b"DISCOVER_RESPONSE", (addr[0], reply_port))
            except socket.timeout:
                continue
            except OSError as e:
                self._log(f"Discovery socket error: {e}")
                break
        sock.close()


# ---------------------------------------------------------------------------
# NetworkClient
# ---------------------------------------------------------------------------

class NetworkClient:
    def __init__(self):
        self.running  = False
        self.lock     = threading.Lock()
        self.inbox    = []
        self.my_id    = None
        self._ws      = None
        self._loop    = None

    def _log(self, msg):
        if getattr(settings, 'DEBUG_NETWORK', False):
            print(f"[Client] {msg}")

    def connect(self, host, port=LAN_PORT):
        self._log(f"Connecting to {host}:{port}...")
        self.running = True
        self._loop = asyncio.new_event_loop()
        t = threading.Thread(
            target=self._run_loop,
            args=(host, port),
            daemon=True
        )
        t.start()
        # Wait briefly for the connection to establish
        deadline = time.time() + LAN_TIMEOUT
        while time.time() < deadline:
            if self._ws is not None or not self.running:
                break
            time.sleep(0.05)
        if self._ws is None:
            self._log(f"Failed to connect to {host}:{port}")
            raise ConnectionError(f"Could not connect to {host}:{port}")
        self._log("Connected successfully.")

    def _run_loop(self, host, port):
        self._log(f"Async thread started for {host}")
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._recv_loop(host, port))
        except Exception as e:
            self._log(f"Fatal error in client loop: {e}")
        self.running = False

    async def _recv_loop(self, host, port):
        import websockets
        uri = f"ws://{host}:{port}"
        try:
            # Use wait_for for compatibility with older websockets versions (<10.0)
            ws = await asyncio.wait_for(websockets.connect(uri), timeout=LAN_TIMEOUT)
            async with ws:
                self._ws = ws
                async for raw in ws:
                    try:
                        msg = json.loads(raw)
                        if msg.get("type") == "assign_id":
                            self.my_id = msg["id"]
                            self._log(f"Handshake successful. Assigned ID: {self.my_id}")
                        else:
                            self._log(f"Incoming msg: {msg.get('type')}")
                            with self.lock:
                                self.inbox.append(msg)
                    except json.JSONDecodeError:
                        self._log("Received malformed JSON from host")
        except asyncio.TimeoutError:
            self._log(f"Connection TIMEOUT: Host at {host}:{port} is unreachable.")
        except ConnectionRefusedError:
            self._log(f"Connection REFUSED: Server not running at {host}:{port} or blocked by firewall.")
        except Exception as e:
            self._log(f"Socket error: {type(e).__name__}: {e}")
        finally:
            self._ws = None
            self._log("Client connection closed.")

    def send(self, msg):
        if not self._loop or not self.running or self._ws is None:
            return
        raw = json.dumps(msg)
        async def _do():
            try:
                await self._ws.send(raw)
            except Exception:
                pass
        asyncio.run_coroutine_threadsafe(_do(), self._loop)

    def poll(self):
        with self.lock:
            msgs = list(self.inbox)
            self.inbox.clear()
        return msgs

    def disconnect(self):
        self.running = False
        if self._loop and self._ws:
            # Gracefully close the websocket; this will break the 'async for' loop in _recv_loop
            asyncio.run_coroutine_threadsafe(self._ws.close(), self._loop)


# ---------------------------------------------------------------------------
# LANDiscovery  (UDP broadcast + parallel TCP – unchanged)
# ---------------------------------------------------------------------------

class LANDiscovery:
    def __init__(self, port=LAN_PORT):
        self.port = port
        self.hosts = []
        self.running = False
        self.scan_thread = None

    def _log(self, msg):
        if getattr(settings, 'DEBUG_NETWORK', False):
            print(f"[Discovery] {msg}")

    def start_scan(self):
        self._log("Starting LAN scan...")
        self.running = True
        self.hosts = []
        self.scan_thread = threading.Thread(target=self._scan, daemon=True)
        self.scan_thread.start()

    def _get_broadcast_addresses(self):
        addrs = set()
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None):
                ip = info[4][0]
                if ip.startswith("127.") or ":" in ip:
                    continue
                parts = ip.split(".")
                addrs.add(".".join(parts[:3]) + ".255")
        except OSError:
            pass
        addrs.add("255.255.255.255")
        return list(addrs)

    def _scan(self):
        targets  = self._get_broadcast_addresses()
        local_ip = self._get_local_ip()
        prefix   = ".".join(local_ip.split(".")[:3])
        lock     = threading.Lock()

        # ---- UDP broadcast ----
        def udp_scan():
            send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                send_sock.bind(("", 0))
            except OSError:
                pass
            recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            recv_sock.settimeout(0.3)
            try:
                recv_sock.bind(("", LAN_DISCOVERY_PORT + 1))
            except OSError:
                try:
                    recv_sock.bind(("", 0))
                except OSError:
                    pass
            reply_port = recv_sock.getsockname()[1]
            payload = f"DISCOVER_REQUEST:{reply_port}".encode()
            self._log(f"Broadcasting UDP discovery to {targets} (reply to port {reply_port})")
            for _ in range(3):
                if not self.running:
                    break
                for bcast in targets:
                    try:
                        send_sock.sendto(payload, (bcast, LAN_DISCOVERY_PORT))
                    except OSError:
                        pass
                deadline = time.time() + 0.5
                while time.time() < deadline:
                    try:
                        data, addr = recv_sock.recvfrom(256)
                        if data == b"DISCOVER_RESPONSE":
                            self._log(f"Found host via UDP: {addr[0]}")
                            with lock:
                                if addr[0] not in self.hosts:
                                    self.hosts.append(addr[0])
                    except socket.timeout:
                        pass
                    except OSError as e:
                        self._log(f"UDP recv error: {e}")
                        break
            send_sock.close()
            recv_sock.close()

        # ---- TCP port scan (works behind AP isolation) ----
        def tcp_check(ip):
            if not self.running:
                return
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.2)
                s.connect((ip, self.port))
                s.close()
                self._log(f"Found host via TCP: {ip}")
                with lock:
                    if ip not in self.hosts:
                        self.hosts.append(ip)
            except (socket.timeout, ConnectionRefusedError, OSError):
                pass

        def tcp_scan():
            ips = [f"{prefix}.{i}" for i in range(1, 255)
                   if f"{prefix}.{i}" != local_ip]
            for i in range(0, len(ips), 64):
                if not self.running:
                    break
                batch = [threading.Thread(target=tcp_check, args=(ip,), daemon=True)
                         for ip in ips[i:i + 64]]
                for th in batch:
                    th.start()
                for th in batch:
                    th.join(timeout=0.5)

        t_udp = threading.Thread(target=udp_scan, daemon=True)
        t_tcp = threading.Thread(target=tcp_scan, daemon=True)
        t_udp.start()
        t_tcp.start()
        t_udp.join()
        t_tcp.join()

    def stop_scan(self):
        self.running = False

    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except OSError:
            return "127.0.0.1"