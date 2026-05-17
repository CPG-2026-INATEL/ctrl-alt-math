import os
import pygame

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60
LANGUAGE = "en"
TTS_ENABLED = True
TTS_RATE = 170
FULLSCREEN = False
BORDERLESS = True  # Borderless windowed - no display mode change, no Alt-Tab glitch
SHOW_LORE_TOASTS = True
DEBUG_NETWORK = True
MATCH_SERVER_HOST = os.getenv("CTRL_ALT_MATH_SERVER_HOST", "0.tcp.sa.ngrok.io")
MATCH_SERVER_PORT = int(os.getenv("CTRL_ALT_MATH_SERVER_PORT", "11749"))
MATCH_SERVER_BIND_HOST = os.getenv("CTRL_ALT_MATH_SERVER_BIND_HOST", "0.0.0.0")
MATCH_SERVER_BIND_PORT = int(os.getenv("CTRL_ALT_MATH_SERVER_BIND_PORT", "5555"))
BASE_WIDTH = 800
BASE_HEIGHT = 600
UI_SCALE = 1.0

DIFFICULTY_EASY = "easy"
DIFFICULTY_MEDIUM = "medium"
DIFFICULTY_HARD = "hard"
DIFFICULTY = DIFFICULTY_HARD

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 100, 255)
CYAN = (50, 255, 255)
YELLOW = (255, 255, 50)
ORANGE = (255, 150, 50)
PURPLE = (200, 50, 255)
PINK = (255, 100, 200)
GRAY = (100, 100, 100)
DARK_GRAY = (30, 30, 30)
LIGHT_GRAY = (180, 180, 180)
DARK_BLUE = (10, 10, 40)
DARK_RED = (60, 10, 10)
TEAL = (0, 128, 128)
GOLD = (255, 215, 0)
MAGENTA = (255, 0, 255)
BROWN = (150, 75, 0)
NAVY = (0, 0, 128)

PLAYER_SIZE = 14
PLAYER_SPEED = 220
PLAYER_MAX_HP = 100
PLAYER_MAX_RIGOR = 100
PLAYER_ATTACK_COOLDOWN = 0.3
PLAYER_ATTACK_DAMAGE = 15
PLAYER_CRIT_CHANCE = 0.15
PLAYER_CRIT_MULTIPLIER = 2.0
PLAYER_START_SKILL_POINTS = 2
RIGOR_REGEN_RATE = 15
RIGOR_REGEN_DELAY = 0

PLAYER_EXP_BASE = 100
PLAYER_EXP_GROWTH = 1.4
PLAYER_HP_PER_LEVEL = 0
PLAYER_DMG_PER_LEVEL = 0
PLAYER_SKILL_POINTS_PER_LEVEL = 1

UPGRADE_COSTS = {
    "atk":   {"base_cost": 30, "cost_scale": 1.5},
    "def":   {"base_cost": 25, "cost_scale": 1.4},
    "hp":    {"base_cost": 20, "cost_scale": 1.3},
    "range": {"base_cost": 40, "cost_scale": 1.6},
}
UPGRADE_PER_LEVEL = {"atk": 3, "def": 2, "hp": 15, "range": 1}

EQUIPMENT_DATA = {
    "weapons": {
        "basic_sword":   {"name": "Espada Basica",      "multiplier": 1.0,  "effect": None,      "desc": "Uma espada simples",       "cost": 0,   "sp_cost": 0},
        "fire_blade":    {"name": "Lamina de Fogo",      "multiplier": 1.12, "effect": "burn",   "desc": "Causa queimadura (3 dmg/2 turnos)",  "cost": 80,  "sp_cost": 0},
        "ice_rapier":    {"name": "Florete de Gelo",     "multiplier": 1.08, "effect": "slow",   "desc": "Reduz movimento do inimigo por 1 turno", "cost": 70,  "sp_cost": 0},
        "thunder_axe":   {"name": "Machado do Trovao",   "multiplier": 1.18, "effect": "stun",   "desc": "Chance de atordoar inimigo",  "cost": 100, "sp_cost": 0},
        "arcane_staff":  {"name": "Cajado Arcano",       "multiplier": 1.05, "effect": "aoe",    "desc": "Ataca inimigos adjacentes ao alvo", "cost": 60,  "sp_cost": 0},
        "shadow_dagger": {"name": "Adaga das Sombras",   "multiplier": 1.10, "effect": "poison", "desc": "2 dmg por 3 turnos (veneno)",  "cost": 85,  "sp_cost": 0},
        "heavy_axe":     {"name": "Machado Pesado",      "multiplier": 1.15, "effect": None,     "desc": "Dano alto sem efeito especial", "cost": 75,  "sp_cost": 0},
    },
    "shields": {
        "wooden_shield":  {"name": "Escudo de Madeira",   "defense": 3,  "effect": None,      "desc": "Protecao basica",           "cost": 0,   "sp_cost": 0},
        "iron_shield":    {"name": "Escudo de Ferro",     "defense": 6,  "effect": None,      "desc": "Protecao resistente",       "cost": 50,  "sp_cost": 0},
        "mirror_shield":  {"name": "Escudo Espelhado",    "defense": 4,  "effect": "reflect", "desc": "Reflete 25% do dano recebido", "cost": 65,  "sp_cost": 0},
        "steel_shield":   {"name": "Escudo de Aco",      "defense": 8,  "effect": None,      "desc": "Protecao maxima",           "cost": 90,  "sp_cost": 0},
    },
}

CONSUMABLE_DATA = {
    "hp_potion_small":  {"name": "Pocao de Vida",        "desc": "Restaura 30 HP",                     "effect": "heal",       "value": 30, "cost": 15, "sp_cost": 0, "scope": "instant",  "duration": 0, "color": (200, 50, 50)},
    "hp_potion_large":  {"name": "Pocao de Vida Grande",  "desc": "Restaura 60 HP",                     "effect": "heal",       "value": 60, "cost": 35, "sp_cost": 0, "scope": "instant",  "duration": 0, "color": (220, 30, 30)},
    "atk_tonic":        {"name": "Tonico de Forca",       "desc": "+10 ATK por 1 sala",                 "effect": "atk_buff",  "value": 10, "cost": 20, "sp_cost": 0, "scope": "room",    "duration": 0, "color": (255, 150, 50)},
    "def_tonic":        {"name": "Tonico de Escudo",      "desc": "+5 DEF por 3 turnos",                "effect": "def_buff",  "value": 5,  "cost": 18, "sp_cost": 0, "scope": "turns",   "duration": 3, "color": (50, 150, 255)},
    "speed_tonic":      {"name": "Tonico de Velocidade",  "desc": "+2 alcance de movimento por 1 sala", "effect": "range_buff","value": 2,  "cost": 25, "sp_cost": 0, "scope": "room",    "duration": 0, "color": (50, 255, 150)},
    "vitality_elixir":   {"name": "Elixir de Vitalidade", "desc": "+15 vida maxima pela sala",          "effect": "max_hp_buff","value": 15, "cost": 50, "sp_cost": 1, "scope": "room",    "duration": 0, "color": (255, 215, 0)},
}

SHOP_ITEMS = {
    "weapons": ["fire_blade", "ice_rapier", "thunder_axe", "arcane_staff", "shadow_dagger", "heavy_axe"],
    "shields": ["iron_shield", "mirror_shield", "steel_shield"],
    "consumables": ["hp_potion_small", "hp_potion_large", "atk_tonic", "def_tonic", "speed_tonic", "vitality_elixir"],
}

GOLD_PER_STAR = {1: 20, 2: 35, 3: 55, 4: 80}
GOLD_PER_ENEMY = {1: 5, 2: 8, 3: 12, 4: 18}
GOLD_BOSS_REWARD = 200

ENEMY_EXP_ORTOGONAL = 25
ENEMY_EXP_ATIRADOR = 20
ENEMY_EXP_GRANADEIRO = 30

GRID_COLS = 16
GRID_ROWS = 12
PLAYER_MOVE_RANGE = 3
BASIC_ATTACK_RANGE = 1
PITAGORAS_RIGOR_COST = 20
PITAGORAS_DAMAGE = 25
PITAGORAS_RANGE = 3
REFLEXAO_RIGOR_COST = 30
REFLEXAO_DAMAGE = 22
REFLEXAO_RANGE = 3
REFLEXAO_DURATION = 2
INTEGRAL_RIGOR_COST = 25
INTEGRAL_DAMAGE = 20
INTEGRAL_RANGE = 2
INTEGRAL_LIFESTEAL = 0.3
FRACTAL_RIGOR_COST = 35
FRACTAL_HP_PER_LEVEL = 20
FRACTAL_RANGE = 1

ENEMY_SIZE = 14
BOSS_SIZE = 36
CENSOR_HP = 30
CENSOR_MOVE_RANGE = 2
CENSOR_DAMAGE = 10
CENSOR_ATTACK_RANGE = 3
STRAWMAN_HP = 20
STRAWMAN_MOVE_RANGE = 3
STRAWMAN_DAMAGE = 7
STRAWMAN_ATTACK_RANGE = 3
BAYESIAN_HP = 25
BAYESIAN_MOVE_RANGE = 2
BAYESIAN_DAMAGE = 9
BAYESIAN_ATTACK_RANGE = 5
BOSS_HP = 150
BOSS_MOVE_RANGE = 1
BOSS_DAMAGE = 15
BOSS_ATTACK_RANGE = 4
BOSS_ACTION_INTERVAL = 0.9

ORTOGONAL_HP = 35
ORTOGONAL_MOVE_RANGE = 1
ORTOGONAL_DAMAGE = 12
ORTOGONAL_ATTACK_RANGE = 1

ATIRADOR_HP = 20
ATIRADOR_MOVE_RANGE = 1
ATIRADOR_DAMAGE = 8
ATIRADOR_ATTACK_RANGE = 6

GRANADEIRO_HP = 25
GRANADEIRO_MOVE_RANGE = 1
GRANADEIRO_DAMAGE = 15
GRANADEIRO_ATTACK_RANGE = 4

ENEMY_EXP_CENSOR = 20
ENEMY_EXP_STRAWMAN = 15
ENEMY_EXP_BAYESIAN = 30
ENEMY_EXP_BOSS = 150

ENEMY_CRIT_CHANCE = 0.08
ENEMY_CRIT_MULTIPLIER = 1.8
ENEMY_DAMAGE_VARIANCE = 0.15

ENTROPY_PER_TURN = 2
REWIND_UNDO_TURNS = 2
REWIND_ENTROPY_INCREASE = 25
REWIND_COOLDOWN_TURNS = 3
REWIND_HEAL_AMOUNT = 10
MAX_ENTROPY = 100
HIGH_ENTROPY_THRESHOLD = 50

VICTORY_TRANSITION_DURATION = 2.5
GAME_OVER_TRANSITION_DURATION = 1.5

UI_BAR_HEIGHT = 125
UI_PADDING = 8
ARENA_WIDTH = 760
ARENA_HEIGHT = 500
ARENA_OFFSET_X = 20
ARENA_OFFSET_Y = 15

COLOR_BG = DARK_BLUE
COLOR_ARENA = (15, 15, 35)
COLOR_WALL = (60, 60, 100)
COLOR_PLAYER = CYAN
COLOR_CENSOR = RED
COLOR_STRAWMAN = ORANGE
COLOR_BAYESIAN = PURPLE
COLOR_BOSS = (180, 20, 20)
COLOR_ORTOGONAL = (50, 180, 180)
COLOR_ATIRADOR = (180, 180, 50)
COLOR_GRANADEIRO = (180, 100, 50)
COLOR_PROJECTILE = YELLOW
INDICATOR_YELLOW = (255, 200, 50, 80)
INDICATOR_ORANGE = (255, 140, 30, 100)
INDICATOR_RED = (255, 50, 50, 120)
INDICATOR_BLUE = (80, 140, 255, 100)
INDICATOR_PURPLE = (180, 50, 255, 100)
INDICATOR_LOCK_DURATION = 0.5
COLOR_DECOY = (255, 100, 50)
COLOR_HEAL = GREEN
COLOR_RIGOR = BLUE
COLOR_ENTROPY = PURPLE
COLOR_HP_BAR = RED
COLOR_RIGOR_BAR = BLUE
COLOR_ENTROPY_BAR = (150, 50, 200)
COLOR_OBSTACLE = (40, 40, 70)
COLOR_OBSTACLE_BORDER = (70, 70, 120)

ARENA_OBSTACLES = [
    {"col": 3, "row": 2, "w": 2, "h": 2},
    {"col": 11, "row": 2, "w": 2, "h": 2},
    {"col": 7, "row": 4, "w": 2, "h": 3},
    {"col": 2, "row": 7, "w": 2, "h": 2},
    {"col": 12, "row": 7, "w": 2, "h": 2},
    {"col": 5, "row": 8, "w": 2, "h": 2},
    {"col": 9, "row": 8, "w": 2, "h": 2},
]

WAVES = [
    {
        "enemies": [("censor", 1)],
        "narrative": "wave_1_narr",
        "post_narrative": "wave_1_post"
    },
    {
        "enemies": [("censor", 2)],
        "narrative": "wave_2_narr",
        "post_narrative": "wave_2_post"
    },
    {
        "enemies": [("censor", 1), ("ortogonal", 1)],
        "narrative": "wave_3_narr",
        "post_narrative": "wave_3_post"
    },
    {
        "enemies": [("censor", 1), ("ortogonal", 1), ("atirador", 1)],
        "narrative": "wave_4_narr",
        "post_narrative": "wave_4_post"
    },
    {
        "enemies": [("censor", 1), ("strawman", 1), ("granadeiro", 1)],
        "narrative": "wave_5_narr",
        "post_narrative": ""
    },
    {
        "enemies": [("ortogonal", 1), ("atirador", 1), ("granadeiro", 1)],
        "narrative": "wave_6_narr",
        "post_narrative": ""
    },
    {
        "enemies": [("boss", 1)],
        "narrative": "wave_7_narr",
        "post_narrative": ""
    },
]

SKILL_TREE_DATA = [
    {
        "id": "axioma",
        "name": "skill_axioma_name",
        "desc": "skill_axioma_desc",
        "cost": 0,
        "prereqs": [],
        "x": 400, "y": 140,
        "color": (100, 200, 255)
    },
    {
        "id": "derivada",
        "name": "skill_derivada_name",
        "desc": "skill_derivada_desc",
        "cost": 1,
        "prereqs": ["axioma"],
        "x": 200, "y": 240,
        "color": (100, 255, 100)
    },
    {
        "id": "pitagoras",
        "name": "skill_pitagoras_name",
        "desc": "skill_pitagoras_desc",
        "cost": 1,
        "prereqs": ["axioma"],
        "x": 400, "y": 240,
        "color": (255, 200, 100)
    },
    {
        "id": "ctrlz",
        "name": "skill_ctrlz_name",
        "desc": "skill_ctrlz_desc",
        "cost": 1,
        "prereqs": ["axioma"],
        "x": 600, "y": 240,
        "color": (255, 100, 100)
    },
    {
        "id": "bayes",
        "name": "skill_bayes_name",
        "desc": "skill_bayes_desc",
        "cost": 2,
        "prereqs": ["derivada"],
        "x": 200, "y": 360,
        "color": (200, 100, 255)
    },
    {
        "id": "reflexao",
        "name": "skill_reflexao_name",
        "desc": "skill_reflexao_desc",
        "cost": 2,
        "prereqs": ["pitagoras"],
        "x": 400, "y": 360,
        "color": (100, 255, 200)
    },
    {
        "id": "entropia",
        "name": "skill_entropia_name",
        "desc": "skill_entropia_desc",
        "cost": 2,
        "prereqs": ["ctrlz"],
        "x": 600, "y": 360,
        "color": (255, 150, 200)
    },
    {
        "id": "teoria_jogos",
        "name": "skill_teoria_jogos_name",
        "desc": "skill_teoria_jogos_desc",
        "cost": 3,
        "prereqs": ["bayes"],
        "x": 200, "y": 480,
        "color": (255, 215, 0)
    },
    {
        "id": "integral",
        "name": "skill_integral_name",
        "desc": "skill_integral_desc",
        "cost": 3,
        "prereqs": ["reflexao"],
        "x": 400, "y": 480,
        "color": (100, 255, 180)
    },
    {
        "id": "fractal",
        "name": "skill_fractal_name",
        "desc": "skill_fractal_desc",
        "cost": 3,
        "prereqs": ["entropia"],
        "x": 600, "y": 480,
        "color": (255, 180, 100)
    },
    {
        "id": "gauss",
        "name": "skill_gauss_name",
        "desc": "skill_gauss_desc",
        "cost": 4,
        "prereqs": ["integral"],
        "x": 400, "y": 580,
        "color": (200, 150, 255)
    },
    {
        "id": "simetria",
        "name": "skill_simetria_name",
        "desc": "skill_simetria_desc",
        "cost": 4,
        "prereqs": ["fractal"],
        "x": 600, "y": 580,
        "color": (150, 255, 220)
    },
    {
        "id": "matriz",
        "name": "skill_matriz_name",
        "desc": "skill_matriz_desc",
        "cost": 5,
        "prereqs": ["gauss", "simetria"],
        "x": 400, "y": 680,
        "color": (255, 255, 100)
    },
]

SKILL_TO_KEY = {
    "pitagoras": "1",
    "reflexao": "2",
    "ctrlz": "r",
}

MAP_COLS = 5
MAP_ROWS = 4
MAP_START_ROOM = "hub"
MAP_ROOM_WIDTH = 120
MAP_ROOM_HEIGHT = 80
MAP_ROOM_GAP = 30
MAP_OFFSET_X = 80
MAP_OFFSET_Y = 80
MAP_HEADER_H = 70

MAP_GEN_DEPTH_EASY = 5
MAP_GEN_DEPTH_MEDIUM = 7
MAP_GEN_DEPTH_HARD = 9
MAP_GEN_MAX_BRANCHES_EASY = 3
MAP_GEN_MAX_BRANCHES_MEDIUM = 4
MAP_GEN_MAX_BRANCHES_HARD = 5

DIFFICULTY = "medium"
DIFFICULTY_SCALING = {
    "easy": {
        "enemy_amount": 0.5,
        "depth": MAP_GEN_DEPTH_EASY,
        "max_branches": MAP_GEN_MAX_BRANCHES_EASY,
    },
    "medium": {
        "enemy_amount": 0.75,
        "depth": MAP_GEN_DEPTH_MEDIUM,
        "max_branches": MAP_GEN_MAX_BRANCHES_MEDIUM,
    },
    "hard": {
        "enemy_amount": 1.0,
        "depth": MAP_GEN_DEPTH_HARD,
        "max_branches": MAP_GEN_MAX_BRANCHES_HARD,
    },
}

MAP_ROOMS = {
    (2, 1): {
        "type": "hub",
        "name": "room_archive_name",
        "narrative": "room_archive_narr",
        "connections": [(1, 1), (3, 1), (2, 0), (2, 2)],
        "enemies": [],
        "obstacles": [],
    },
    (1, 1): {
        "type": "normal",
        "name": "room_library_name",
        "narrative": "room_library_narr",
        "connections": [(2, 1), (0, 1), (1, 0)],
        "enemies": [("censor", 2)],
        "obstacles": [
            {"col": 3, "row": 2, "w": 2, "h": 1},
            {"col": 11, "row": 6, "w": 2, "h": 2},
        ],
    },
    (3, 1): {
        "type": "normal",
        "name": "room_logic_name",
        "narrative": "room_logic_narr",
        "connections": [(2, 1), (4, 1), (3, 2)],
        "enemies": [("censor", 1), ("strawman", 1)],
        "obstacles": [
            {"col": 5, "row": 3, "w": 2, "h": 2},
            {"col": 9, "row": 8, "w": 2, "h": 1},
        ],
    },
    (2, 0): {
        "type": "normal",
        "name": "room_gallery_name",
        "narrative": "room_gallery_narr",
        "connections": [(2, 1), (1, 0), (3, 0)],
        "enemies": [("censor", 1), ("strawman", 2)],
        "obstacles": [
            {"col": 2, "row": 4, "w": 2, "h": 3},
            {"col": 12, "row": 4, "w": 2, "h": 3},
        ],
    },
    (2, 2): {
        "type": "normal",
        "name": "room_hall_name",
        "narrative": "room_hall_narr",
        "connections": [(2, 1), (1, 2), (3, 2)],
        "enemies": [("censor", 2), ("strawman", 1)],
        "obstacles": [
            {"col": 4, "row": 2, "w": 2, "h": 2},
            {"col": 10, "row": 6, "w": 2, "h": 2},
        ],
    },
    (0, 1): {
        "type": "challenge",
        "name": "room_maze_name",
        "narrative": "room_maze_narr",
        "connections": [(1, 1), (0, 0)],
        "enemies": [("censor", 2), ("strawman", 2)],
        "obstacles": [
            {"col": 3, "row": 2, "w": 2, "h": 1},
            {"col": 7, "row": 4, "w": 2, "h": 3},
            {"col": 11, "row": 7, "w": 2, "h": 2},
        ],
    },
    (1, 0): {
        "type": "challenge",
        "name": "room_tower_name",
        "narrative": "room_tower_narr",
        "connections": [(2, 0), (0, 1)],
        "enemies": [("censor", 1), ("strawman", 1), ("bayesian", 1)],
        "obstacles": [
            {"col": 5, "row": 2, "w": 3, "h": 1},
            {"col": 8, "row": 8, "w": 2, "h": 1},
        ],
    },
    (1, 2): {
        "type": "challenge",
        "name": "room_dungeon_name",
        "narrative": "room_dungeon_narr",
        "connections": [(2, 2), (0, 2)],
        "enemies": [("censor", 1), ("bayesian", 2)],
        "obstacles": [
            {"col": 3, "row": 3, "w": 2, "h": 2},
            {"col": 11, "row": 5, "w": 2, "h": 3},
        ],
    },
    (0, 0): {
        "type": "boss",
        "name": "room_boss_censor_name",
        "narrative": "room_boss_censor_narr",
        "connections": [(0, 1)],
        "enemies": [("boss", 1)],
        "obstacles": [
            {"col": 4, "row": 3, "w": 2, "h": 2},
            {"col": 10, "row": 3, "w": 2, "h": 2},
            {"col": 7, "row": 6, "w": 2, "h": 2},
        ],
        "boss_hp": 150,
    },
    (3, 0): {
        "type": "boss",
        "name": "room_boss_engine_name",
        "narrative": "room_boss_engine_narr",
        "connections": [(2, 0), (4, 0)],
        "enemies": [("boss", 1)],
        "obstacles": [
            {"col": 3, "row": 2, "w": 2, "h": 2},
            {"col": 11, "row": 2, "w": 2, "h": 2},
        ],
        "boss_hp": 180,
    },
    (4, 1): {
        "type": "boss",
        "name": "room_boss_final_name",
        "narrative": "room_boss_final_narr",
        "connections": [(3, 1), (4, 2)],
        "enemies": [("boss", 1)],
        "obstacles": [
            {"col": 3, "row": 2, "w": 2, "h": 1},
            {"col": 11, "row": 2, "w": 2, "h": 1},
            {"col": 7, "row": 5, "w": 2, "h": 3},
        ],
        "boss_hp": 200,
    },
    (4, 2): {
        "type": "victory",
        "name": "room_victory_name",
        "narrative": "room_victory_narr",
        "connections": [(4, 1)],
        "enemies": [],
        "obstacles": [],
    },
    (0, 2): {
        "type": "normal",
        "name": "room_sanctuary_name",
        "narrative": "room_sanctuary_narr",
        "connections": [(1, 2)],
        "enemies": [("censor", 2), ("bayesian", 1)],
        "obstacles": [
            {"col": 5, "row": 4, "w": 3, "h": 2},
        ],
    },
    (3, 2): {
        "type": "normal",
        "name": "room_vault_name",
        "narrative": "room_vault_narr",
        "connections": [(2, 2), (3, 1)],
        "enemies": [("censor", 1), ("strawman", 1), ("bayesian", 1)],
        "obstacles": [
            {"col": 3, "row": 3, "w": 2, "h": 2},
            {"col": 11, "row": 6, "w": 2, "h": 2},
        ],
    },
    (4, 0): {
        "type": "challenge",
        "name": "room_lab_name",
        "narrative": "room_lab_narr",
        "connections": [(3, 0)],
        "enemies": [("censor", 3), ("strawman", 2), ("bayesian", 1)],
        "obstacles": [
            {"col": 2, "row": 2, "w": 2, "h": 1},
            {"col": 5, "row": 5, "w": 2, "h": 2},
            {"col": 9, "row": 3, "w": 1, "h": 1},
            {"col": 12, "row": 8, "w": 1, "h": 1},
        ],
},
}

LAN_PORT = MATCH_SERVER_PORT
LAN_DISCOVERY_PORT = MATCH_SERVER_PORT + 1
LAN_BUFFER_SIZE = 8192
LAN_TICK_RATE = 20
LAN_TIMEOUT = 5.0
LAN_MAX_PLAYERS = 2
