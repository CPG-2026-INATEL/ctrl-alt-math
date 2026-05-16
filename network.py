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
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("", self.port))
        self.server_socket.listen(1)
        self.server_socket.settimeout(1.0)
        self.running = True
        self.accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.accept_thread.start()

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

    def _scan(self):
        local_ip = self._get_local_ip()
        prefix = ".".join(local_ip.split(".")[:3])
        for i in range(1, 255):
            if not self.running:
                break
            ip = f"{prefix}.{i}"
            if ip == local_ip:
                continue
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.1)
                s.connect((ip, self.port))
                s.close()
                self.hosts.append(ip)
            except (socket.timeout, ConnectionError, OSError):
                continue

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