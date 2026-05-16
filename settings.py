import pygame

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

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

PLAYER_SIZE = 14
PLAYER_SPEED = 220
PLAYER_MAX_HP = 100
PLAYER_MAX_RIGOR = 100
PLAYER_ATTACK_COOLDOWN = 0.3
PLAYER_ATTACK_DAMAGE = 15
PLAYER_START_SKILL_POINTS = 2
RIGOR_REGEN_RATE = 15
RIGOR_REGEN_DELAY = 0

GRID_COLS = 16
GRID_ROWS = 12
PLAYER_MOVE_RANGE = 3
BASIC_ATTACK_RANGE = 1
PITAGORAS_RIGOR_COST = 20
PITAGORAS_DAMAGE = 25
PITAGORAS_RANGE = 3
REFLEXAO_RIGOR_COST = 30
REFLEXAO_DAMAGE = 10
REFLEXAO_RANGE = 2
REFLEXAO_DURATION = 2

ENEMY_SIZE = 14
BOSS_SIZE = 36
CENSOR_HP = 30
CENSOR_MOVE_RANGE = 2
CENSOR_DAMAGE = 12
CENSOR_ATTACK_RANGE = 3
STRAWMAN_HP = 20
STRAWMAN_MOVE_RANGE = 3
STRAWMAN_DAMAGE = 8
STRAWMAN_ATTACK_RANGE = 3
BAYESIAN_HP = 25
BAYESIAN_MOVE_RANGE = 2
BAYESIAN_DAMAGE = 10
BAYESIAN_ATTACK_RANGE = 5
BOSS_HP = 150
BOSS_MOVE_RANGE = 1
BOSS_DAMAGE = 15
BOSS_ATTACK_RANGE = 4
BOSS_ACTION_INTERVAL = 0.9

ENTROPY_PER_TURN = 2
REWIND_UNDO_TURNS = 2
REWIND_ENTROPY_INCREASE = 12
REWIND_COOLDOWN_TURNS = 3
MAX_ENTROPY = 100
HIGH_ENTROPY_THRESHOLD = 50

VICTORY_TRANSITION_DURATION = 2.5

UI_BAR_HEIGHT = 55
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
COLOR_PROJECTILE = YELLOW
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
    {"x": 180, "y": 120, "w": 40, "h": 40},
    {"x": 580, "y": 120, "w": 40, "h": 40},
    {"x": 380, "y": 200, "w": 40, "h": 80},
    {"x": 120, "y": 320, "w": 60, "h": 30},
    {"x": 620, "y": 320, "w": 60, "h": 30},
    {"x": 300, "y": 380, "w": 30, "h": 50},
    {"x": 470, "y": 380, "w": 30, "h": 50},
]

WAVES = [
    {
        "enemies": [("censor", 1)],
        "narrative": "Mathematics is forbidden.\nBut reality still obeys it.",
        "post_narrative": "You recover a lost axiom\nfrom a censored archive."
    },
    {
        "enemies": [("censor", 2)],
        "narrative": "The regime sends more censors.\nThey cannot erase what is proven.",
        "post_narrative": "Derivatives and integrals\nwhisper in the static."
    },
    {
        "enemies": [("censor", 1), ("strawman", 1)],
        "narrative": "Rhetorical tricksters enter the field.\nThey distort your theorems.",
        "post_narrative": "You see through their\nlogical fallacies."
    },
    {
        "enemies": [("censor", 1), ("strawman", 1), ("bayesian", 1)],
        "narrative": "An Inquisidor Bayesiano joins.\nIt calculates your every move.",
        "post_narrative": "Probability bends to your will.\nThe end approaches."
    },
    {
        "enemies": [("boss", 1)],
        "narrative": "O Grande Simplificador approaches.\nIt wants to reduce all thought\nto one dimension.",
        "post_narrative": ""
    },
]

SKILL_TREE_DATA = [
    {
        "id": "axioma",
        "name": "Axioma B\u00e1sico",
        "desc": "The foundation of all\nmathematical thought.",
        "cost": 0,
        "prereqs": [],
        "x": 400, "y": 60,
        "color": (100, 200, 255)
    },
    {
        "id": "derivada",
        "name": "Derivada",
        "desc": "Predict enemy movement.\nShows future positions.",
        "cost": 1,
        "prereqs": ["axioma"],
        "x": 200, "y": 160,
        "color": (100, 255, 100)
    },
    {
        "id": "pitagoras",
        "name": "Pit\u00e1goras",
        "desc": "Geometric attack (range 3).\nPress 1 to target area.",
        "cost": 1,
        "prereqs": ["axioma"],
        "x": 400, "y": 160,
        "color": (255, 200, 100)
    },
    {
        "id": "ctrlz",
        "name": "Ctrl+Z",
        "desc": "Rewind 2 turns back.\nPress R to undo.",
        "cost": 1,
        "prereqs": ["axioma"],
        "x": 600, "y": 160,
        "color": (255, 100, 100)
    },
    {
        "id": "bayes",
        "name": "Bayes",
        "desc": "Improved prediction.\nShows attack intent.",
        "cost": 2,
        "prereqs": ["derivada"],
        "x": 200, "y": 280,
        "color": (200, 100, 255)
    },
    {
        "id": "reflexao",
        "name": "Reflex\u00e3o",
        "desc": "Barrier cells block enemies.\nPress 2 for barrier.",
        "cost": 2,
        "prereqs": ["pitagoras"],
        "x": 400, "y": 280,
        "color": (100, 255, 200)
    },
    {
        "id": "entropia",
        "name": "Entropia Controlada",
        "desc": "Reduce entropy gain\nfrom rewinding.",
        "cost": 2,
        "prereqs": ["ctrlz"],
        "x": 600, "y": 280,
        "color": (255, 150, 200)
    },
    {
        "id": "teoria_jogos",
        "name": "Teoria dos Jogos",
        "desc": "Reveal enemy targets.\nShows who enemies target.",
        "cost": 3,
        "prereqs": ["bayes"],
        "x": 200, "y": 400,
        "color": (255, 215, 0)
    },
]

SKILL_TO_KEY = {
    "pitagoras": "1",
    "reflexao": "2",
    "ctrlz": "r",
}

MAP_COLS = 5
MAP_ROWS = 4
MAP_START_ROOM = (2, 1)
MAP_ROOM_WIDTH = 120
MAP_ROOM_HEIGHT = 80
MAP_ROOM_GAP = 30
MAP_OFFSET_X = 80
MAP_OFFSET_Y = 80

MAP_ROOMS = {
    (2, 1): {
        "type": "hub",
        "name": "The Archive",
        "narrative": "A safe haven where forbidden knowledge persists.",
        "connections": [(1, 1), (3, 1), (2, 0), (2, 2)],
        "enemies": [],
        "obstacles": [],
    },
    (1, 1): {
        "type": "normal",
        "name": "Censored Library",
        "narrative": "Books burn themselves as you enter.",
        "connections": [(2, 1), (0, 1), (1, 0)],
        "enemies": [("censor", 2)],
        "obstacles": [
            {"x": 200, "y": 100, "w": 50, "h": 30},
            {"x": 550, "y": 300, "w": 50, "h": 30},
        ],
    },
    (3, 1): {
        "type": "normal",
        "name": "Logic Chamber",
        "narrative": "Every argument here must be proven.",
        "connections": [(2, 1), (4, 1), (3, 2)],
        "enemies": [("censor", 1), ("strawman", 1)],
        "obstacles": [
            {"x": 300, "y": 150, "w": 40, "h": 60},
            {"x": 450, "y": 350, "w": 60, "h": 40},
        ],
    },
    (2, 0): {
        "type": "normal",
        "name": "Proof Gallery",
        "narrative": "Theorems hang on walls like paintings.",
        "connections": [(2, 1), (1, 0), (3, 0)],
        "enemies": [("censor", 1), ("strawman", 2)],
        "obstacles": [
            {"x": 150, "y": 200, "w": 30, "h": 80},
            {"x": 620, "y": 200, "w": 30, "h": 80},
        ],
    },
    (2, 2): {
        "type": "normal",
        "name": "Derivative Hall",
        "narrative": "Rates of change echo through corridors.",
        "connections": [(2, 1), (1, 2), (3, 2)],
        "enemies": [("censor", 2), ("strawman", 1)],
        "obstacles": [
            {"x": 250, "y": 120, "w": 50, "h": 50},
            {"x": 500, "y": 280, "w": 50, "h": 50},
        ],
    },
    (0, 1): {
        "type": "challenge",
        "name": "Fallacy Maze",
        "narrative": "Every path leads to a logical trap.",
        "connections": [(1, 1), (0, 0)],
        "enemies": [("censor", 2), ("strawman", 2)],
        "obstacles": [
            {"x": 180, "y": 100, "w": 40, "h": 40},
            {"x": 380, "y": 200, "w": 40, "h": 80},
            {"x": 580, "y": 320, "w": 40, "h": 40},
        ],
    },
    (1, 0): {
        "type": "challenge",
        "name": "Induction Tower",
        "narrative": "Prove the base case to ascend.",
        "connections": [(2, 0), (0, 1)],
        "enemies": [("censor", 1), ("strawman", 1), ("bayesian", 1)],
        "obstacles": [
            {"x": 300, "y": 100, "w": 60, "h": 30},
            {"x": 400, "y": 350, "w": 60, "h": 30},
        ],
    },
    (1, 2): {
        "type": "challenge",
        "name": "Probability Dungeon",
        "narrative": "Bayesian inference is your only light.",
        "connections": [(2, 2), (0, 2)],
        "enemies": [("censor", 1), ("bayesian", 2)],
        "obstacles": [
            {"x": 200, "y": 150, "w": 30, "h": 60},
            {"x": 570, "y": 250, "w": 30, "h": 60},
        ],
    },
    (0, 0): {
        "type": "boss",
        "name": "The Censor General",
        "narrative": "The head of all censorship awaits.",
        "connections": [(0, 1)],
        "enemies": [("boss", 1)],
        "obstacles": [
            {"x": 250, "y": 180, "w": 40, "h": 40},
            {"x": 510, "y": 180, "w": 40, "h": 40},
            {"x": 380, "y": 300, "w": 40, "h": 40},
        ],
        "boss_hp": 150,
    },
    (3, 0): {
        "type": "boss",
        "name": "The Reduction Engine",
        "narrative": "It reduces complexity to nothing.",
        "connections": [(2, 0), (4, 0)],
        "enemies": [("boss", 1)],
        "obstacles": [
            {"x": 180, "y": 120, "w": 50, "h": 50},
            {"x": 570, "y": 120, "w": 50, "h": 50},
        ],
        "boss_hp": 180,
    },
    (4, 1): {
        "type": "boss",
        "name": "O Grande Simplificador",
        "narrative": "The final boss. It wants one-dimensional thought.",
        "connections": [(3, 1), (4, 2)],
        "enemies": [("boss", 1)],
        "obstacles": [
            {"x": 200, "y": 100, "w": 40, "h": 40},
            {"x": 560, "y": 100, "w": 40, "h": 40},
            {"x": 380, "y": 250, "w": 40, "h": 80},
        ],
        "boss_hp": 200,
    },
    (4, 2): {
        "type": "victory",
        "name": "The Unbound Theorem",
        "narrative": "Mathematics cannot be contained.",
        "connections": [(4, 1)],
        "enemies": [],
        "obstacles": [],
    },
    (0, 2): {
        "type": "normal",
        "name": "Integral Sanctuary",
        "narrative": "Accumulated knowledge flows here.",
        "connections": [(1, 2)],
        "enemies": [("censor", 2), ("bayesian", 1)],
        "obstacles": [
            {"x": 300, "y": 200, "w": 80, "h": 40},
        ],
    },
    (3, 2): {
        "type": "normal",
        "name": "Matrix Vault",
        "narrative": "Linear transformations guard this room.",
        "connections": [(2, 2), (3, 1)],
        "enemies": [("censor", 1), ("strawman", 1), ("bayesian", 1)],
        "obstacles": [
            {"x": 200, "y": 150, "w": 40, "h": 40},
            {"x": 560, "y": 300, "w": 40, "h": 40},
        ],
    },
    (4, 0): {
        "type": "challenge",
        "name": "Chaos Theory Lab",
        "narrative": "Small changes have massive consequences.",
        "connections": [(3, 0)],
        "enemies": [("censor", 3), ("strawman", 2), ("bayesian", 1)],
        "obstacles": [
            {"x": 150, "y": 100, "w": 30, "h": 30},
            {"x": 300, "y": 250, "w": 30, "h": 30},
            {"x": 450, "y": 150, "w": 30, "h": 30},
            {"x": 600, "y": 350, "w": 30, "h": 30},
        ],
    },
}
