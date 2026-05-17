import json
import random
import socket
import string
import threading
import time

import settings


LAN_PORT = settings.LAN_PORT
LAN_DISCOVERY_PORT = getattr(settings, "LAN_DISCOVERY_PORT", LAN_PORT + 1)
LAN_BUFFER_SIZE = settings.LAN_BUFFER_SIZE
LAN_TIMEOUT = settings.LAN_TIMEOUT


class NetworkHost:
    def __init__(self, host=settings.MATCH_SERVER_HOST, port=settings.MATCH_SERVER_PORT):
        self.server_host = host
        self.server_port = port
        self.socket = None
        self.running = False
        self.lock = threading.Lock()
        self.inbox = []
        self.connected_clients = []
        self.my_id = None
        self.room_code = ""
        self.connection_error = None

    def _log(self, msg):
        if getattr(settings, "DEBUG_NETWORK", False):
            print(f"[Host] {msg}")

    def start(self):
        self._log(f"Connecting to match server {self.server_host}:{self.server_port}")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(LAN_TIMEOUT)
        self.socket.connect((self.server_host, self.server_port))
        self.socket.settimeout(LAN_TIMEOUT)
        self.running = True
        threading.Thread(target=self._recv_loop, daemon=True).start()
        self._send_raw({"type": "create_room"})

        deadline = time.time() + LAN_TIMEOUT
        while time.time() < deadline:
            if self.connection_error:
                self.stop()
                raise ConnectionError(self.connection_error)
            if self.room_code:
                return
            time.sleep(0.05)
        self.stop()
        raise ConnectionError("Could not create room on match server")

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
                    self._handle_server_msg(msg)
            except socket.timeout:
                continue
            except (ConnectionError, OSError):
                if not self.running:
                    break
        self.running = False

    def _handle_server_msg(self, msg):
        mtype = msg.get("type")
        if mtype == "room_created":
            self.room_code = msg.get("room", "")
            self.my_id = 1
            self._log(f"Created room {self.room_code}")
            return
        if mtype == "peer_joined":
            peer_ip = msg.get("peer_ip", "unknown")
            with self.lock:
                self.connected_clients = [(2, peer_ip)]
            return
        if mtype == "peer_left":
            with self.lock:
                self.connected_clients = []
            return
        if mtype == "relay":
            payload = msg.get("payload", {})
            payload["_from"] = msg.get("from_player", 2)
            with self.lock:
                self.inbox.append(payload)
            return
        if mtype == "error":
            self.connection_error = msg.get("message", "Match server error")

    def _send_raw(self, msg):
        if not self.socket:
            return
        raw = (json.dumps(msg) + "\n").encode("utf-8")
        try:
            self.socket.sendall(raw)
        except (ConnectionError, OSError):
            pass

    def broadcast(self, msg):
        self._send_raw({"type": "relay", "payload": msg})

    def send_to(self, cid, msg):
        if cid == 2:
            self.broadcast(msg)

    def poll(self):
        with self.lock:
            msgs = list(self.inbox)
            self.inbox.clear()
        return msgs

    def get_connected_clients_info(self):
        with self.lock:
            return list(self.connected_clients)

    def stop(self):
        self.running = False
        try:
            if self.socket:
                self.socket.close()
        except OSError:
            pass


class NetworkClient:
    def __init__(self):
        self.socket = None
        self.running = False
        self.lock = threading.Lock()
        self.inbox = []
        self.my_id = None
        self.room_code = ""
        self.player_index = None
        self.connection_error = None

    def _log(self, msg):
        if getattr(settings, "DEBUG_NETWORK", False):
            print(f"[Client] {msg}")

    def connect(self, host, port=LAN_PORT, room_code=None):
        if not room_code:
            raise ConnectionError("Room code is required")
        self._log(f"Connecting to match server {host}:{port} room {room_code}")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(LAN_TIMEOUT)
        self.socket.connect((host, port))
        self.socket.settimeout(LAN_TIMEOUT)
        self.running = True
        self.room_code = room_code.upper()
        threading.Thread(target=self._recv_loop, daemon=True).start()
        self.send({"type": "join_room", "room": self.room_code}, raw=True)

        deadline = time.time() + LAN_TIMEOUT
        while time.time() < deadline:
            if self.connection_error:
                self.disconnect()
                raise ConnectionError(self.connection_error)
            if self.my_id is not None:
                return
            time.sleep(0.05)
        self.disconnect()
        raise ConnectionError(f"Could not join room {self.room_code}")

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
                    self._handle_server_msg(msg)
            except socket.timeout:
                continue
            except (ConnectionError, OSError):
                if not self.running:
                    break
        self.running = False

    def _handle_server_msg(self, msg):
        mtype = msg.get("type")
        if mtype == "room_joined":
            self.my_id = 2
            self.player_index = 2
            self.room_code = msg.get("room", self.room_code)
            return
        if mtype == "relay":
            payload = msg.get("payload", {})
            payload["_from"] = msg.get("from_player", 1)
            with self.lock:
                self.inbox.append(payload)
            return
        if mtype == "error":
            self.connection_error = msg.get("message", "Match server error")
            with self.lock:
                self.inbox.append(msg)

    def send(self, msg, raw=False):
        if not self.socket:
            return
        outgoing = msg if raw else {"type": "relay", "payload": msg}
        raw_msg = (json.dumps(outgoing) + "\n").encode("utf-8")
        try:
            self.socket.sendall(raw_msg)
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

    def start_scan(self):
        self.running = True
        self.hosts = []

    def stop_scan(self):
        self.running = False


def generate_room_code(length=6):
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))
