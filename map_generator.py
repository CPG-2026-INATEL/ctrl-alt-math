import random
import math

import settings

ENEMY_POOL_BY_DIFFICULTY = {
    1: [("censor", 1, 2)],
    2: [("censor", 1, 2), ("ortogonal", 1, 1)],
    3: [("censor", 1, 2), ("ortogonal", 1, 1), ("atirador", 1, 1), ("strawman", 1, 1)],
    4: [("censor", 2, 3), ("ortogonal", 1, 2), ("atirador", 1, 2), ("strawman", 1, 1), ("granadeiro", 1, 1), ("bayesian", 1, 1)],
}

OBSTACLE_TEMPLATES = {
    1: [
        [{"col": 4, "row": 3, "w": 2, "h": 1}],
        [{"col": 10, "row": 5, "w": 2, "h": 2}],
    ],
    2: [
        [{"col": 3, "row": 2, "w": 2, "h": 2}, {"col": 11, "row": 7, "w": 2, "h": 2}],
        [{"col": 5, "row": 4, "w": 2, "h": 3}, {"col": 9, "row": 3, "w": 1, "h": 1}],
    ],
    3: [
        [{"col": 3, "row": 2, "w": 2, "h": 2}, {"col": 11, "row": 2, "w": 2, "h": 2}, {"col": 7, "row": 6, "w": 2, "h": 2}],
        [{"col": 5, "row": 3, "w": 3, "h": 1}, {"col": 2, "row": 7, "w": 2, "h": 2}, {"col": 12, "row": 7, "w": 2, "h": 2}],
    ],
    4: [
        [{"col": 3, "row": 1, "w": 2, "h": 2}, {"col": 11, "row": 1, "w": 2, "h": 2}, {"col": 7, "row": 4, "w": 2, "h": 3}, {"col": 3, "row": 8, "w": 2, "h": 2}],
        [{"col": 5, "row": 2, "w": 2, "h": 2}, {"col": 9, "row": 5, "w": 2, "h": 3}, {"col": 2, "row": 7, "w": 2, "h": 2}, {"col": 12, "row": 7, "w": 2, "h": 2}],
    ],
}

ROOM_NAMES = {
    1: ["room_hall_name", "room_library_name", "room_archive_name", "room_study_name"],
    2: ["room_gallery_name", "room_vault_name", "room_logic_name", "room_lab_name"],
    3: ["room_maze_name", "room_tower_name", "room_dungeon_name", "room_sanctuary_name"],
    4: ["room_fortress_name", "room_citadel_name", "room_stronghold_name"],
}

ROOM_NARRATIVES = {
    1: ["room_hall_narr", "room_library_narr", "room_archive_narr", "room_study_narr"],
    2: ["room_gallery_narr", "room_vault_narr", "room_logic_narr", "room_lab_narr"],
    3: ["room_maze_narr", "room_tower_narr", "room_dungeon_narr", "room_sanctuary_narr"],
    4: ["room_fortress_narr", "room_citadel_narr", "room_stronghold_narr"],
}

ARENA_SIZES = {
    1: (12, 9),
    2: (14, 10),
    3: (14, 10),
    4: (16, 12),
}


class MapGenerator:
    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.randint(0, 999999)
        self.rng = random.Random(self.seed)

    def generate(self, difficulty=None):
        if difficulty is None:
            difficulty = settings.DIFFICULTY
        difficulty_params = settings.DIFFICULTY_SCALING[difficulty]
        depth = difficulty_params.get("depth", 5)
        max_branches = difficulty_params.get("max_branches", 3)

        return self._build_dag(depth, max_branches, difficulty)

    def _build_dag(self, depth, max_branches, difficulty):
        rng = self.rng
        rooms = {}
        connections = {}

        hub_id = "hub"
        rooms[hub_id] = {
            "id": hub_id,
            "layer": 0,
            "row": 0,
            "difficulty": 1,
            "type": "hub",
            "name": "room_archive_name",
            "narrative": "room_archive_narr",
            "enemies": [],
            "obstacles": [],
            "gold_reward": 0,
            "is_start": True,
            "is_final": False,
            "boss_hp": settings.BOSS_HP,
        }
        connections[hub_id] = []

        layers = [[] for _ in range(depth + 1)]
        layers[0].append(hub_id)

        room_counter = 1
        used_names = {d: [] for d in range(1, 5)}

        for layer_idx in range(1, depth + 1):
            if layer_idx == depth:
                num_rooms = 1
            else:
                min_rooms = 1
                max_rooms = max_branches
                room_scale = layer_idx / depth
                max_for_layer = max(1, int(max_branches * (0.5 + 0.5 * room_scale)))
                num_rooms = rng.randint(min_rooms, min(max_for_layer, max_branches))

            layer_room_ids = []
            for i in range(num_rooms):
                room_id = f"room_{layer_idx}_{i}"

                if layer_idx == depth:
                    diff = 4
                    rtype = "boss"
                elif layer_idx <= 2:
                    diff = rng.choice([1, 1, 2])
                    rtype = "normal"
                elif layer_idx <= depth - 2:
                    diff = rng.choice([2, 2, 3])
                    rtype = rng.choice(["normal", "challenge"])
                else:
                    diff = rng.choice([3, 3, 4])
                    rtype = rng.choice(["challenge", "boss" if layer_idx == depth - 1 else "normal"])

                name_list = ROOM_NAMES.get(diff, ROOM_NAMES[1])
                available_names = [n for n in name_list if n not in used_names[diff]]
                if not available_names:
                    name_list = ROOM_NAMES.get(max(1, diff - 1), ROOM_NAMES[1])
                    available_names = list(name_list)
                name_key = rng.choice(available_names)
                used_names[diff].append(name_key)

                narr_list = ROOM_NARRATIVES.get(diff, ROOM_NARRATIVES[1])
                narr_key = rng.choice(narr_list)

                enemies = self._generate_enemies(diff, rng)
                obstacles = self._generate_obstacles(diff, rng)
                gold_reward = self._calculate_gold(diff)

                if rtype == "boss":
                    boss_hp = settings.BOSS_HP
                    enemies = [("boss", 1)]
                    arena_size = ARENA_SIZES[4]
                else:
                    boss_hp = settings.BOSS_HP
                    arena_size = ARENA_SIZES.get(diff, ARENA_SIZES[1])

                rooms[room_id] = {
                    "id": room_id,
                    "layer": layer_idx,
                    "row": i,
                    "difficulty": diff,
                    "type": rtype,
                    "name": name_key,
                    "narrative": narr_key,
                    "enemies": enemies,
                    "obstacles": obstacles,
                    "gold_reward": gold_reward,
                    "is_start": False,
                    "is_final": layer_idx == depth,
                    "boss_hp": boss_hp,
                    "arena_cols": arena_size[0],
                    "arena_rows": arena_size[1],
                }
                connections[room_id] = []
                layer_room_ids.append(room_id)
                room_counter += 1

            layers[layer_idx] = layer_room_ids

            prev_layer = layers[layer_idx - 1]
            for room_id in layer_room_ids:
                num_parents = rng.randint(1, min(2, len(prev_layer)))
                parents = rng.sample(prev_layer, min(num_parents, len(prev_layer)))
                for parent in parents:
                    if room_id not in connections[parent]:
                        connections[parent].append(room_id)

            for parent_id in prev_layer:
                if parent_id in connections and not connections[parent_id]:
                    child = rng.choice(layer_room_ids)
                    connections[parent_id].append(child)

            for i in range(len(layer_room_ids) - 1):
                if i + 1 < len(layer_room_ids):
                    connections[layer_room_ids[i]].append(layer_room_ids[i + 1])

        for layer_idx in range(depth + 1):
            for room_id in layers[layer_idx]:
                for conn_id in connections.get(room_id, []):
                    if conn_id in rooms:
                        if room_id not in rooms[conn_id].get("back_connections", []):
                            if "back_connections" not in rooms[conn_id]:
                                rooms[conn_id]["back_connections"] = []
                            rooms[conn_id]["back_connections"].append(room_id)

        for room_id, room_data in rooms.items():
            if "back_connections" in room_data:
                all_conns = list(set(connections.get(room_id, []) + room_data["back_connections"]))
                room_data["connections_out"] = connections.get(room_id, [])
                room_data["connections_in"] = room_data["back_connections"]
                room_data["all_connections"] = all_conns
            else:
                room_data["connections_out"] = connections.get(room_id, [])
                room_data["connections_in"] = []
                room_data["all_connections"] = connections.get(room_id, [])
            if "back_connections" in room_data:
                del room_data["back_connections"]

        start = rooms[hub_id]
        for conn_id in start.get("connections_out", []):
            if conn_id in rooms:
                rooms[conn_id]["state"] = "available"

        total_rooms = len(layers)
        for layer_idx, layer in enumerate(layers):
            for i, room_id in enumerate(layer):
                room_data = rooms[room_id]
                room_data["col"] = layer_idx
                max_row = max(len(l) for l in layers) - 1
                row_count = len(layer)
                if row_count == 1:
                    room_data["row"] = 0
                else:
                    room_data["row"] = i - (row_count - 1) // 2

        return rooms, connections, layers

    def _generate_enemies(self, difficulty, rng):
        pool = ENEMY_POOL_BY_DIFFICULTY.get(difficulty, ENEMY_POOL_BY_DIFFICULTY[1])
        enemies = []
        for enemy_type, min_count, max_count in pool:
            count = rng.randint(min_count, max_count)
            if count > 0:
                enemies.append((enemy_type, count))
        return enemies

    def _generate_obstacles(self, difficulty, rng):
        templates = OBSTACLE_TEMPLATES.get(difficulty, OBSTACLE_TEMPLATES[1])
        template = rng.choice(templates)
        return [obs.copy() for obs in template]

    def _calculate_gold(self, difficulty):
        base = settings.GOLD_PER_STAR.get(difficulty, 20)
        return base