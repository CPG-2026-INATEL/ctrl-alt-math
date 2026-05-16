# Ctrl + Alt + Math — Phases 1-4 Detailed Implementation Plan

## Phase 1.1: Obstacle Collision

### utils.py — Add new function
```python
def resolve_obstacle_collision(entity_x, entity_y, entity_size, obstacles):
    entity_rect = pygame.Rect(
        entity_x - entity_size, entity_y - entity_size,
        entity_size * 2, entity_size * 2
    )
    for obs in obstacles:
        if entity_rect.colliderect(obs):
            # Calculate overlap on each axis
            overlap_left = entity_rect.right - obs.left
            overlap_right = obs.right - entity_rect.left
            overlap_top = entity_rect.bottom - obs.top
            overlap_bottom = obs.bottom - entity_rect.top
            min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
            if min_overlap == overlap_left:
                entity_x -= overlap_left
            elif min_overlap == overlap_right:
                entity_x += overlap_right
            elif min_overlap == overlap_top:
                entity_y -= overlap_top
            else:
                entity_y += overlap_bottom
            entity_rect = pygame.Rect(
                entity_x - entity_size, entity_y - entity_size,
                entity_size * 2, entity_size * 2
            )
    return entity_x, entity_y
```

### game.py — Resolve obstacles after entity updates
In `_update_playing()`, after `self.player.update()` and after `_update_enemies()`:
```python
# After player.update():
self.player.x, self.player.y = resolve_obstacle_collision(
    self.player.x, self.player.y, self.player.size, self.obstacles
)

# After _update_enemies():
for enemy in self.enemies:
    if not enemy.dead:
        enemy.x, enemy.y = resolve_obstacle_collision(
            enemy.x, enemy.y, enemy.size, self.obstacles
        )
```

### game.py — Projectile obstacle collision
In `_update_projectiles()`:
```python
for proj in list(self.projectiles):
    proj.update(dt)
    # Check obstacle collision
    for obs in self.obstacles:
        if obs.collidepoint(proj.x, proj.y):
            proj.alive = False
            break
    if not proj.alive:
        self.projectiles.remove(proj)
```

### game.py — Pass obstacles to _update_enemies
Change signature: `_update_enemies(dt)` → `_update_enemies(dt, obstacles)`
(Actually, better to resolve in game.py after the call to keep enemy.py clean)

---

## Phase 1.2: Bayes Prediction Scaling

### ui.py — draw_prediction()
Around line 368-373, the purple square is drawn at fixed 8x8 size.
Change to scale with distance:

```python
# Before the purple square drawing, calculate distance
dist_to_player = distance((enemy.x, enemy.y), (player.x, player.y))
proximity = max(0, 1.0 - (dist_to_player / enemy.attack_range))
square_size = int(8 + proximity * 16)  # 8 to 24px

# Then use square_size instead of hardcoded 8
s2 = pygame.Surface((square_size, square_size))
s2.set_alpha(80)
s2.fill(settings.PURPLE)
screen.blit(s2, (pred2_x - square_size // 2, pred2_y - square_size // 2))
pygame.draw.rect(screen, settings.PURPLE,
    (pred2_x - square_size // 2, pred2_y - square_size // 2, square_size, square_size), 1)
```

---

## Phase 1.3: Skill Points Visibility

### skills.py — draw()
The problem: Axioma node is at y=60 with height 46, so rect spans y=37 to y=83.
Skill points text at y=70 overlaps with the Axioma node which is drawn AFTER the text.

**Fix:** Move skill points text to y=110 (below all top-row nodes) and draw it AFTER all nodes.

```python
# Remove the skill points text from its current position (line ~86-88)
# Add it AFTER all nodes are drawn, before the hovered description:
draw_text(screen, f"Skill Points: {self.skill_points}",
    (settings.WINDOW_WIDTH // 2, 110),
    settings.GOLD, 28)
```

---

## Phase 1.4: Wave Difficulty Balance

### settings.py — WAVES
```python
WAVES = [
    {"enemies": [("censor", 1)], ...},           # Wave 1: unchanged
    {"enemies": [("censor", 2)], ...},            # Wave 2: 3→2
    {"enemies": [("censor", 1), ("strawman", 1)], ...},  # Wave 3: 2+2→1+1
    {"enemies": [("censor", 1), ("strawman", 1), ("bayesian", 1)], ...},  # Wave 4: 2+1+2→1+1+1
    {"enemies": [("boss", 1)], ...},              # Wave 5: boss HP 200→150
]
```

Also change `BOSS_HP = 150` (was 200).

---

## Phase 2: Katana Zero Rewind

### rewind.py — Full-state recording

Replace current `RewindBuffer` with extended version:

```python
class RewindBuffer:
    def __init__(self):
        self.buffer = []
        self.timer = 0

    def record(self, player, enemies, projectiles):
        self.timer += 1/60.0  # approximate, actual dt passed
        # Actually use dt parameter
    def record(self, player, enemies, projectiles, dt):
        self.timer += dt
        if self.timer >= settings.REWIND_SNAPSHOT_INTERVAL:
            self.timer = 0
            snapshot = {
                'time': pygame.time.get_ticks(),
                'player': {
                    'x': player.x, 'y': player.y,
                    'hp': player.hp, 'max_hp': player.max_hp,
                },
                'enemies': [
                    {
                        'x': e.x, 'y': e.y, 'hp': e.hp, 'max_hp': e.max_hp,
                        'type': e.type, 'alive': e.alive, 'dead': e.dead,
                        'size': e.size, 'color': e.color,
                    }
                    for e in enemies if not e.dead
                ],
                'projectiles': [
                    {
                        'x': p.x, 'y': p.y, 'vx': p.vx, 'vy': p.vy,
                        'damage': p.damage, 'owner': p.owner,
                        'color': p.color, 'size': p.size,
                    }
                    for p in projectiles if p.alive
                ],
            }
            self.buffer.append(snapshot)
            cutoff = pygame.time.get_ticks() - settings.REWIND_BUFFER_SECONDS * 1000
            while self.buffer and self.buffer[0]['time'] < cutoff:
                self.buffer.pop(0)

    def rewind(self):
        # Same as before, returns full snapshot instead of just player data
        if not self.buffer:
            return None
        target_time = pygame.time.get_ticks() - settings.REWIND_SECONDS * 1000
        best = None
        for entry in reversed(self.buffer):
            if entry['time'] <= target_time:
                best = entry
                break
        if best is None:
            best = self.buffer[0]
        return best
```

### game.py — Rewind Playback State

New state: `"REWIND_PLAYBACK"`

In `_handle_keydown()`, PLAYING state, K_r handler:
```python
elif event.key == pygame.K_r:
    if self.skill_tree.is_unlocked("ctrlz"):
        if len(self.rewind_buffer.buffer) > 0 and self.rewind_cooldown <= 0:
            self.prev_state = "PLAYING"
            self.state = "REWIND_PLAYBACK"
            self.rewind_playback_index = len(self.rewind_buffer.buffer) - 1
            self.rewind_playback_timer = 0
            self.sfx.play("rewind")
```

New method `_update_rewind_playback(dt)`:
```python
def _update_rewind_playback(self, dt):
    self.rewind_playback_timer += dt * 4  # 4x speed
    # Move backward through buffer
    target_index = self.rewind_playback_index - int(self.rewind_playback_timer * 10)
    target_index = max(0, target_index)
    
    if target_index <= 0:
        # Rewind complete, apply final state
        self._apply_rewind_snapshot(self.rewind_buffer.buffer[0])
        self.state = self.prev_state or "PLAYING"
        self.prev_state = None
        self.rewind_cooldown = 2.0
        ent_inc = settings.REWIND_ENTROPY_INCREASE
        if self.skill_tree.is_unlocked("entropia"):
            ent_inc *= 0.5
        self.entropy = min(settings.MAX_ENTROPY, self.entropy + ent_inc)
        self.particles.emit_burst(self.player.x, self.player.y, settings.CYAN, 30, 100, 0.6)
        self._add_hit_stop(0.08)
        return
    
    snapshot = self.rewind_buffer.buffer[target_index]
    self.rewind_playback_index = target_index
    self._apply_rewind_snapshot(snapshot)
```

New method `_apply_rewind_snapshot(snapshot)`:
```python
def _apply_rewind_snapshot(self, snapshot):
    # Restore player
    self.player.x = snapshot['player']['x']
    self.player.y = snapshot['player']['y']
    self.player.hp = snapshot['player']['hp']
    self.player.max_hp = snapshot['player']['max_hp']
    
    # Restore enemies
    restored_types = set()
    for e_data in snapshot['enemies']:
        restored_types.add(e_data['type'])
        # Find matching enemy or create one
        found = False
        for e in self.enemies:
            if e.type == e_data['type'] and not e.dead:
                e.x = e_data['x']
                e.y = e_data['y']
                e.hp = e_data['hp']
                e.max_hp = e_data['max_hp']
                found = True
                break
        if not found:
            # Create enemy at recorded position
            new_enemy = Enemy(e_data['x'], e_data['y'], e_data['type'])
            new_enemy.hp = e_data['hp']
            new_enemy.max_hp = e_data['max_hp']
            new_enemy.size = e_data['size']
            new_enemy.color = e_data['color']
            self.enemies.append(new_enemy)
    
    # Mark enemies not in snapshot as dead
    for e in self.enemies:
        if e.type not in restored_types and not e.dead:
            e.alive = False
            e.dead = True
    
    # Restore projectiles
    self.projectiles = []
    for p_data in snapshot['projectiles']:
        proj = Projectile(
            p_data['x'], p_data['y'],
            p_data['vx'], p_data['vy'],
            p_data['damage'], p_data['owner'],
            color=p_data['color'], size=p_data['size']
        )
        self.projectiles.append(proj)
```

### game.py — Update loop
In `_update()`:
```python
elif self.state == "REWIND_PLAYBACK":
    self._update_rewind_playback(dt)
    self.particles.update(dt)
    self.floating_text.update(dt)
```

In `_draw()`, add to the list of states that draw the game:
```python
elif self.state in ("PLAYING", "WAVE_INTRO", "WAVE_COMPLETE",
                    "PAUSED", "SKILL_TREE", "GAME_OVER", "VICTORY",
                    "REWIND_PLAYBACK"):
```

### rewind_fx.py — Retro Visual Effects (new file)

```python
import pygame
import random
import settings

class RewindEffects:
    def __init__(self):
        self.scanline_surface = pygame.Surface(
            (settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA
        )
        self._build_scanlines()
    
    def _build_scanlines(self):
        self.scanline_surface.fill((0, 0, 0, 0))
        for y in range(0, settings.WINDOW_HEIGHT, 3):
            pygame.draw.line(self.scanline_surface, (0, 0, 0, 40), (0, y), 
                           (settings.WINDOW_WIDTH, y))
    
    def apply_rewind_fx(self, screen, time_val):
        # 1. Scanlines
        screen.blit(self.scanline_surface, (0, 0))
        
        # 2. VHS green tint
        tint = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
        tint.fill((0, 30, 0))
        tint.set_alpha(25)
        screen.blit(tint, (0, 0))
        
        # 3. Chromatic aberration (subtle RGB offset)
        # Only if performance allows - may skip for simplicity
        
        # 4. Static noise
        for _ in range(50):
            x = random.randint(0, settings.WINDOW_WIDTH)
            y = random.randint(0, settings.WINDOW_HEIGHT)
            alpha = random.randint(10, 30)
            s = pygame.Surface((2, 1))
            s.set_alpha(alpha)
            s.fill(settings.WHITE)
            screen.blit(s, (x, y))
        
        # 5. "REWIND" text
        from utils import draw_text
        pulse = int(180 + 75 * (0.5 + 0.5 * __import__('math').sin(time_val * 8)))
        draw_text(screen, "⟨⟨ REWIND ⟩⟩",
                 (settings.WINDOW_WIDTH // 2, 30),
                 (pulse, 255, pulse), 32)
```

### game.py — Integrate rewind effects
In `_draw()`, after drawing game for REWIND_PLAYBACK state:
```python
if self.state == "REWIND_PLAYBACK":
    self.rewind_fx.apply_rewind_fx(self.screen, pygame.time.get_ticks() / 1000.0)
```

Also initialize in `__init__`:
```python
from rewind_fx import RewindEffects
self.rewind_fx = RewindEffects()
```

---

## Phase 3: Visual Formulas

### math_bg.py (new file)

```python
import pygame
import random
import math
import settings

FORMULAS = [
    "∫f(x)dx", "∑(n=1→∞)", "√(a²+b²)=c", "∂f/∂x", "∇×F",
    "e^(iπ)+1=0", "∮B·dl=μ₀I", "ΔS≥0", "λ=h/p", "F=ma",
    "E=mc²", "∇²φ=0", "det(A)≠0", "lim(x→0)", "∏(1+1/n)",
    "sin²θ+cos²θ=1", "a·b=|a||b|cosθ", "∫∫∫ dV", "P(A|B)=P(B|A)P(A)/P(B)",
]

class FloatingFormula:
    def __init__(self, arena_rect):
        self.text = random.choice(FORMULAS)
        # Spawn at random edge of arena
        side = random.randint(0, 3)
        if side == 0:  # top
            self.x = random.randint(arena_rect.left, arena_rect.right)
            self.y = arena_rect.top - 10
            self.vx = random.uniform(-15, 15)
            self.vy = random.uniform(5, 15)
        elif side == 1:  # bottom
            self.x = random.randint(arena_rect.left, arena_rect.right)
            self.y = arena_rect.bottom + 10
            self.vx = random.uniform(-15, 15)
            self.vy = random.uniform(-15, -5)
        elif side == 2:  # left
            self.x = arena_rect.left - 10
            self.y = random.randint(arena_rect.top, arena_rect.bottom)
            self.vx = random.uniform(5, 15)
            self.vy = random.uniform(-15, 15)
        else:  # right
            self.x = arena_rect.right + 10
            self.y = random.randint(arena_rect.top, arena_rect.bottom)
            self.vx = random.uniform(-15, -5)
            self.vy = random.uniform(-15, 15)
        
        self.alpha = 0
        self.max_alpha = random.randint(15, 30)
        self.lifetime = random.uniform(6.0, 12.0)
        self.age = 0
        self.fade_in = 1.5
        self.fade_out = 2.0
        self.font = pygame.font.Font(None, random.choice([20, 24, 28]))
        self.color = random.choice([settings.CYAN, settings.PURPLE, settings.GOLD, settings.WHITE])

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.age += dt
        # Fade in
        if self.age < self.fade_in:
            self.alpha = int(self.max_alpha * (self.age / self.fade_in))
        # Fade out
        elif self.age > self.lifetime - self.fade_out:
            remaining = self.lifetime - self.age
            self.alpha = int(self.max_alpha * (remaining / self.fade_out))
        else:
            self.alpha = self.max_alpha
        return self.age < self.lifetime

    def draw(self, screen):
        if self.alpha <= 0:
            return
        img = self.font.render(self.text, True, self.color)
        img.set_alpha(self.alpha)
        screen.blit(img, (self.x - img.get_width() // 2, self.y - img.get_height() // 2))


class MathBackground:
    def __init__(self):
        self.formulas = []
        self.spawn_timer = 0
        self.spawn_interval = 2.0  # seconds between spawns

    def update(self, dt, arena_rect):
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            if len(self.formulas) < 15:  # cap max formulas
                self.formulas.append(FloatingFormula(arena_rect))
        self.formulas = [f for f in self.formulas if f.update(dt)]

    def draw(self, screen):
        for f in self.formulas:
            f.draw(screen)
```

### game.py — Integration
In `_init_game_state()`:
```python
from math_bg import MathBackground
self.math_bg = MathBackground()
```

In `_update_playing()`:
```python
arena_rect = pygame.Rect(
    settings.ARENA_OFFSET_X, settings.ARENA_OFFSET_Y,
    settings.ARENA_WIDTH, settings.ARENA_HEIGHT
)
self.math_bg.update(dt, arena_rect)
```

In `_draw_game()`, after arena background, before entities:
```python
self.math_bg.draw(temp)
```

---

## Phase 4: Baba Is You Style Map

### settings.py — Map Data

```python
# Room grid: 5 columns (0-4) x 4 rows (0-3)
# Room types: "hub", "normal", "challenge", "boss", "victory"
MAP_ROOMS = {
    # Hub (center)
    (2, 1): {
        "type": "hub",
        "name": "The Archive",
        "narrative": "A safe haven where forbidden knowledge persists.",
        "connections": [(1, 1), (3, 1), (2, 0), (2, 2)],
        "enemies": [],
        "obstacles": [],
    },
    # Normal levels
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
    # Challenge levels
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
    # Boss levels
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
    # Victory
    (4, 2): {
        "type": "victory",
        "name": "The Unbound Theorem",
        "narrative": "Mathematics cannot be contained.",
        "connections": [(4, 1)],
        "enemies": [],
        "obstacles": [],
    },
    # Locked/secret rooms
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

MAP_COLS = 5
MAP_ROWS = 4
MAP_START_ROOM = (2, 1)  # Hub
MAP_ROOM_WIDTH = 120
MAP_ROOM_HEIGHT = 80
MAP_ROOM_GAP = 30
MAP_OFFSET_X = 80
MAP_OFFSET_Y = 80
```

### map.py (new file)

```python
import pygame
import math
import settings
from utils import draw_text

class Room:
    def __init__(self, col, row, data):
        self.col = col
        self.row = row
        self.type = data["type"]
        self.name = data["name"]
        self.narrative = data["narrative"]
        self.connections = data["connections"]
        self.enemies = data["enemies"]
        self.obstacles = data["obstacles"]
        self.boss_hp = data.get("boss_hp", settings.BOSS_HP)
        self.state = "locked"  # locked, available, completed
        self.bob_phase = 0

    @property
    def screen_x(self):
        return settings.MAP_OFFSET_X + self.col * (settings.MAP_ROOM_WIDTH + settings.MAP_ROOM_GAP)

    @property
    def screen_y(self):
        return settings.MAP_OFFSET_Y + self.row * (settings.MAP_ROOM_HEIGHT + settings.MAP_ROOM_GAP)

    @property
    def rect(self):
        return pygame.Rect(self.screen_x, self.screen_y,
                          settings.MAP_ROOM_WIDTH, settings.MAP_ROOM_HEIGHT)


class WorldMap:
    def __init__(self):
        self.rooms = {}
        for (col, row), data in settings.MAP_ROOMS.items():
            self.rooms[(col, row)] = Room(col, row, data)
        
        # Set initial states
        start = settings.MAP_START_ROOM
        self.rooms[start].state = "available"
        for conn in self.rooms[start].connections:
            if conn in self.rooms:
                self.rooms[conn].state = "available"
        
        self.player_room = start
        self.hovered_room = None
        self.anim_timer = 0

    def update(self, dt):
        self.anim_timer += dt
        for room in self.rooms.values():
            room.bob_phase += dt * 3

    def navigate(self, direction):
        """direction: 'up', 'down', 'left', 'right'"""
        col, row = self.player_room
        target = None
        if direction == "up" and (col, row - 1) in self.rooms:
            target = (col, row - 1)
        elif direction == "down" and (col, row + 1) in self.rooms:
            target = (col, row + 1)
        elif direction == "left" and (col - 1, row) in self.rooms:
            target = (col - 1, row)
        elif direction == "right" and (col + 1, row) in self.rooms:
            target = (col + 1, row)
        
        if target:
            self.player_room = target
            return True
        return False

    def select_room(self):
        room = self.rooms.get(self.player_room)
        if room and room.state in ("available", "completed"):
            return room
        return None

    def complete_room(self, room_pos):
        room = self.rooms.get(room_pos)
        if room:
            room.state = "completed"
            for conn in room.connections:
                if conn in self.rooms:
                    conn_room = self.rooms[conn]
                    if conn_room.state == "locked":
                        conn_room.state = "available"

    def draw(self, screen):
        screen.fill(settings.DARK_BLUE)
        
        draw_text(screen, "THE FORBIDDEN ARCHIVE",
                 (settings.WINDOW_WIDTH // 2, 25),
                 settings.CYAN, 32)
        
        # Draw connections first
        for room in self.rooms.values():
            for conn_pos in room.connections:
                conn_room = self.rooms.get(conn_pos)
                if conn_room and conn_room.col >= room.col:  # avoid double-drawing
                    start = room.rect.center
                    end = conn_room.rect.center
                    if room.state == "completed" and conn_room.state == "completed":
                        color = settings.GREEN
                    elif room.state != "locked" and conn_room.state != "locked":
                        color = settings.GRAY
                    else:
                        color = (40, 40, 40)
                    pygame.draw.line(screen, color, start, end, 2)
        
        # Draw rooms
        for room in self.rooms.values():
            self._draw_room(screen, room)
        
        # Draw player avatar
        player_room = self.rooms[self.player_room]
        bob_y = int(math.sin(player_room.bob_phase) * 4)
        avatar_x = player_room.rect.centerx
        avatar_y = player_room.rect.bottom + 20 + bob_y
        pygame.draw.rect(screen, settings.CYAN,
                        (avatar_x - 8, avatar_y - 8, 16, 16))
        pygame.draw.rect(screen, settings.WHITE,
                        (avatar_x - 8, avatar_y - 8, 16, 16), 1)
        
        # Room info at bottom
        if player_room.state != "locked":
            draw_text(screen, player_room.name,
                     (settings.WINDOW_WIDTH // 2, 510),
                     settings.WHITE, 20)
            draw_text(screen, player_room.narrative,
                     (settings.WINDOW_WIDTH // 2, 535),
                     settings.GRAY, 14)
            if player_room.state == "available":
                draw_text(screen, "Press ENTER to enter",
                         (settings.WINDOW_WIDTH // 2, 565),
                         settings.GREEN, 16)
            elif player_room.state == "completed":
                draw_text(screen, "Completed ✓",
                         (settings.WINDOW_WIDTH // 2, 565),
                         settings.GOLD, 16)
        else:
            draw_text(screen, "???",
                     (settings.WINDOW_WIDTH // 2, 535),
                     settings.GRAY, 16)
        
        draw_text(screen, "WASD: Navigate | ENTER: Enter | ESC: Menu",
                 (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT - 15),
                 settings.GRAY, 14)

    def _draw_room(self, screen, room):
        rect = room.rect
        is_player = (room.col, room.row) == self.player_room
        
        if room.type == "hub":
            bg_color = (20, 30, 50)
            border_color = settings.CYAN
        elif room.type == "boss":
            bg_color = (50, 15, 15)
            border_color = settings.RED
        elif room.type == "challenge":
            bg_color = (40, 30, 15)
            border_color = settings.ORANGE
        elif room.type == "victory":
            bg_color = (15, 40, 15)
            border_color = settings.GREEN
        else:
            bg_color = (25, 25, 40)
            border_color = settings.LIGHT_GRAY
        
        if room.state == "locked":
            bg_color = (15, 15, 15)
            border_color = (40, 40, 40)
        
        pygame.draw.rect(screen, bg_color, rect, border_radius=6)
        
        border_width = 3 if is_player else 2
        if is_player:
            pulse = int(180 + 75 * math.sin(room.bob_phase * 2))
            border_color = (pulse, pulse, 255)
            border_width = 3
        
        pygame.draw.rect(screen, border_color, rect, border_width, border_radius=6)
        
        # Room icon
        icon = self._get_room_icon(room)
        draw_text(screen, icon, rect.center,
                 settings.WHITE if room.state != "locked" else (60, 60, 60),
                 24)
        
        # Room name (small)
        draw_text(screen, room.name,
                 (rect.centerx, rect.bottom - 12),
                 settings.LIGHT_GRAY if room.state != "locked" else (50, 50, 50),
                 10)

    def _get_room_icon(self, room):
        if room.state == "completed":
            return "✓"
        if room.state == "locked":
            return "🔒"
        if room.type == "hub":
            return "⌂"
        if room.type == "boss":
            return "⚔"
        if room.type == "challenge":
            return "★"
        if room.type == "victory":
            return "✦"
        return "◇"

    def save(self):
        import json
        data = {
            "player_room": list(self.player_room),
            "rooms": {}
        }
        for pos, room in self.rooms.items():
            data["rooms"][f"{pos[0]},{pos[1]}"] = room.state
        with open("save.json", "w") as f:
            json.dump(data, f)

    def load(self):
        import json
        import os
        if not os.path.exists("save.json"):
            return False
        try:
            with open("save.json", "r") as f:
                data = json.load(f)
            self.player_room = tuple(data["player_room"])
            for pos_str, state in data["rooms"].items():
                pos = tuple(int(x) for x in pos_str.split(","))
                if pos in self.rooms:
                    self.rooms[pos].state = state
            return True
        except:
            return False
```

### game.py — Map Integration

New states: `"MAP"`

In `_handle_keydown()`:
```python
elif self.state == "MAP":
    if event.key == pygame.K_UP:
        self.world_map.navigate("up")
        self.sfx.play("menu_select")
    elif event.key == pygame.K_DOWN:
        self.world_map.navigate("down")
        self.sfx.play("menu_select")
    elif event.key == pygame.K_LEFT:
        self.world_map.navigate("left")
        self.sfx.play("menu_select")
    elif event.key == pygame.K_RIGHT:
        self.world_map.navigate("right")
        self.sfx.play("menu_select")
    elif event.key == pygame.K_RETURN:
        room = self.world_map.select_room()
        if room:
            self.enter_room(room)
            self.sfx.play("menu_confirm")
    elif event.key == pygame.K_ESCAPE:
        self.state = "MENU"
        self.sfx.play("menu_select")
```

New method `enter_room(room)`:
```python
def enter_room(self, room):
    self._init_game_state()
    self.current_room = room
    self.obstacles = [pygame.Rect(o["x"], o["y"], o["w"], o["h"])
                      for o in room.obstacles]
    self.state = "WAVE_INTRO"
    
    # Set up enemies for this room
    self.enemies = []
    for enemy_type, count in room.enemies:
        for _ in range(count):
            x, y = self.get_spawn_position()
            enemy = Enemy(x, y, enemy_type)
            if enemy_type == "boss":
                enemy.max_hp = room.boss_hp
                enemy.hp = room.boss_hp
            self.enemies.append(enemy)
    
    # Override boss HP in settings temporarily
    if room.type == "boss":
        self.boss_hp_override = room.boss_hp
```

In `_update()`:
```python
elif self.state == "MAP":
    self.world_map.update(dt)
```

In `_draw()`:
```python
elif self.state == "MAP":
    self.world_map.draw(self.screen)
```

In `start_game()`:
```python
def start_game(self):
    self._init_game_state()
    self.state = "MAP"
```

In `_init_game_state()`:
```python
from map import WorldMap
self.world_map = WorldMap()
self.world_map.load()
self.current_room = None
self.boss_hp_override = None
```

In wave complete handler:
```python
# When wave is complete, return to map
if self.current_room:
    self.world_map.complete_room((self.current_room.col, self.current_room.row))
    self.world_map.save()
self.state = "MAP"
```

---

## File Change Summary

### New Files (3)
1. `math_bg.py` — Floating math formulas background
2. `map.py` — World map system (WorldMap, Room classes)
3. `rewind_fx.py` — Retro visual effects for rewind

### Modified Files (8)
1. `utils.py` — Add `resolve_obstacle_collision()`
2. `player.py` — No changes needed (obstacle resolution in game.py)
3. `enemy.py` — No changes needed (obstacle resolution in game.py)
4. `ui.py` — Bayes prediction scaling
5. `skills.py` — Skill points visibility fix
6. `rewind.py` — Full-state recording
7. `game.py` — Major: obstacle collision, rewind playback, map integration, math bg
8. `settings.py` — Wave balance, boss HP, map data

### No Changes
- `projectile.py` — Obstacle collision handled in game.py
- `particles.py` — No changes needed
- `sfx.py` — No changes needed
- `floating_text.py` — No changes needed
