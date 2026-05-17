import random
import math

import settings

ENEMY_POOL_BY_DIFFICULTY = {
    1: [("censor", 2, 3)],
    2: [("censor", 1, 2), ("ortogonal", 1, 2)],
    3: [("censor", 2, 3), ("ortogonal", 1, 2), ("atirador", 1, 2), ("strawman", 1, 1)],
    4: [("censor", 3, 4), ("ortogonal", 2, 3), ("atirador", 1, 2), ("strawman", 1, 2), ("granadeiro", 1, 2), ("bayesian", 1, 1)],
}

CTF_ENEMY_POOL = {
    1: [("censor", 3, 4)],
    2: [("censor", 2, 3), ("ortogonal", 2, 3)],
    3: [("censor", 2, 4), ("ortogonal", 2, 3), ("atirador", 1, 2), ("strawman", 1, 2)],
    4: [("censor", 3, 5), ("ortogonal", 2, 4), ("atirador", 2, 3), ("strawman", 1, 2), ("granadeiro", 1, 2), ("bayesian", 1, 1)],
}

OBSTACLE_TEMPLATES = {
    1: [
        [{"col": 4, "row": 3, "w": 2, "h": 1}],
        [{"col": 10, "row": 5, "w": 2, "h": 2}],
        [{"col": 6, "row": 3, "w": 1, "h": 3}],
    ],
    2: [
        [{"col": 3, "row": 2, "w": 2, "h": 2}, {"col": 11, "row": 7, "w": 2, "h": 2}],
        [{"col": 5, "row": 4, "w": 2, "h": 3}, {"col": 9, "row": 3, "w": 1, "h": 1}],
        [{"col": 2, "row": 2, "w": 3, "h": 1}, {"col": 12, "row": 6, "w": 1, "h": 3}],
        [{"col": 7, "row": 3, "w": 1, "h": 2}, {"col": 7, "row": 7, "w": 1, "h": 2}],
        [{"col": 4, "row": 2, "w": 1, "h": 5}, {"col": 11, "row": 4, "w": 1, "h": 4}],
    ],
    3: [
        [{"col": 3, "row": 2, "w": 2, "h": 2}, {"col": 11, "row": 2, "w": 2, "h": 2}, {"col": 7, "row": 6, "w": 2, "h": 2}],
        [{"col": 5, "row": 3, "w": 3, "h": 1}, {"col": 2, "row": 7, "w": 2, "h": 2}, {"col": 12, "row": 7, "w": 2, "h": 2}],
        [{"col": 3, "row": 2, "w": 1, "h": 4}, {"col": 8, "row": 2, "w": 1, "h": 3}, {"col": 12, "row": 4, "w": 1, "h": 4}],
        [{"col": 4, "row": 2, "w": 3, "h": 1}, {"col": 4, "row": 6, "w": 3, "h": 1}, {"col": 10, "row": 3, "w": 1, "h": 3}],
        [{"col": 2, "row": 3, "w": 2, "h": 2}, {"col": 6, "row": 2, "w": 2, "h": 1}, {"col": 10, "row": 5, "w": 2, "h": 2}],
    ],
    4: [
        [{"col": 3, "row": 1, "w": 2, "h": 2}, {"col": 11, "row": 1, "w": 2, "h": 2}, {"col": 7, "row": 4, "w": 2, "h": 3}, {"col": 3, "row": 8, "w": 2, "h": 2}],
        [{"col": 5, "row": 2, "w": 2, "h": 2}, {"col": 9, "row": 5, "w": 2, "h": 3}, {"col": 2, "row": 7, "w": 2, "h": 2}, {"col": 12, "row": 7, "w": 2, "h": 2}],
        [{"col": 2, "row": 2, "w": 1, "h": 5}, {"col": 7, "row": 1, "w": 1, "h": 3}, {"col": 12, "row": 2, "w": 1, "h": 5}, {"col": 5, "row": 7, "w": 3, "h": 1}],
        [{"col": 3, "row": 2, "w": 3, "h": 1}, {"col": 3, "row": 7, "w": 3, "h": 1}, {"col": 10, "row": 2, "w": 1, "h": 5}, {"col": 14, "row": 4, "w": 1, "h": 4}],
        [{"col": 4, "row": 1, "w": 2, "h": 2}, {"col": 8, "row": 3, "w": 1, "h": 3}, {"col": 12, "row": 1, "w": 2, "h": 2}, {"col": 6, "row": 7, "w": 2, "h": 2}],
    ],
}

ROOM_NAMES = {
    1: ["room_hall_name", "room_library_name", "room_archive_name", "room_study_name",
        "room_cloister_name", "room_atrium_name", "room_vestibule_name"],
    2: ["room_gallery_name", "room_vault_name", "room_logic_name", "room_lab_name",
        "room_archive_name", "room_observatory_name", "room_scriptorium_name"],
    3: ["room_maze_name", "room_tower_name", "room_dungeon_name", "room_sanctuary_name",
        "room_catacomb_name", "room_citadel_name"],
    4: ["room_fortress_name", "room_citadel_name", "room_stronghold_name"],
}

ROOM_NARRATIVES = {
    1: ["room_hall_narr", "room_library_narr", "room_archive_narr", "room_study_narr",
        "room_cloister_narr", "room_atrium_narr", "room_vestibule_narr"],
    2: ["room_gallery_narr", "room_vault_narr", "room_logic_narr", "room_lab_narr",
        "room_archive_narr", "room_observatory_narr", "room_scriptorium_narr"],
    3: ["room_maze_narr", "room_tower_narr", "room_dungeon_narr", "room_sanctuary_narr",
        "room_catacomb_narr", "room_citadel_narr"],
    4: ["room_fortress_narr", "room_citadel_narr", "room_stronghold_narr"],
}

ARENA_SIZES = {
    1: (12, 9),
    2: (14, 10),
    3: (14, 10),
    4: (16, 12),
}

CTF_ARENA_SIZES = {
    1: (16, 13),
    2: (18, 14),
    3: (18, 14),
    4: (20, 16),
}

SIDE_ROOM_NAMES = ["room_cloister_name", "room_atrium_name", "room_vestibule_name",
                    "room_study_name", "room_archive_name", "room_library_name"]
SIDE_ROOM_NARRATIVES = ["room_cloister_narr", "room_atrium_narr", "room_vestibule_narr",
                         "room_study_narr", "room_archive_narr", "room_library_narr"]


class MapGenerator:
    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.randint(0, 999999)
        self.rng = random.Random(self.seed)

    def generate(self, difficulty=None):
        if difficulty is None:
            difficulty = settings.DIFFICULTY
        difficulty_params = settings.DIFFICULTY_SCALING[difficulty]
        depth = difficulty_params.get("depth", 5)
        max_branches = difficulty_params.get("max_branches", 4)

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
            "jitter_x": 0,
            "jitter_y": 0,
            "objective": "kill_all",
            "arena_cols": 12,
            "arena_rows": 9,
        }
        connections[hub_id] = []

        layers = [[] for _ in range(depth + 1)]
        layers[0].append(hub_id)

        room_counter = 1
        used_names = {d: [] for d in range(1, 5)}

        for layer_idx in range(1, depth + 1):
            is_boss_layer = (layer_idx == depth)
            is_pre_boss = (layer_idx == depth - 1)
            if is_boss_layer:
                num_rooms = 1
            else:
                progress = layer_idx / depth
                diff_boost = 0 if settings.DIFFICULTY == "easy" else (1 if settings.DIFFICULTY == "medium" else 2)
                if progress < 0.5:
                    min_rooms = 2 + diff_boost
                    max_rooms = max_branches + diff_boost
                elif progress < 0.8:
                    min_rooms = 2 + diff_boost
                    max_rooms = max_branches + 1 + diff_boost
                else:
                    min_rooms = 1 + diff_boost
                    max_rooms = max(2, max_branches - 1) + diff_boost

                if is_pre_boss:
                    max_rooms = max(2, max_branches + diff_boost)
                    min_rooms = 2

                num_rooms = rng.randint(min_rooms, min(max_rooms, max_branches + 2))

            if is_boss_layer:
                _layer_max_ctf = 0
            else:
                _layer_max_ctf = max(1, int(math.ceil(num_rooms * 0.5)))
            _layer_ctf_count = 0

            layer_room_ids = []
            for i in range(num_rooms):
                room_id = f"room_{layer_idx}_{i}"

                if is_boss_layer:
                    diff = 4
                    rtype = "boss"
                elif layer_idx <= 2:
                    diff = rng.choice([1, 1, 1, 2])
                    rtype = "normal"
                elif progress < 0.5:
                    diff = rng.choice([1, 2, 2])
                    rtype = rng.choice(["normal", "normal", "challenge"])
                elif progress < 0.8:
                    diff = rng.choice([2, 2, 3])
                    rtype = rng.choice(["normal", "challenge"])
                else:
                    diff = rng.choice([3, 3, 4])
                    rtype = "challenge"

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

                jitter_x = rng.randint(-10, 10)
                jitter_y = rng.randint(-14, 14)

                if rtype == "boss":
                    boss_hp = settings.BOSS_HP
                    enemies = [("boss", 1)]
                    arena_size = ARENA_SIZES[4]
                    gold_reward = settings.GOLD_BOSS_REWARD
                    objective = "kill_all"
                else:
                    boss_hp = settings.BOSS_HP
                    enemy_mult = settings.DIFFICULTY_SCALING[settings.DIFFICULTY]["enemy_amount"]
                    if _layer_ctf_count < _layer_max_ctf and rng.random() < 0.35:
                        objective = "capture_flag"
                        enemies = self._generate_ctf_enemies(diff, rng)
                        arena_size = CTF_ARENA_SIZES.get(diff, CTF_ARENA_SIZES[1])
                        _layer_ctf_count += 1
                    else:
                        objective = "kill_all"
                        enemies = self._generate_enemies(diff, rng)
                        arena_size = ARENA_SIZES.get(diff, ARENA_SIZES[1])
                    gold_reward = self._calculate_gold(diff, enemies)

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
                    "is_final": is_boss_layer,
                    "boss_hp": boss_hp,
                    "arena_cols": arena_size[0],
                    "arena_rows": arena_size[1],
                    "jitter_x": jitter_x,
                    "jitter_y": jitter_y,
                    "objective": objective,
                }
                connections[room_id] = []
                layer_room_ids.append(room_id)
                room_counter += 1

            layers[layer_idx] = layer_room_ids

            prev_layer = layers[layer_idx - 1]

            for room_id in layer_room_ids:
                num_parents = 1 if rng.random() < 0.7 else min(2, len(prev_layer))
                parents = rng.sample(prev_layer, min(num_parents, len(prev_layer)))
                for parent in parents:
                    if room_id not in connections[parent]:
                        connections[parent].append(room_id)

            unconnected_parents = [pid for pid in prev_layer
                                   if pid in connections and not connections[pid]]
            for parent_id in unconnected_parents:
                if layer_room_ids:
                    child = rng.choice(layer_room_ids)
                    if child not in connections[parent_id]:
                        connections[parent_id].append(child)

            if len(layer_room_ids) > 1 and rng.random() < 0.2:
                i = rng.randint(0, len(layer_room_ids) - 2)
                if layer_room_ids[i + 1] not in connections[layer_room_ids[i]]:
                    connections[layer_room_ids[i]].append(layer_room_ids[i + 1])

            if not is_boss_layer and layer_idx >= 2:
                if settings.DIFFICULTY == "easy":
                    side_chance = 0.45 if layer_idx <= depth - 2 else 0.25
                elif settings.DIFFICULTY == "medium":
                    side_chance = 0.55 if layer_idx <= depth - 2 else 0.30
                else:
                    side_chance = 0.65 if layer_idx <= depth - 2 else 0.35
                if rng.random() < side_chance:
                    num_side = rng.randint(1, 2)
                    for _ in range(num_side):
                        side_idx = len(layer_room_ids) + len([
                            r for r in rooms.values()
                            if r.get("layer") == layer_idx and r.get("type") == "side"
                        ])
                        side_id = f"side_{layer_idx}_{side_idx}"
                        side_diff = rng.choice([1, 1, 2])

                        side_name_list = SIDE_ROOM_NAMES
                        available = [n for n in side_name_list if n not in used_names.get(side_diff, [])]
                        if available:
                            side_name = rng.choice(available)
                        else:
                            side_name = rng.choice(side_name_list)
                        used_names.setdefault(side_diff, []).append(side_name)
                        side_narr_list = SIDE_ROOM_NARRATIVES
                        side_narr = rng.choice(side_narr_list)

                        side_enemies = self._generate_enemies(side_diff, rng)
                        side_obstacles = self._generate_obstacles(side_diff, rng)

                        parent = rng.choice(prev_layer)
                        jitter_x = rng.randint(-8, 8)
                        jitter_y = rng.randint(-20, 20)

                        rooms[side_id] = {
                            "id": side_id,
                            "layer": layer_idx,
                            "row": len(layer_room_ids),
                            "difficulty": side_diff,
                            "type": "side",
                            "name": side_name,
                            "narrative": side_narr,
                            "enemies": side_enemies,
                            "obstacles": side_obstacles,
                            "gold_reward": self._calculate_gold(side_diff, side_enemies),
                            "is_start": False,
                            "is_final": False,
                            "boss_hp": settings.BOSS_HP,
                            "arena_cols": ARENA_SIZES[side_diff][0],
                            "arena_rows": ARENA_SIZES[side_diff][1],
                            "jitter_x": jitter_x,
                            "jitter_y": jitter_y,
                            "objective": "kill_all",
                        }
                        connections[side_id] = []

                        if side_id not in connections[parent]:
                            connections[parent].append(side_id)

                        next_layer_idx = min(layer_idx + 1, depth)
                        next_candidates = layers[next_layer_idx]
                        if next_candidates:
                            target = rng.choice(next_candidates)
                            if target not in connections[side_id]:
                                connections[side_id].append(target)

                        layer_room_ids.append(side_id)

            layers[layer_idx] = layer_room_ids

        for layer_idx, layer in enumerate(layers):
            for i, room_id in enumerate(layer):
                room_data = rooms[room_id]
                room_data["col"] = layer_idx
                row_count = len(layer)
                if row_count == 1:
                    room_data["row"] = 0
                else:
                    room_data["row"] = i - (row_count - 1) // 2

        for room_id, room_data in rooms.items():
            directional = {"left": None, "up": None, "right": None, "down": None}
            current_row = room_data.get("row", 0)

            incoming = []
            for pid, children in connections.items():
                if room_id in children and pid in rooms:
                    incoming.append(pid)
            if incoming:
                if len(incoming) == 1:
                    directional["left"] = incoming[0]
                else:
                    incoming.sort(key=lambda pid: abs(rooms[pid].get("row", 0) - current_row))
                    directional["left"] = incoming[0]

            outgoing = connections.get(room_id, [])
            targets = []
            for cid in outgoing:
                if cid in rooms:
                    targets.append((rooms[cid].get("row", 0), cid))

            if len(targets) == 1:
                directional["right"] = targets[0][1]
            elif len(targets) >= 2:
                targets.sort(key=lambda t: t[0] - current_row)
                mid = len(targets) // 2
                if len(targets) >= 3:
                    directional["up"] = targets[0][1]
                    directional["right"] = targets[1][1]
                    directional["down"] = targets[2][1]
                else:
                    if targets[0][0] < current_row:
                        directional["up"] = targets[0][1]
                    else:
                        directional["right"] = targets[0][1]
                    if targets[1][0] > current_row:
                        directional["down"] = targets[1][1]
                    else:
                        directional["right"] = targets[1][1]

            if directional["right"] is None and directional["up"] is not None:
                directional["right"] = directional["up"]
                directional["up"] = None
            if directional["right"] is None and directional["down"] is not None:
                directional["right"] = directional["down"]
                directional["down"] = None

            room_data["directional_connections"] = directional
            room_data["all_connections"] = [v for v in directional.values() if v is not None]

        start = rooms[hub_id]
        for d in ["up", "right", "down"]:
            conn_id = start["directional_connections"].get(d)
            if conn_id and conn_id in rooms:
                rooms[conn_id]["state"] = "available"

        return rooms, connections, layers

    def _generate_enemies(self, difficulty, rng):
        pool = ENEMY_POOL_BY_DIFFICULTY.get(difficulty, ENEMY_POOL_BY_DIFFICULTY[1])
        enemies = []
        for enemy_type, min_count, max_count in pool:
            count = rng.randint(min_count, max_count)
            if count > 0:
                enemies.append((enemy_type, count))
        return enemies

    def _generate_ctf_enemies(self, difficulty, rng):
        pool = CTF_ENEMY_POOL.get(difficulty, CTF_ENEMY_POOL[1])
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

    def _calculate_gold(self, difficulty, enemies):
        base = settings.GOLD_PER_STAR.get(difficulty, 20)
        gold_per_enemy = settings.GOLD_PER_ENEMY.get(difficulty, 5)
        total_enemies = sum(count for _, count in enemies)
        return base + total_enemies * gold_per_enemy