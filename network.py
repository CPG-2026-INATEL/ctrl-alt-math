import json
import socket
import threading
import time
import asyncio
import websockets
from py_localtunnel.tunnel import Tunnel

import settings


class NetworkHost:
    def __init__(self, port=settings.LAN_PORT):
        self.port = port
        self.running = False
        self.lock = threading.Lock()
        self.inbox = []
        self.clients = []        # list of active WebSocket connections
        self.client_ids = {}     # client_id -> WebSocket
        self._conn_to_id = {}    # WebSocket -> client_id
        self._next_id = 1
        self.public_url = None
        self.tunnel = None
        self.loop = None
        self.server = None

    def _log(self, msg):
        if getattr(settings, "DEBUG_NETWORK", False):
            print(f"[Host] {msg}")

    def start(self):
        self._log(f"Starting WebSocket host on port {self.port}")
        self.running = True
        self.server_ready = threading.Event()

        # Start the WebSocket server in a background thread
        threading.Thread(target=self._run_server, daemon=True).start()

        # Wait for the WebSocket server to be fully bound and listening (timeout 5s)
        if not self.server_ready.wait(timeout=5.0):
            self._log("Error: WebSocket server failed to start within timeout.")
            return

        # Programmatically start the localtunnel
        try:
            self.tunnel = Tunnel()
            # Monkeypatch check_local_port to be a no-op to avoid triggering raw TCP handshake EOFError warnings on websockets
            self.tunnel.check_local_port = lambda: None
            # Fetch the URL first (instantaneous)
            raw_url = self.tunnel.get_url(None)
            # Convert https:// to wss:// for public WebSocket connection
            self.public_url = raw_url.replace("https://", "wss://").replace("http://", "ws://")
            self._log(f"Localtunnel generated: {raw_url} -> {self.public_url}")

            # Start the tunnel in a daemon thread, passing 127.0.0.1 as local_host
            # to prevent Windows IPv6 localhost connection refusal (WinError 10061)
            threading.Thread(
                target=self.tunnel.create_tunnel,
                args=(self.port, "127.0.0.1"),
                daemon=True
            ).start()
        except Exception as e:
            self._log(f"Failed to start localtunnel: {e}")
            self.public_url = None

        # Also start discovery loop for LAN discovery compatibility
        threading.Thread(target=self._discovery_loop, daemon=True).start()

    def _run_server(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        async def main():
            self.server = await websockets.serve(self._handler, "0.0.0.0", self.port)
            self._log(f"WebSocket server listening on port {self.port}")
            self.server_ready.set()
            while self.running:
                await asyncio.sleep(0.1)
            self.server.close()
            await self.server.wait_closed()

        try:
            self.loop.run_until_complete(main())
        except Exception as e:
            self._log(f"Server thread error: {e}")
            if not self.server_ready.is_set():
                self.server_ready.set()
        finally:
            self.loop.close()

    async def _handler(self, websocket):
        with self.lock:
            cid = self._next_id
            self._next_id += 1
            self.clients.append(websocket)
            self.client_ids[cid] = websocket
            self._conn_to_id[websocket] = cid

        self._log(f"Client {cid} connected")

        # Send initial assignments (ID assignment and player index)
        try:
            await websocket.send(json.dumps({"type": "assign_id", "id": cid}))
            await websocket.send(json.dumps({"type": "player_index", "index": cid + 1}))
        except Exception as e:
            self._log(f"Failed to send initial messages to Client {cid}: {e}")

        try:
            async for message in websocket:
                try:
                    msg = json.loads(message)
                except json.JSONDecodeError:
                    continue
                msg["_from"] = cid
                with self.lock:
                    self.inbox.append(msg)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            with self.lock:
                if websocket in self.clients:
                    self.clients.remove(websocket)
                self.client_ids.pop(cid, None)
                self._conn_to_id.pop(websocket, None)
            self._log(f"Client {cid} disconnected")

    def _send(self, websocket, msg):
        if self.loop and self.loop.is_running():
            async def send_coro():
                try:
                    await websocket.send(json.dumps(msg))
                except Exception:
                    pass
            asyncio.run_coroutine_threadsafe(send_coro(), self.loop)

    def broadcast(self, msg):
        with self.lock:
            targets = list(self.clients)
        for ws in targets:
            self._send(ws, msg)

    def send_to(self, cid, msg):
        with self.lock:
            ws = self.client_ids.get(cid)
        if ws is not None:
            self._send(ws, msg)

    def poll(self):
        with self.lock:
            msgs = list(self.inbox)
            self.inbox.clear()
        return msgs

    def get_connected_clients_info(self):
        with self.lock:
            info = []
            for ws, cid in self._conn_to_id.items():
                try:
                    # Retrieve the client's peer IP address
                    ip = ws.remote_address[0]
                except Exception:
                    ip = "unknown"
                info.append((cid, ip))
            return info

    def stop(self):
        self.running = False
        if self.tunnel:
            try:
                self.tunnel.stop_tunnel()
            except Exception:
                pass

        if self.loop and self.loop.is_running():
            with self.lock:
                clients = list(self.clients)
            async def close_all():
                for ws in clients:
                    try:
                        await ws.close()
                    except Exception:
                        pass
            asyncio.run_coroutine_threadsafe(close_all(), self.loop)

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

        def rank(ip):
            if ip.startswith("192.168."):
                return 0
            if ip.startswith("10."):
                return 1
            if ip.startswith("172."):
                return 2
            return 3

        return sorted(ips, key=rank) or ["127.0.0.1"]

    def _discovery_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("", settings.LAN_DISCOVERY_PORT))
        except OSError:
            return
        sock.settimeout(1.0)
        while self.running:
            try:
                data, addr = sock.recvfrom(256)
                if data.decode("utf-8", errors="ignore").startswith("DISCOVER_REQUEST"):
                    sock.sendto(b"DISCOVER_RESPONSE", (addr[0], settings.LAN_DISCOVERY_PORT + 1))
            except socket.timeout:
                continue
            except OSError:
                break
        sock.close()


class NetworkClient:
    def __init__(self):
        self.running = False
        self.lock = threading.Lock()
        self.inbox = []
        self.my_id = None
        self.websocket = None
        self.loop = None

    def _log(self, msg):
        if getattr(settings, "DEBUG_NETWORK", False):
            print(f"[Client] {msg}")

    def connect(self, host, port=settings.LAN_PORT):
        self._log(f"Connecting to {host}:{port}")
        self.running = True

        # Resolve WebSocket URL
        host_lower = host.lower()
        if host_lower.startswith("wss://") or host_lower.startswith("ws://"):
            url = host
        elif host_lower.startswith("https://"):
            url = host.replace("https://", "wss://")
        elif host_lower.startswith("http://"):
            url = host.replace("http://", "ws://")
        elif "loca.lt" in host_lower:
            url = f"wss://{host_lower}"
        else:
            if ":" in host:
                url = f"ws://{host}"
            else:
                url = f"ws://{host}:{port}"

        self._log(f"Resolved WebSocket URL: {url}")

        connected_event = threading.Event()
        error_container = []

        threading.Thread(
            target=self._run_client,
            args=(url, connected_event, error_container),
            daemon=True
        ).start()

        # Wait for ID assignment from host
        deadline = time.time() + settings.LAN_TIMEOUT
        while time.time() < deadline:
            if error_container:
                self.disconnect()
                raise ConnectionError(f"Failed to connect: {error_container[0]}")
            if self.my_id is not None:
                return
            time.sleep(0.05)

        self.disconnect()
        raise ConnectionError(f"Connection to {url} timed out or no ID assigned")

    def _run_client(self, url, connected_event, error_container):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        async def main():
            try:
                async with websockets.connect(url) as ws:
                    self.websocket = ws
                    connected_event.set()

                    async for message in ws:
                        try:
                            msg = json.loads(message)
                        except json.JSONDecodeError:
                            continue
                        if msg.get("type") == "assign_id":
                            self.my_id = msg.get("id")
                        else:
                            with self.lock:
                                self.inbox.append(msg)
            except Exception as e:
                if not connected_event.is_set():
                    error_container.append(e)
                    connected_event.set()
                self._log(f"Connection error: {e}")

        try:
            self.loop.run_until_complete(main())
        finally:
            self.running = False
            self.websocket = None
            self.loop.close()

    def send(self, msg):
        if not self.websocket or not self.running:
            return
        if self.loop and self.loop.is_running():
            async def send_coro():
                try:
                    await self.websocket.send(json.dumps(msg))
                except Exception:
                    pass
            asyncio.run_coroutine_threadsafe(send_coro(), self.loop)

    def poll(self):
        with self.lock:
            msgs = list(self.inbox)
            self.inbox.clear()
        return msgs

    def disconnect(self):
        self.running = False
        if self.websocket:
            if self.loop and self.loop.is_running():
                async def close_coro():
                    try:
                        await self.websocket.close()
                    except Exception:
                        pass
                asyncio.run_coroutine_threadsafe(close_coro(), self.loop)


class LANDiscovery:
    def __init__(self, port=settings.LAN_PORT):
        self.port = port
        self.hosts = []
        self.running = False
        self.scan_thread = None

    def _log(self, msg):
        if getattr(settings, "DEBUG_NETWORK", False):
            print(f"[Discovery] {msg}")

    def start_scan(self):
        self.running = True
        self.hosts = []
        self.scan_thread = threading.Thread(target=self._scan, daemon=True)
        self.scan_thread.start()

    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except OSError:
            return "127.0.0.1"

    def _scan(self):
        local_ip = self._get_local_ip()
        prefix = ".".join(local_ip.split(".")[:3])
        targets = [f"{prefix}.{i}" for i in range(1, 255) if f"{prefix}.{i}" != local_ip]

        for ip in targets:
            if not self.running:
                break
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.08)
                s.connect((ip, self.port))
                s.close()
                if ip not in self.hosts:
                    self.hosts.append(ip)
            except (socket.timeout, ConnectionError, OSError):
                continue

    def stop_scan(self):
        self.running = False
