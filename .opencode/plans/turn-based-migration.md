# Turn-Based Migration Plan — Ctrl + Alt + Math

## Overview
Convert real-time action game to grid-based tactical turn-based combat (16×12 grid), with math as core mechanics. Victory screen gets 2-3 second delay with particles.

## Design Philosophy
- **Movement = Vectors**: Grid displacement as (dx, dy), Derivada shows enemy velocity vectors
- **Attacks = Equations**: Pitágoras visualizes √(a²+b²), Reflexão creates barrier equations
- **Prediction = Probability**: Bayes shows P(A|B) heatmap on grid cells
- **Entropy = Turn pressure**: Each turn increases entropy, rewind undoes turns at entropy cost
- **Rewind = Undo**: Ctrl+Z undoes last 2 turns (very thematic for turn-based)

---

## Phase A: Grid System

### A.1 Grid Constants (settings.py)
```
GRID_COLS = 16
GRID_ROWS = 12
GRID_CELL_W = ARENA_WIDTH / GRID_COLS   # 47.5px
GRID_CELL_H = ARENA_HEIGHT / GRID_ROWS  # 41.67px
PLAYER_MOVE_RANGE = 3        # tiles per turn
BASIC_ATTACK_RANGE = 1       # adjacent cells
PITAGORAS_RANGE = 3          # tiles (distance formula)
REFLEXAO_RANGE = 2           # tiles (barrier radius)
```

### A.2 New file: grid.py
```
Grid class:
  - cell_size: (w, h) computed from arena dimensions
  - obstacles: set of (col, row) blocked cells
  - to_grid(x, y) -> (col, row)
  - to_pixel(col, row) -> (x, y) center
  - is_blocked(col, row) -> bool
  - get_cells_in_range(center_col, center_row, radius) -> [(col, row), ...]
  - get_cells_in_cone(origin, direction, range) -> [(col, row), ...]
  - pathfind(start, end, obstacles) -> [(col, row), ...]  # A* or BFS
  - draw_grid(screen, highlight_cells, highlight_color)
```

### A.3 Obstacle-to-grid mapping
On room enter, convert ARENA_OBSTACLES rects to blocked grid cells:
```
for each obstacle rect:
    for col in range(grid_cols):
        for row in range(grid_rows):
            cell_rect = grid.cell_rect(col, row)
            if cell_rect.colliderect(obstacle):
                grid.mark_blocked(col, row)
```

---

## Phase B: Turn Manager

### B.1 New file: turn_manager.py
```
TurnManager class:
  - turn_number: int (starts at 1)
  - phase: "PLAYER_INPUT" | "RESOLVE_PLAYER" | "ENEMY_TURN" | "RESOLVE_ENEMIES" | "TURN_END"
  - action_queue: list of pending actions
  - resolve_timer: float (for animation timing)
  - history: list of turn snapshots (for rewind/undo)

Methods:
  - start_turn(): set phase to PLAYER_INPUT
  - queue_player_action(action): add to action_queue
  - execute_player_actions(): animate queued actions
  - execute_enemy_turn(): each enemy decides + acts
  - snapshot(): save full game state for undo
  - undo(n): restore state from n turns ago
  - is_player_turn(): phase in (PLAYER_INPUT, RESOLVE_PLAYER)
```

### B.2 Action types
```
Action = {
    "type": "move" | "attack" | "skill" | "rewind" | "wait",
    "actor": player or enemy,
    "target_col": int,
    "target_row": int,
    "skill_id": str (for skill actions),
    "direction": (dx, dy) (for directional attacks),
}
```

### B.3 Turn flow
```
1. PLAYER_INPUT: Player selects move + action via mouse/keyboard
2. RESOLVE_PLAYER: Animate player movement, then attack (0.5s each)
3. ENEMY_TURN: AI decides each enemy's action
4. RESOLVE_ENEMIES: Animate each enemy action sequentially (0.3s each)
5. TURN_END: Check win/lose, increment entropy, update history, turn_number++
6. Back to PLAYER_INPUT
```

---

## Phase C: Math-Themed Mechanics

### C.1 Movement as Vectors
- Player selects destination cell within move_range (highlighted in blue)
- Movement shown as vector arrow from current to target cell
- Derivada skill: each enemy shows a velocity vector arrow (predicted next move direction)
- Vector length = enemy speed rating, direction = toward player or strategic position

### C.2 Attacks as Equations
**Basic Attack** (Space):
- Melee: hits all enemies in adjacent 8 cells
- Damage: PLAYER_ATTACK_DAMAGE

**Pitágoras** (1, requires unlock):
- Range shown as circle: √(dx² + dy²) ≤ PITAGORAS_RANGE
- Triangle visualization drawn between player and target cell
- Area damage to all enemies in range
- Costs RIGOR

**Reflexão** (2, requires unlock):
- Places barrier on cells within REFLEXAO_RANGE
- Barrier lasts 2 turns
- Enemy projectiles hitting barrier cells are reflected
- Visual: equation "θᵢ = θᵣ" drawn on barrier cells
- Costs RIGOR

### C.3 Bayesian Prediction
- Bayes skill: shows probability heatmap on grid
- Each cell colored by P(enemy moves here | current state)
- Purple intensity = probability
- Formula "P(A|B) = P(B|A)·P(A)/P(B)" shown in HUD corner
- High entropy causes heatmap to flicker/distort

### C.4 Teoria dos Jogos
- Shows targeting matrix: which enemy targets which cell
- Lines from enemies to their predicted target cells
- Color-coded by threat level
- Nash equilibrium indicator on safest cell for player

### C.5 Entropy System (turn-based)
- Each turn: entropy += ENTROPY_PER_TURN (2)
- Rewind (Ctrl+Z): entropy += REWIND_ENTROPY_COST (12)
- High entropy (>50):
  - Grid cells randomly shift by 1 tile (visual only)
  - Prediction heatmap flickers
  - Random "noise" cells appear on grid
- Entropia Controlada skill: rewind cost *= 0.5

### C.6 Rewind/Undo (Ctrl+Z)
- Undoes last 2 turns (player + enemies)
- Full state restore from TurnManager.history
- Katana Zero retro effects during undo animation
- Shows "TURN -2, -1" counting up during animation
- Costs entropy, has cooldown (1 use per 3 turns)

---

## Phase D: Player Turn Input

### D.1 Input system
- **WASD/Arrows**: Move cursor on grid
- **Enter/Space**: Confirm move to cursor cell
- **Mouse click**: Click target cell to move there
- **1/2/R**: Select skill, then click target
- **Tab**: Open skill tree
- **Esc**: Pause
- **Wait key (W after moving)**: Skip action, end turn

### D.2 Action selection flow
```
1. Player sees grid with highlighted valid move cells (blue)
2. Player moves cursor or clicks destination
3. If destination valid:
   a. Player moves there (animation)
   b. Now in ACTION phase: highlight attack range (red)
   c. Player selects attack or skill
   d. If no action: press W to wait, or auto-wait after timeout
4. Turn resolves, enemies act
```

### D.3 UI for turn input
- Top bar: "TURN 5 — YOUR MOVE" (cyan)
- Move range: blue highlighted cells
- Attack range: red highlighted cells (after moving)
- Selected skill range: yellow highlighted cells
- Cursor: glowing cell highlight following mouse/keys
- Action points: "Move: ✓ | Action: ○" (checkmark = used)

---

## Phase E: Enemy AI (Turn-Based)

### E.1 Enemy decision making
Each enemy evaluates options on their turn:
```
1. If in attack range of player: ATTACK
2. If within 2 tiles of player: MOVE toward player, then ATTACK if possible
3. Otherwise: MOVE toward player (pathfinding)
```

### E.2 Enemy types adapted
**Censor**:
- Move: 2 tiles toward player
- Attack: Ranged projectile to player cell (damage 12)
- Behavior: Direct, predictable

**Strawman**:
- Move: 3 tiles, erratic (may move diagonally away)
- Attack: Ranged (damage 8)
- Special: 25% chance to spawn decoy on adjacent cell (decoy lasts 2 turns)

**Bayesian**:
- Move: 2 tiles toward predicted player position
- Attack: Fires at cell where player WILL BE (uses prediction)
- Special: If Bayes skill unlocked, shows extra prediction layer

**Boss**:
- Move: 1 tile
- Phase I: Line attack (1-2 projectiles in player direction)
- Phase II: + Area attack (3×3 cell AoE, 1 turn telegraph shown on grid)
- Phase III: + Double attack (two separate actions per turn)
- HP scales per room (150/180/200)

---

## Phase F: Victory Delay

### F.1 Victory transition
When last enemy dies:
1. Set phase to "VICTORY_TRANSITION"
2. Start 2.5 second timer
3. During transition:
   - Slow particle burst from last enemy position
   - "QED" text appears and grows (mathematical proof complete)
   - Screen gradually brightens
   - Math formulas float up from arena
4. After timer: switch to VictoryScene

### F.2 QED animation
- "Q.E.D." text renders at enemy death position
- Grows from size 16 to 72 over 2 seconds
- Color transitions from WHITE to GOLD
- Accompanied by golden particle burst
- Quod Erat Demonstrandum — "what was to be demonstrated"

---

## Phase G: Scene Updates

### G.1 gameplay_scene.py — Full rewrite
Replace real-time loop with turn-based:
```
handle_event():
  - Phase-based input handling
  - Grid cursor movement
  - Action confirmation

update():
  - Phase transitions
  - Action resolution animations
  - Enemy AI execution
  - Victory transition timer

draw():
  - Grid overlay
  - Range highlights
  - Vector arrows
  - Probability heatmap
  - Turn indicator
  - All existing visual elements (particles, floating text, etc.)
```

### G.2 New scenes
- No new scenes needed — existing scene structure works
- VictoryScene gets updated with QED reference

---

## Phase H: File Changes Summary

### New Files (3)
1. `grid.py` — Grid system, cell management, pathfinding, drawing
2. `turn_manager.py` — Turn state machine, action queue, history/undo
3. `action_resolver.py` — Animate movement, attacks, skills on grid

### Modified Files (10)
1. `settings.py` — Grid constants, turn-based constants, entropy per turn
2. `game.py` — Turn-based shared state, reset logic
3. `scenes/gameplay_scene.py` — Full rewrite for turn-based loop
4. `scenes/victory_scene.py` — QED reference, delayed entry
5. `player.py` — Grid-based movement, cell position tracking
6. `enemy.py` — Turn-based AI, grid positioning
7. `ui.py` — Turn HUD, grid overlays, range indicators, probability heatmap
8. `skills.py` — Adapted skill descriptions for turn-based
9. `rewind.py` — Turn-based undo (state snapshots instead of time buffer)
10. `map.py` — Room data includes grid obstacle mapping

### No Changes
- `projectile.py` — Still works, just launched on grid
- `particles.py` — Unchanged
- `sfx.py` — Unchanged
- `floating_text.py` — Unchanged
- `scenes/scene.py` — Unchanged
- `scenes/scene_manager.py` — Unchanged
- `scenes/menu_scene.py` — Unchanged
- `scenes/map_scene.py` — Unchanged
- `scenes/skill_tree_scene.py` — Unchanged
- `scenes/pause_scene.py` — Unchanged
- `scenes/game_over_scene.py` — Unchanged
- `rewind_fx.py` — Unchanged
- `math_bg.py` — Unchanged

---

## Implementation Order

1. **Phase A**: Grid system (grid.py + settings)
2. **Phase F**: Victory delay (quick win, test early)
3. **Phase B**: Turn manager (turn_manager.py)
4. **Phase C**: Math mechanics (integrated into grid + turn manager)
5. **Phase D**: Player input (gameplay_scene rewrite)
6. **Phase E**: Enemy AI (enemy.py turn-based)
7. **Phase G**: Scene integration + UI
8. **Phase H**: Polish, testing, balance

## Key Tradeoffs
- **Lost**: Real-time movement fluidity, projectile dodging
- **Gained**: Strategic depth, math theme integration, puzzle-like combat
- **Preserved**: All skills, rewind, entropy, boss phases, map system, particles, SFX
