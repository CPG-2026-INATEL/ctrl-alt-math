import json
import socket
import threading

import settings
from network import generate_room_code


class MatchServer:
    def __init__(self, host="0.0.0.0", port=settings.MATCH_SERVER_PORT):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.lock = threading.Lock()
        self.clients = {}
        self.rooms = {}
        self.client_rooms = {}
        self.next_client_id = 1

    def _log(self, msg):
        print(f"[Server] {msg}")

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(16)
        self.server_socket.settimeout(1.0)
        self.running = True
        self._log(f"Listening on {self.host}:{self.port}")
        try:
            while self.running:
                try:
                    conn, addr = self.server_socket.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break
                conn.settimeout(settings.LAN_TIMEOUT)
                with self.lock:
                    client_id = self.next_client_id
                    self.next_client_id += 1
                    self.clients[client_id] = {"conn": conn, "addr": addr}
                threading.Thread(target=self._client_loop, args=(client_id,), daemon=True).start()
                self._log(f"Client {client_id} connected from {addr[0]}")
        finally:
            self.stop()

    def stop(self):
        self.running = False
        try:
            if self.server_socket:
                self.server_socket.close()
        except OSError:
            pass
        with self.lock:
            clients = list(self.clients.items())
            self.clients.clear()
            self.rooms.clear()
            self.client_rooms.clear()
        for _, info in clients:
            try:
                info["conn"].close()
            except OSError:
                pass

    def _client_loop(self, client_id):
        with self.lock:
            info = self.clients.get(client_id)
        if not info:
            return
        conn = info["conn"]
        buffer = ""
        try:
            while self.running:
                try:
                    data = conn.recv(settings.LAN_BUFFER_SIZE)
                except socket.timeout:
                    continue
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
                    self._handle_message(client_id, msg)
        finally:
            self._remove_client(client_id)

    def _handle_message(self, client_id, msg):
        mtype = msg.get("type")
        if mtype == "create_room":
            self._create_room(client_id)
        elif mtype == "join_room":
            self._join_room(client_id, msg.get("room", ""))
        elif mtype == "relay":
            self._relay(client_id, msg.get("payload", {}))

    def _create_room(self, client_id):
        with self.lock:
            if client_id in self.client_rooms:
                self._send(client_id, {"type": "error", "message": "Already in a room"})
                return
            room_code = generate_room_code()
            while room_code in self.rooms:
                room_code = generate_room_code()
            self.rooms[room_code] = [client_id]
            self.client_rooms[client_id] = room_code
        self._send(client_id, {"type": "room_created", "room": room_code, "player_index": 1})

    def _join_room(self, client_id, room_code):
        room_code = (room_code or "").strip().upper()
        with self.lock:
            room = self.rooms.get(room_code)
            if room is None:
                self._send(client_id, {"type": "error", "message": "Room not found"})
                return
            if len(room) >= settings.LAN_MAX_PLAYERS:
                self._send(client_id, {"type": "error", "message": "Room is full"})
                return
            if client_id in self.client_rooms:
                self._send(client_id, {"type": "error", "message": "Already in a room"})
                return
            room.append(client_id)
            self.client_rooms[client_id] = room_code
            host_id = room[0]
            peer_ip = self.clients[client_id]["addr"][0]
        self._send(client_id, {"type": "room_joined", "room": room_code, "player_index": 2})
        self._send(host_id, {"type": "peer_joined", "player_index": 2, "peer_ip": peer_ip})

    def _relay(self, client_id, payload):
        with self.lock:
            room_code = self.client_rooms.get(client_id)
            if not room_code:
                return
            room = list(self.rooms.get(room_code, []))
        from_player = room.index(client_id) + 1 if client_id in room else None
        for peer_id in room:
            if peer_id != client_id:
                self._send(peer_id, {"type": "relay", "from_player": from_player, "payload": payload})

    def _remove_client(self, client_id):
        with self.lock:
            info = self.clients.pop(client_id, None)
            room_code = self.client_rooms.pop(client_id, None)
            peer_ids = []
            if room_code and room_code in self.rooms:
                room = self.rooms[room_code]
                if client_id in room:
                    room.remove(client_id)
                peer_ids = list(room)
                if room:
                    self.rooms[room_code] = room
                else:
                    self.rooms.pop(room_code, None)
        for peer_id in peer_ids:
            self._send(peer_id, {"type": "peer_left", "player_index": 2})
        if info:
            try:
                info["conn"].close()
            except OSError:
                pass
            self._log(f"Client {client_id} disconnected")

    def _send(self, client_id, msg):
        with self.lock:
            info = self.clients.get(client_id)
        if not info:
            return
        raw = (json.dumps(msg) + "\n").encode("utf-8")
        try:
            info["conn"].sendall(raw)
        except (ConnectionError, OSError):
            pass


if __name__ == "__main__":
    MatchServer().start()
