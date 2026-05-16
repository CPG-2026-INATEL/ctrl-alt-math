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
PLAYER_ATTACK_RANGE = 35
PLAYER_ATTACK_DAMAGE = 15
PLAYER_START_SKILL_POINTS = 2
RIGOR_REGEN_RATE = 8
RIGOR_REGEN_DELAY = 2.0

PITAGORAS_RIGOR_COST = 20
PITAGORAS_DAMAGE = 25
PITAGORAS_RANGE = 80

REFLEXAO_RIGOR_COST = 30
REFLEXAO_RANGE = 60
REFLEXAO_DAMAGE = 10
REFLEXAO_KNOCKBACK = 200

ENEMY_SIZE = 14
BOSS_SIZE = 36
ENEMY_ACTION_INTERVAL = 1.2
BOSS_ACTION_INTERVAL = 0.9

CENSOR_HP = 30
CENSOR_SPEED = 80
CENSOR_DAMAGE = 12
CENSOR_ATTACK_RANGE = 50

STRAWMAN_HP = 20
STRAWMAN_SPEED = 120
STRAWMAN_DAMAGE = 8

BAYESIAN_HP = 25
BAYESIAN_SPEED = 90
BAYESIAN_DAMAGE = 10
BAYESIAN_PROJECTILE_SPEED = 150

BOSS_HP = 200
BOSS_SPEED = 60
BOSS_DAMAGE = 15

REWIND_BUFFER_SECONDS = 3.0
REWIND_SNAPSHOT_INTERVAL = 0.08
REWIND_SECONDS = 1.5
REWIND_ENTROPY_INCREASE = 12
MAX_ENTROPY = 100
HIGH_ENTROPY_THRESHOLD = 50
ENTROPY_DECAY_RATE = 2

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
        "enemies": [("censor", 3)],
        "narrative": "The regime sends more censors.\nThey cannot erase what is proven.",
        "post_narrative": "Derivatives and integrals\nwhisper in the static."
    },
    {
        "enemies": [("censor", 2), ("strawman", 2)],
        "narrative": "Rhetorical tricksters enter the field.\nThey distort your theorems.",
        "post_narrative": "You see through their\nlogical fallacies."
    },
    {
        "enemies": [("censor", 2), ("strawman", 1), ("bayesian", 2)],
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
        "desc": "Geometric attack.\nPress 1 to use.",
        "cost": 1,
        "prereqs": ["axioma"],
        "x": 400, "y": 160,
        "color": (255, 200, 100)
    },
    {
        "id": "ctrlz",
        "name": "Ctrl+Z",
        "desc": "Rewind time.\nPress R to undo recent damage.",
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
        "desc": "Reflect projectiles.\nPress 2 for burst.",
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
