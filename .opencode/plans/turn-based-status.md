# Turn-Based Migration — Current Status & Remaining Work

## DONE (Working)
- Grid system (grid.py): 16×12 grid, pathfinding (BFS), reachable cells, radius/cone queries, barriers
- Turn manager (turn_manager.py): phase state machine, action queue, state snapshots, undo
- Player grid positioning (player.py): col/row, set_grid_position(), animation interpolation
- Enemy grid positioning (enemy.py): col/row, set_grid_position(), decide_action() for AI, move/attack/line_attack/area_attack
- Gameplay scene (scenes/gameplay_scene.py): full turn-based loop with grid cursor, range highlights, enemy AI resolution
- Map system (map.py): 15-room world, navigation, room entry, completion/saving
- Victory transition (scenes/victory_scene.py): QED animation, 2.5s delay
- Scene architecture: scene_manager with push/pop/switch, prev_scene passing
- Wave balance: reduced enemy counts, boss HP 150
- Skills menu: points visible at y=110 after nodes

## BUGS FOUND
1. **Animation interpolation broken**: `update_animation()` computes float col/row, but then tries to set x/y from grid.to_pixel() which floors floats → jerky movement. Need to interpolate pixel positions directly: `x/y = lerp(from_pixel, to_pixel, t)`
2. **Hub room auto-victory**: Hub has 0 enemies → immediately triggers VICTORY_TRANSITION. Need to handle rooms with no enemies as "already completed" or skip to map.
3. **Undo resets wrong state**: TurnManager.undo() modifies the game_state dict in place, but doesn't actually restore game.enemies/player.hp properly. The undo method modifies the dict but the game objects aren't updated from it.
4. **Float col/row vs int col/row**: After animation completes, col/row should be ints but can remain as floats. This causes grid_distance() issues.
5. **Player not shown during WAVE_INTRO**: When entering room, state is WAVE_INTRO but no key handler processes it to transition to PLAYER_INPUT. The WAVE_INTRO state should auto-transition or accept key.
6. **MANUAL ATTACK_RANGE constants duplicated**: STRAWMAN_ATTACK_RANGE and BOSS_ATTACK_RANGE exist in both settings.py and enemy.py (as instance vars). Need to ensure consistency.
7. **Real-time remnants still in game.py**: projectile handling, queue_basic_damage, queue_pitagoras_damage, ENTITY_ACTION_INTERVAL references in old code paths.
8. **rewind_playback_scene.py references Projectile**: The rewind playback scene still imports and creates Projectiles, which aren't used in turn-based mode.

## MISSING FEATURES (from plan)
1. **Derivada skill visualization**: Enemy velocity arrows drawn on grid during player's turn (lines of code exist in gameplay_scene but may need tuning)
2. **Bayes probability heatmap**: P(A|B) overlay on grid cells showing enemy attack probability (partially implemented in draw method)
3. **Teoria dos Jogos targeting lines**: Lines from enemies to their target cells (partially implemented in draw method)
4. **Pitagoras triangle visualization**: Draw right triangle from player to target cell showing a²+b²=c² (lines exist in gameplay_scene for triangle)
5. **Reflexão barrier cell rendering**: grid.draw_barriers() exists and draws barrier cells with θᵢ=θᵣ equation
6. **Turn indicator UI**: "TURN X — YOUR MOVE" / "ENEMY TURN" text drawn at bottom of screen (implemented)
7. **Move/Action point display**: "Move: ✓ | Action: ○" shown in HUD (implemented)
8. **Rigor regeneration**: Changed from time-based (8/sec with 2s delay) to per-turn (15/turn, no delay) but player.update() still Uses RIGOR_REGEN_RATE * dt
9. **Skill descriptions need updating**: Currently say "Press 1 to use" etc., should say "Grid range 3" etc.
10. **Local co-op**: Not started (second player with arrow keys + numpad)
11. **Sound effects for turn transitions**: Not implemented
12. **Screen drawing for non-hub rooms with obstacles**: Grid draws on top of obstacles (background obstacles + grid lines, may look cluttered)

## DETAILED FIXES NEEDED

### Fix 1: Animation interpolation (Critical)
**File**: player.py, enemy.py
**Problem**: `update_animation()` sets col/row as interpolated floats and uses grid.to_pixel() which takes ints
**Fix**: Store from_pixel/to_pixel, interpolate x/y directly:
```python
def start_move_anim(self, from_col, from_row, to_col, to_row, grid):
    self.anim_from_col = from_col
    self.anim_from_row = from_row
    self.anim_to_col = to_col
    self.anim_to_row = to_row
    self.anim_from_px, self.anim_from_py = grid.to_pixel(from_col, from_row)
    self.anim_to_px, self.anim_to_py = grid.to_pixel(to_col, to_row)
    self.anim_progress = 0.0

def update_animation(self, dt):
    if self.anim_progress < 1.0:
        self.anim_progress = min(1.0, self.anim_progress + dt * 5)
        t = self.anim_progress * self.anim_progress * (3 - 2 * self.anim_progress)  # smoothstep
        self.x = self.anim_from_px + (self.anim_to_px - self.anim_from_px) * t
        self.y = self.anim_from_py + (self.anim_to_py - self.anim_from_py) * t
    # When complete, snap to exact position:
    if self.anim_progress >= 1.0:
        self.col = self.anim_to_col
        self.row = self.anim_to_row
        self.x, self.y = grid.to_pixel(self.anim_to_col, self.anim_to_row)
```

### Fix 2: Hub room auto-victory (High)
**File**: scenes/gameplay_scene.py
**Problem**: Room with 0 enemies immediately triggers VICTORY_TRANSITION
**Fix**: Add check in enter() and in WAVE_INTRO handler:
```python
if len(room.enemies) == 0 and room.type != "hub":
    # Victory room with no enemies
    self.state = "VICTORY_TRANSITION"
elif len(room.enemies) == 0 and room.type == "hub":
    # Hub room - just show briefly then return to map
    self.state = "WAVE_INTRO"  # Shows narrative, then player can leave
```
Better: Hub rooms should immediately return to map. Add a "NO_COMBAT" state.

### Fix 3: Undo state restoration (High)
**File**: turn_manager.py
**Problem**: undo() modifies game_state dict but doesn't update game objects
**Fix**: Return the target snapshot and let gameplay_scene apply it:
```python
def undo(self):
    if len(self.history) < 2:
        return None
    target = self.history[-2]
    self.history = self.history[:-2]
    self.turn_number = target["turn"]
    return target  # Let gameplay scene apply the snapshot
```
Then in gameplay_scene._try_rewind():
```python
result = self.turn_manager.undo()
if result:
    self.game.player.col = result["player"]["col"]
    self.game.player.row = result["player"]["row"]
    self.game.player.hp = result["player"]["hp"]
    # ... restore enemies, entropy, barriers
```

### Fix 4: Float col/row → int (Medium)
**Files**: player.py, enemy.py
**Problem**: After animation, col/row can be floats causing grid_distance issues
**Fix**: Ensure col/row are always ints after animation completes. Add `int()` conversion.

### Fix 5: WAVE_INTRO auto-transition (Medium)
**File**: scenes/gameplay_scene.py
**Problem**: WAVE_INTRO state requires keypress but should auto-transition for rooms
**Fix**: Change WAVE_INTRO to auto-fade after 1.5s or on any key. Actually the current code does handle it:
```python
if self.state == "WAVE_INTRO":
    self.state = "PLAYER_INPUT"
    self.turn_manager.start_turn()
    self.show_move_range = True
    self.game.sfx.play("wave_start")
```
This works on keydown. The issue is the handle_event method only processes KEYDOWN, so it needs a keypress. This is fine - player presses Enter to start.

### Fix 6: Attack range constants consistency (Low)
**Files**: settings.py, enemy.py
**Problem**: STRAWMAN_ATTACK_RANGE and BOSS_ATTACK_RANGE defined in both settings.py and enemy.py
**Fix**: Remove from enemy.py, use settings constants only.

### Fix 7: Clean up real-time remnants from game.py (Medium)
**File**: game.py
**Problem**: Still has projectiles list, queue_basic_damage, queue_pitagoras_damage, wave_countdown, current_wave
**Fix**: Remove unused attributes from _init_shared_state and reset_game_state.

### Fix 8: Remove rewind_playback_scene.py (Medium)
**Problem**: References Projectile, no longer used in turn-based mode. The rewind animation should happen within gameplay_scene using retro effects during TurnManager.undo().
**Fix**: Delete the scene, or repurpose it for a brief rewind animation overlay during undo.

## POLISH ITEMS
1. **Derivada skill arrows**: Already drawing in gameplay_scene.draw(), need to test with unlocked skill
2. **Bayes heatmap**: Already drawing probability cells when unlocked, need to test
3. **Teoria dos Jogos targeting**: Already drawing targeting lines, need to test  
4. **Pitagoras triangle**: grid.draw_triangle() exists, need to add to action selection visualization
5. **Skill descriptions update**: Change from "Press 1" to "Range 3 tiles (a²+b²=c²)"
6. **Rigor regen**: Should be per-turn (15) not per-second, needs update in player.update() to not use dt
7. **Sound effects**: Add turn_start, grid_cursor, move_confirm, attack_hit sounds in sfx.py
8. **Grid visual polish**: Make grid lines more subtle, better obstacle rendering
9. **Enemy death animation**: Add fade-out when enemy dies on grid
10. **Player death screen**: Game over should work with turn-based
11. **Hub rooms**: Should either be safe zones or auto-complete with narrative text
12. **Save/load for map progress**: Already implemented in WorldMap.save()/load()

## IMPLEMENTATION ORDER
1. Fix animation interpolation (Critical, affects all visual movement)
2. Fix hub room auto-victory (High, blocks gameplay flow)
3. Fix undo state restoration (High, breaks rewind)
4. Fix float col/row → int (Medium, causes grid bugs)
5. Clean up real-time remnants (Medium, removes dead code)
6. Update skill descriptions (Medium, user-facing)
7. Add sound effects for turn transitions (Low, polish)
8. Test full flow: menu → map → room → combat → victory → map (Integration)
9. Test boss fights (Integration)
10. Polish grid visuals (Low, polish)
