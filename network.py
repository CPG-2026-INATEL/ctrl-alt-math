import json
import socket
import threading
import time

import settings

LAN_PORT = settings.LAN_PORT
LAN_BUFFER_SIZE = settings.LAN_BUFFER_SIZE
LAN_TIMEOUT = settings.LAN_TIMEOUT


class NetworkHost:
    def __init__(self, port=settings.LAN_PORT):
        self.port = port
        self.server_socket = None
        self.clients = []
        self.running = False
        self.lock = threading.Lock()
        self.inbox = []
        self.client_ids = {}
        self._next_id = 1

    def start(self):
        self._ensure_firewall_rules()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("", self.port))
        self.server_socket.listen(1)
        self.server_socket.settimeout(1.0)
        self.running = True
        self.accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.accept_thread.start()
        self.discovery_thread = threading.Thread(target=self._discovery_loop, daemon=True)
        self.discovery_thread.start()

    @staticmethod
    def _ensure_firewall_rules():
        """Try to add Windows Firewall rules for the game ports (silently fails if no admin)."""
        import subprocess, sys
        if sys.platform != "win32":
            return
        rules = [
            ("CtrlAltMath-TCP-In",  "TCP",  str(settings.LAN_PORT)),
            ("CtrlAltMath-UDP-In",  "UDP",  str(settings.LAN_DISCOVERY_PORT)),
            ("CtrlAltMath-UDP2-In", "UDP",  str(settings.LAN_DISCOVERY_PORT + 1)),
        ]
        for name, proto, port in rules:
            try:
                subprocess.run(
                    ["netsh", "advfirewall", "firewall", "add", "rule",
                     f"name={name}", "dir=in", "action=allow",
                     f"protocol={proto}", f"localport={port}",
                     "enable=yes", "profile=any"],
                    capture_output=True, timeout=3
                )
            except Exception:
                pass  # No admin rights or netsh not available — ignore

    def _accept_loop(self):
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                conn.settimeout(LAN_TIMEOUT)
                with self.lock:
                    cid = self._next_id
                    self._next_id += 1
                    self.client_ids[conn] = cid
                    self.clients.append(conn)
                self._send(conn, {"type": "assign_id", "id": cid})
                self._send(conn, {"type": "player_index", "index": len(self.clients)})
                t = threading.Thread(target=self._recv_loop, args=(conn, cid), daemon=True)
                t.start()
            except socket.timeout:
                continue
            except OSError:
                break

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
                text = data.decode("utf-8", errors="ignore")
                # New format: "DISCOVER_REQUEST:{reply_port}"
                if text.startswith("DISCOVER_REQUEST"):
                    reply_port = settings.LAN_DISCOVERY_PORT + 1  # default fallback
                    if ":" in text:
                        try:
                            reply_port = int(text.split(":", 1)[1])
                        except ValueError:
                            pass
                    sock.sendto(b"DISCOVER_RESPONSE", (addr[0], reply_port))
            except socket.timeout:
                continue
            except OSError:
                break
        sock.close()

    def _recv_loop(self, conn, cid):
        buf = ""
        while self.running:
            try:
                data = conn.recv(LAN_BUFFER_SIZE).decode("utf-8")
                if not data:
                    break
                buf += data
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    if line.strip():
                        try:
                            msg = json.loads(line)
                            msg["_from"] = cid
                            with self.lock:
                                self.inbox.append(msg)
                        except json.JSONDecodeError:
                            pass
            except (socket.timeout, ConnectionError, OSError):
                break
        with self.lock:
            if conn in self.clients:
                self.clients.remove(conn)
            self.client_ids.pop(conn, None)
        try:
            conn.close()
        except OSError:
            pass

    def broadcast(self, msg):
        data = json.dumps(msg) + "\n"
        with self.lock:
            dead = []
            for c in self.clients:
                try:
                    c.sendall(data.encode("utf-8"))
                except (ConnectionError, OSError):
                    dead.append(c)
            for c in dead:
                self.clients.remove(c)
                self.client_ids.pop(c, None)

    def send_to(self, cid, msg):
        with self.lock:
            for conn, id_ in list(self.client_ids.items()):
                if id_ == cid:
                    self._send(conn, msg)
                    break

    def _send(self, conn, msg):
        data = json.dumps(msg) + "\n"
        try:
            conn.sendall(data.encode("utf-8"))
        except (ConnectionError, OSError):
            pass

    def poll(self):
        with self.lock:
            msgs = list(self.inbox)
            self.inbox.clear()
        return msgs

    def stop(self):
        self.running = False
        try:
            self.server_socket.close()
        except OSError:
            pass
        with self.lock:
            for c in self.clients:
                try:
                    c.close()
                except OSError:
                    pass
            self.clients.clear()
            self.client_ids.clear()

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except OSError:
            return "127.0.0.1"

    def get_all_local_ips(self):
        """Return all non-loopback IPv4 addresses, sorted so 192.168.x.x comes first."""
        ips = set()
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None):
                ip = info[4][0]
                if ip.startswith("127.") or ":" in ip:
                    continue
                ips.add(ip)
        except OSError:
            pass
        # Also grab the default-route IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ips.add(s.getsockname()[0])
            s.close()
        except OSError:
            pass
        # Sort: 192.168.x.x first, then 10.x.x.x, then others
        def _rank(ip):
            if ip.startswith("192.168."):
                return 0
            if ip.startswith("10."):
                return 1
            if ip.startswith("172."):
                return 2
            return 3
        return sorted(ips, key=_rank) or ["127.0.0.1"]


class NetworkClient:
    def __init__(self):
        self.socket = None
        self.running = False
        self.lock = threading.Lock()
        self.inbox = []
        self.my_id = None

    def connect(self, host, port=settings.LAN_PORT):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(LAN_TIMEOUT)
        self.socket.connect((host, port))
        self.socket.settimeout(None)
        self.running = True
        self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self.recv_thread.start()

    def _recv_loop(self):
        buf = ""
        while self.running:
            try:
                data = self.socket.recv(LAN_BUFFER_SIZE).decode("utf-8")
                if not data:
                    break
                buf += data
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    if line.strip():
                        try:
                            msg = json.loads(line)
                            if msg.get("type") == "assign_id":
                                self.my_id = msg["id"]
                            else:
                                with self.lock:
                                    self.inbox.append(msg)
                        except json.JSONDecodeError:
                            pass
            except (ConnectionError, OSError):
                break
        self.running = False

    def send(self, msg):
        data = json.dumps(msg) + "\n"
        try:
            self.socket.sendall(data.encode("utf-8"))
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
            self.socket.close()
        except OSError:
            pass


class LANDiscovery:
    def __init__(self, port=settings.LAN_PORT):
        self.port = port
        self.hosts = []
        self.running = False
        self.scan_thread = None

    def start_scan(self):
        self.running = True
        self.hosts = []
        self.scan_thread = threading.Thread(target=self._scan, daemon=True)
        self.scan_thread.start()

    def _get_broadcast_addresses(self):
        """Return all directed broadcast addresses for every local interface."""
        addrs = set()
        try:
            # Use socket.getaddrinfo to enumerate all local IPs
            hostname = socket.gethostname()
            for info in socket.getaddrinfo(hostname, None):
                ip = info[4][0]
                if ip.startswith("127.") or ":" in ip:
                    continue
                parts = ip.split(".")
                # Directed broadcast: keep first 3 octets, last = 255
                addrs.add(".".join(parts[:3]) + ".255")
        except OSError:
            pass
        # Always include the generic broadcast as a fallback
        addrs.add("255.255.255.255")
        return list(addrs)

    def _scan(self):
        targets = self._get_broadcast_addresses()
        local_ip = self._get_local_ip()
        prefix = ".".join(local_ip.split(".")[:3])
        lock = threading.Lock()

        # ---- Strategy 1: UDP broadcast (fast on home networks) ----
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
                recv_sock.bind(("", settings.LAN_DISCOVERY_PORT + 1))
            except OSError:
                try:
                    recv_sock.bind(("", 0))
                except OSError:
                    pass
            reply_port = recv_sock.getsockname()[1]
            payload = f"DISCOVER_REQUEST:{reply_port}".encode()
            for _ in range(3):
                if not self.running:
                    break
                for bcast in targets:
                    try:
                        send_sock.sendto(payload, (bcast, settings.LAN_DISCOVERY_PORT))
                    except OSError:
                        pass
                deadline = time.time() + 0.5
                while time.time() < deadline:
                    try:
                        data, addr = recv_sock.recvfrom(256)
                        if data == b"DISCOVER_RESPONSE":
                            with lock:
                                if addr[0] not in self.hosts:
                                    self.hosts.append(addr[0])
                    except socket.timeout:
                        pass
                    except OSError:
                        break
            send_sock.close()
            recv_sock.close()

        # ---- Strategy 2: Parallel TCP scan (works when AP isolation blocks UDP) ----
        def tcp_check(ip):
            if not self.running:
                return
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.15)
                s.connect((ip, self.port))
                s.close()
                with lock:
                    if ip not in self.hosts:
                        self.hosts.append(ip)
            except (socket.timeout, ConnectionRefusedError, OSError):
                pass

        def tcp_scan():
            ips = [f"{prefix}.{i}" for i in range(1, 255) if f"{prefix}.{i}" != local_ip]
            # Scan in batches of 64 parallel threads
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