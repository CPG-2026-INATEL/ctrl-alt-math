import json
import os

import settings


SAVE_PATH = os.path.join(os.path.dirname(__file__), "savegame.json")


def save_exists():
    return os.path.exists(SAVE_PATH)


def _serialize_player(player):
    return {
        "hp": player.hp,
        "max_hp": player.max_hp,
        "base_damage": player.base_damage,
        "rigor": player.rigor,
        "max_rigor": player.max_rigor,
        "level": player.level,
        "exp": player.exp,
        "next_level_exp": player.next_level_exp,
        "move_range": player.move_range,
        "upgrade_tickets": player.upgrade_tickets,
        "defense": player.defense,
        "upgrades": dict(player.upgrades),
        "gold": player.gold,
        "inventory": [dict(item) for item in player.inventory],
        "equipment": dict(player.equipment),
        "buffs": [dict(buff) for buff in player.buffs],
        "skin_index": player.skin_index,
        "pitagoras_cooldown": getattr(player, "pitagoras_cooldown", 0),
        "reflexao_cooldown": getattr(player, "reflexao_cooldown", 0),
        "integral_cooldown": getattr(player, "integral_cooldown", 0),
        "fractal_cooldown": getattr(player, "fractal_cooldown", 0),
    }


def _apply_player(player, data):
    player.hp = data.get("hp", player.hp)
    player.max_hp = data.get("max_hp", player.max_hp)
    player.base_damage = data.get("base_damage", player.base_damage)
    player.rigor = data.get("rigor", player.rigor)
    player.max_rigor = data.get("max_rigor", player.max_rigor)
    player.level = data.get("level", player.level)
    player.exp = data.get("exp", player.exp)
    player.next_level_exp = data.get("next_level_exp", player.next_level_exp)
    player.move_range = data.get("move_range", player.move_range)
    player.upgrade_tickets = data.get("upgrade_tickets", player.upgrade_tickets)
    player.defense = data.get("defense", player.defense)
    player.upgrades = dict(data.get("upgrades", player.upgrades))
    player.gold = data.get("gold", player.gold)
    player.inventory = [dict(item) for item in data.get("inventory", [])]
    player.equipment = dict(data.get("equipment", player.equipment))
    player.buffs = [dict(buff) for buff in data.get("buffs", [])]
    player.skin_index = data.get("skin_index", player.skin_index)
    player.pitagoras_cooldown = data.get("pitagoras_cooldown", getattr(player, "pitagoras_cooldown", 0))
    player.reflexao_cooldown = data.get("reflexao_cooldown", getattr(player, "reflexao_cooldown", 0))
    player.integral_cooldown = data.get("integral_cooldown", getattr(player, "integral_cooldown", 0))
    player.fractal_cooldown = data.get("fractal_cooldown", getattr(player, "fractal_cooldown", 0))


def save_game(game):
    data = {
        "language": settings.LANGUAGE,
        "difficulty": settings.DIFFICULTY,
        "entropy": game.entropy,
        "gold": game.gold,
        "players": [_serialize_player(player) for player in game.players],
        "skill_tree": {
            "skill_points": game.skill_tree.skill_points,
            "levels": {skill_id: skill["level"] for skill_id, skill in game.skill_tree.skills.items()},
        },
        "world_map": game.world_map.get_state_data(),
    }
    with open(SAVE_PATH, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def load_game(game):
    if not save_exists():
        return False

    with open(SAVE_PATH, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    settings.LANGUAGE = data.get("language", settings.LANGUAGE)
    settings.DIFFICULTY = data.get("difficulty", settings.DIFFICULTY)

    game.reset_game_state()
    game.entropy = data.get("entropy", 0)
    game.gold = data.get("gold", 0)

    for player, player_data in zip(game.players, data.get("players", [])):
        _apply_player(player, player_data)

    game.player = game.players[0]
    game.player2 = game.players[1] if len(game.players) > 1 else game.players[0]
    game.gold = game.player.gold

    skill_tree = data.get("skill_tree", {})
    game.skill_tree.skill_points = skill_tree.get("skill_points", game.skill_tree.skill_points)
    for skill_id, level in skill_tree.get("levels", {}).items():
        if skill_id in game.skill_tree.skills:
            game.skill_tree.skills[skill_id]["level"] = level

    game.world_map.apply_state_data(data.get("world_map", {}))
    game.world_map._game = game
    game.current_room = None
    return True
