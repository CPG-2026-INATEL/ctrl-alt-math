import json
import socket
import threading
import time

import settings

LAN_PORT = settings.LAN_PORT
LAN_DISCOVERY_PORT = getattr(settings, "LAN_DISCOVERY_PORT", LAN_PORT + 1)
LAN_BUFFER_SIZE = settings.LAN_BUFFER_SIZE
LAN_TIMEOUT = settings.LAN_TIMEOUT


class NetworkHost:
    def __init__(self, port=LAN_PORT):
        self.port = port
        self.server_socket = None
        self.running = False
        self.lock = threading.Lock()
        self.inbox = []
        self.clients = []
        self.client_ids = {}
        self._conn_to_id = {}
        self._next_id = 1

    def _log(self, msg):
        if getattr(settings, "DEBUG_NETWORK", False):
            print(f"[Host] {msg}")

    def start(self):
        self._log(f"Starting TCP host on port {self.port}")
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("", self.port))
        self.server_socket.listen(max(1, settings.LAN_MAX_PLAYERS - 1))
        self.server_socket.settimeout(1.0)
        self.running = True

        threading.Thread(target=self._accept_loop, daemon=True).start()
        threading.Thread(target=self._discovery_loop, daemon=True).start()

    def _accept_loop(self):
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            conn.settimeout(LAN_TIMEOUT)
            with self.lock:
                cid = self._next_id
                self._next_id += 1
                self.clients.append(conn)
                self.client_ids[cid] = conn
                self._conn_to_id[conn] = cid

            self._log(f"Client {cid} connected from {addr[0]}")
            self._send(conn, {"type": "assign_id", "id": cid})
            self._send(conn, {"type": "player_index", "index": cid + 1})
            threading.Thread(target=self._recv_loop, args=(conn,), daemon=True).start()

    def _recv_loop(self, conn):
        buffer = ""
        while self.running:
            try:
                data = conn.recv(LAN_BUFFER_SIZE)
                if not data:
                    break
                buffer += data.decode("utf-8")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msg = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    with self.lock:
                        cid = self._conn_to_id.get(conn)
                        if cid is not None:
                            msg["_from"] = cid
                        self.inbox.append(msg)
            except (socket.timeout, ConnectionError, OSError):
                break

        with self.lock:
            cid = self._conn_to_id.pop(conn, None)
            if conn in self.clients:
                self.clients.remove(conn)
            if cid is not None:
                self.client_ids.pop(cid, None)
        try:
            conn.close()
        except OSError:
            pass

    def _send(self, conn, msg):
        raw = (json.dumps(msg) + "\n").encode("utf-8")
        try:
            conn.sendall(raw)
        except (ConnectionError, OSError):
            pass

    def broadcast(self, msg):
        with self.lock:
            targets = list(self.clients)
        for conn in targets:
            self._send(conn, msg)

    def send_to(self, cid, msg):
        with self.lock:
            conn = self.client_ids.get(cid)
        if conn is not None:
            self._send(conn, msg)

    def poll(self):
        with self.lock:
            msgs = list(self.inbox)
            self.inbox.clear()
        return msgs

    def get_connected_clients_info(self):
        with self.lock:
            info = []
            for conn, cid in self._conn_to_id.items():
                try:
                    ip = conn.getpeername()[0]
                except OSError:
                    ip = "unknown"
                info.append((cid, ip))
            return info

    def stop(self):
        self.running = False
        try:
            if self.server_socket:
                self.server_socket.close()
        except OSError:
            pass
        with self.lock:
            for conn in self.clients:
                try:
                    conn.close()
                except OSError:
                    pass
            self.clients.clear()
            self.client_ids.clear()
            self._conn_to_id.clear()

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
            sock.bind(("", LAN_DISCOVERY_PORT))
        except OSError:
            return
        sock.settimeout(1.0)
        while self.running:
            try:
                data, addr = sock.recvfrom(256)
                if data.decode("utf-8", errors="ignore").startswith("DISCOVER_REQUEST"):
                    sock.sendto(b"DISCOVER_RESPONSE", (addr[0], LAN_DISCOVERY_PORT + 1))
            except socket.timeout:
                continue
            except OSError:
                break
        sock.close()


class NetworkClient:
    def __init__(self):
        self.socket = None
        self.running = False
        self.lock = threading.Lock()
        self.inbox = []
        self.my_id = None

    def _log(self, msg):
        if getattr(settings, "DEBUG_NETWORK", False):
            print(f"[Client] {msg}")

    def connect(self, host, port=LAN_PORT):
        self._log(f"Connecting to {host}:{port}")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(LAN_TIMEOUT)
        self.socket.connect((host, port))
        self.socket.settimeout(LAN_TIMEOUT)
        self.running = True
        threading.Thread(target=self._recv_loop, daemon=True).start()

        deadline = time.time() + LAN_TIMEOUT
        while time.time() < deadline:
            if self.my_id is not None:
                return
            time.sleep(0.05)
        raise ConnectionError(f"Could not connect to {host}:{port}")

    def _recv_loop(self):
        buffer = ""
        while self.running:
            try:
                data = self.socket.recv(LAN_BUFFER_SIZE)
                if not data:
                    break
                buffer += data.decode("utf-8")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msg = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if msg.get("type") == "assign_id":
                        self.my_id = msg.get("id")
                    else:
                        with self.lock:
                            self.inbox.append(msg)
            except (socket.timeout, ConnectionError, OSError):
                if not self.running:
                    break
        self.running = False

    def send(self, msg):
        if not self.socket:
            return
        raw = (json.dumps(msg) + "\n").encode("utf-8")
        try:
            self.socket.sendall(raw)
        except (ConnectionError, OSError):
            pass

    def poll(self):
        with self.lock:
            msgs = list(self.inbox)
            self.inbox.clear()
        return msgs

    def disconnect(self):
        self.running = False
        try:
            if self.socket:
                self.socket.close()
        except OSError:
            pass


class LANDiscovery:
    def __init__(self, port=LAN_PORT):
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
