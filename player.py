import pygame
import math
import random

import settings
from utils import clamp, distance


class Player:
    def __init__(self):
        self.x = settings.WINDOW_WIDTH // 2
        self.y = settings.WINDOW_HEIGHT // 2 + 50
        self.col = 8
        self.row = 6
        self.size = settings.PLAYER_SIZE
        self.hp = settings.PLAYER_MAX_HP
        self.max_hp = settings.PLAYER_MAX_HP
        self.base_damage = settings.PLAYER_ATTACK_DAMAGE
        self.rigor = settings.PLAYER_MAX_RIGOR
        self.max_rigor = settings.PLAYER_MAX_RIGOR
        
        self.level = 1
        self.exp = 0
        self.next_level_exp = settings.PLAYER_EXP_BASE
        self.move_range = settings.PLAYER_MOVE_RANGE
        self.upgrade_tickets = 0

        self.defense = 0
        self.upgrades = {"atk": 0, "def": 0, "hp": 0, "range": 0}
        self.gold = 0
        self.inventory = []
        self.equipment = {"weapon": "basic_sword", "shield": "wooden_shield"}
        self.buffs = []

        self.dir_x = 0
        self.dir_y = -1

        self.invulnerable = 0
        self.flash_timer = 0
        self.pitagoras_cooldown = 0
        self.reflexao_cooldown = 0

        self.glow_phase = 0
        self.trail = []
        self.trail_max = 8

        self.anim_progress = 1.0
        self.anim_from_col = 8
        self.anim_from_row = 6
        self.anim_to_col = 8
        self.anim_to_row = 6
        self.anim_from_px = 0
        self.anim_from_py = 0
        self.anim_to_px = 0
        self.anim_to_py = 0
        self.anim_cells = []
        self.anim_step_idx = 0

        self.last_crit = False

        self.skin_index = 0
        self.skin_names = [
            "Assault", "SquadLeader", "AntiTank", "Grenadier",
            "MachineGunner", "RadioOperator", "Sniper"
        ]
        self.skin_paths = {
            "Assault": "assets/Soldiers/Assault-Class.png",
            "SquadLeader": "assets/Soldiers/SquadLeader.png",
            "AntiTank": "assets/Soldiers/AntiTank-Class.png",
            "Grenadier": "assets/Soldiers/Grenadier-Class.png",
            "MachineGunner": "assets/Soldiers/MachineGunner-Class.png",
            "RadioOperator": "assets/Soldiers/RadioOperator-Class.png",
            "Sniper": "assets/Soldiers/Sniper-Class.png"
        }
        self.spritesheets = {}
        self.load_skins()

        self.current_anim = "idle"
        self.anim_frame = 0
        self.anim_timer = 0
        self.anim_speed = 0.2
        self.sprite_size = 16
        self.display_size = 64

        self.anim_map = {
            "idle": 0, "walk": 1, "crawl": 2, "fire": 3,
            "hit": 4, "death": 5, "throw": 6
        }
        self.anim_frames = {
            "idle": 2, "walk": 2, "crawl": 2, "fire": 2,
            "hit": 3, "death": 5, "throw": 3
        }

        self.effects = {}
        self.load_effects()

    def load_effects(self):
        try:
            self.effects["blood"] = pygame.image.load("assets/Effects/hit-spatters.png").convert_alpha()
            self.effects["muzzle"] = pygame.image.load("assets/Effects/muzzle-flashes.png").convert_alpha()
        except Exception as e:
            print(f"Error loading effects: {e}")

    def load_skins(self):
        for name, path in self.skin_paths.items():
            try:
                sheet = pygame.image.load(path).convert_alpha()
                self.spritesheets[name] = sheet
            except Exception as e:
                print(f"Error loading skin {name}: {e}")

    def toggle_skin(self):
        self.skin_index = (self.skin_index + 1) % len(self.skin_names)

    def get_current_sprite(self):
        skin_name = self.skin_names[self.skin_index]
        sheet = self.spritesheets.get(skin_name)
        if not sheet:
            return None

        row = self.anim_map.get(self.current_anim, 0)
        col = int(self.anim_frame) % self.anim_frames.get(self.current_anim, 1)

        rect = pygame.Rect(col * self.sprite_size, row * self.sprite_size,
                           self.sprite_size, self.sprite_size)
        try:
            return sheet.subsurface(rect)
        except:
            return None

    def check_crit(self):
        self.last_crit = random.random() < settings.PLAYER_CRIT_CHANCE
        return self.last_crit

    def set_grid_position(self, col, row, grid):
        self.col = int(col)
        self.row = int(row)
        self.x, self.y = grid.to_pixel(self.col, self.row)

    def _begin_anim_step(self, grid):
        from_col, from_row = self.anim_cells[self.anim_step_idx]
        to_col, to_row = self.anim_cells[self.anim_step_idx + 1]
        self.anim_from_col = from_col
        self.anim_from_row = from_row
        self.anim_to_col = to_col
        self.anim_to_row = to_row
        self.anim_from_px, self.anim_from_py = grid.to_pixel(from_col, from_row)
        self.anim_to_px, self.anim_to_py = grid.to_pixel(to_col, to_row)
        self.anim_progress = 0.0
        self.current_anim = "walk"
        self.dir_x = to_col - from_col
        self.dir_y = to_row - from_row
        length = math.sqrt(self.dir_x ** 2 + self.dir_y ** 2)
        if length > 0:
            self.dir_x /= length
            self.dir_y /= length

    def start_move_anim(self, from_col, from_row, to_col, to_row, grid, path=None):
        if path is None:
            path = [(to_col, to_row)]
        self.anim_cells = [(from_col, from_row)] + [(int(col), int(row)) for col, row in path]
        self.anim_step_idx = 0
        self._begin_anim_step(grid)

    def is_animating(self):
        return len(self.anim_cells) > 1

    def update_animation(self, dt, grid=None):
        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % self.anim_frames.get(self.current_anim, 1)

        if self.is_animating():
            self.current_anim = "walk"
            self.anim_progress = min(1.0, self.anim_progress + dt * 10)
            frac = self.anim_progress
            frac = frac * frac * (3 - 2 * frac)
            self.x = self.anim_from_px + (self.anim_to_px - self.anim_from_px) * frac
            self.y = self.anim_from_py + (self.anim_to_py - self.anim_from_py) * frac
            if self.anim_progress >= 1.0:
                self.anim_step_idx += 1
                self.col = int(self.anim_to_col)
                self.row = int(self.anim_to_row)
                if self.anim_step_idx >= len(self.anim_cells) - 1:
                    self.anim_cells = []
                    self.anim_step_idx = 0
                    self.anim_progress = 1.0
                    self.current_anim = "idle"
                if grid is not None:
                    self.x, self.y = grid.to_pixel(self.col, self.row)
                    if self.anim_step_idx < len(self.anim_cells):
                        self._begin_anim_step(grid)
        else:
            self.current_anim = "idle"
            if grid is not None:
                self.x, self.y = grid.to_pixel(self.col, self.row)

    def update(self, dt, keys):
        self.invulnerable = max(0, self.invulnerable - dt)
        self.flash_timer = max(0, self.flash_timer - dt)
        self.glow_phase += dt * 4

    def decrement_cooldowns(self):
        self.pitagoras_cooldown = getattr(self, 'pitagoras_cooldown', 0)
        self.reflexao_cooldown = getattr(self, 'reflexao_cooldown', 0)
        self.pitagoras_cooldown = max(0, self.pitagoras_cooldown - 1)
        self.reflexao_cooldown = max(0, self.reflexao_cooldown - 1)

    def add_exp(self, amount):
        self.exp += amount
        leveled_up = False
        while self.exp >= self.next_level_exp:
            self.exp -= self.next_level_exp
            self.level_up()
            leveled_up = True
        return leveled_up

    def level_up(self):
        self.level += 1
        self.hp = self.max_hp
        self.next_level_exp = int(self.next_level_exp * settings.PLAYER_EXP_GROWTH)
        if self.level % 2 == 0:
            self.move_range += 1
        self.upgrade_tickets += 1

    def get_attack_damage(self):
        base = settings.PLAYER_ATTACK_DAMAGE + self.upgrades["atk"] * settings.UPGRADE_PER_LEVEL["atk"]
        weapon_data = settings.EQUIPMENT_DATA["weapons"].get(self.equipment.get("weapon"), {})
        multiplier = weapon_data.get("multiplier", 1.0)
        return int(base * multiplier) + self._buff_sum("atk_buff")

    def get_attack_multiplier(self):
        weapon_data = settings.EQUIPMENT_DATA["weapons"].get(self.equipment.get("weapon"), {})
        return weapon_data.get("multiplier", 1.0)

    def get_weapon_effect(self):
        weapon_data = settings.EQUIPMENT_DATA["weapons"].get(self.equipment.get("weapon"), {})
        return weapon_data.get("effect")

    def get_defense(self):
        shield_data = settings.EQUIPMENT_DATA["shields"].get(self.equipment.get("shield"), {})
        return self.upgrades["def"] * settings.UPGRADE_PER_LEVEL["def"] + shield_data.get("defense", 0) + self._buff_sum("def_buff")

    def get_max_hp(self):
        return settings.PLAYER_MAX_HP + self.upgrades["hp"] * settings.UPGRADE_PER_LEVEL["hp"] + self._buff_sum("max_hp_buff")

    def get_move_range(self):
        return settings.PLAYER_MOVE_RANGE + self.upgrades["range"] + self._buff_sum("range_buff")

    def get_upgrade_cost(self, upgrade_type):
        data = settings.UPGRADE_COSTS[upgrade_type]
        return int(data["base_cost"] * (data["cost_scale"] ** self.upgrades[upgrade_type]))

    def buy_upgrade(self, upgrade_type):
        if getattr(self, "upgrade_tickets", 0) > 0:
            self.upgrade_tickets -= 1
            self.upgrades[upgrade_type] += 1
            if upgrade_type == "hp":
                old_max = self.max_hp
                self.max_hp = self.get_max_hp()
                self.hp += (self.max_hp - old_max)
            return True

        cost = self.get_upgrade_cost(upgrade_type)
        if self.gold >= cost:
            self.gold -= cost
            self.upgrades[upgrade_type] += 1
            if upgrade_type == "hp":
                old_max = self.max_hp
                self.max_hp = self.get_max_hp()
                self.hp += (self.max_hp - old_max)
            return True
        return False

    def add_buff(self, effect, value, scope="room", turns=0):
        self.buffs.append({"effect": effect, "value": value, "scope": scope, "turns_left": turns})

    def tick_buffs(self):
        expired = []
        for i, buff in enumerate(self.buffs):
            if buff["scope"] == "turns":
                buff["turns_left"] -= 1
                if buff["turns_left"] <= 0:
                    expired.append(i)
        for i in reversed(expired):
            self.buffs.pop(i)

    def clear_room_buffs(self):
        self.buffs = [b for b in self.buffs if b["scope"] != "room"]

    def _buff_sum(self, effect_key):
        return sum(b["value"] for b in self.buffs if b["effect"] == effect_key)

    def use_consumable(self, item_id):
        for i, item in enumerate(self.inventory):
            if item.get("id") == item_id:
                data = settings.CONSUMABLE_DATA.get(item_id, {})
                if not data:
                    return False
                effect = data["effect"]
                value = data["value"]
                scope = data.get("scope", "instant")
                duration = data.get("duration", 0)
                if effect == "heal":
                    self.hp = min(self.hp + value, self.get_max_hp())
                elif effect in ("atk_buff", "def_buff", "range_buff", "max_hp_buff"):
                    turns = duration if scope == "turns" else 0
                    self.add_buff(effect, value, scope=scope, turns=turns)
                    if effect == "max_hp_buff":
                        new_max = self.get_max_hp()
                        self.hp = min(self.hp + value, new_max)
                if item.get("count", 1) > 1:
                    item["count"] -= 1
                else:
                    self.inventory.pop(i)
                return True
        return False

    def basic_attack(self):
        return True

    def pitagoras_attack(self):
        if getattr(self, 'pitagoras_cooldown', 0) > 0:
            return False
        if self.rigor < settings.PITAGORAS_RIGOR_COST:
            return False
        self.rigor -= settings.PITAGORAS_RIGOR_COST
        self.pitagoras_cooldown = 1
        return True

    def reflexao_attack(self):
        if getattr(self, 'reflexao_cooldown', 0) > 0:
            return False
        if self.rigor < settings.REFLEXAO_RIGOR_COST:
            return False
        self.rigor -= settings.REFLEXAO_RIGOR_COST
        self.reflexao_cooldown = 3
        return True

    def take_damage(self, amount):
        if self.invulnerable > 0:
            return False
        self.hp = max(0, self.hp - amount)
        self.invulnerable = 0.4
        self.flash_timer = 0.4
        return True

    def set_position(self, pos):
        self.x, self.y = pos

    def set_hp(self, hp, max_hp):
        self.hp = hp
        self.max_hp = max_hp

    def draw(self, screen, offset=(0, 0)):
        ox, oy = offset
        for tx, ty, t in self.trail:
            alpha = int((t / 0.3) * 100)
            trail_size = int(self.display_size * (t / 0.3))
            if trail_size > 0:
                sprite = self.get_current_sprite()
                if sprite:
                    if self.dir_x < 0:
                        sprite = pygame.transform.flip(sprite, True, False)
                    s = pygame.transform.scale(sprite, (trail_size, trail_size))
                    s.set_alpha(alpha)
                    screen.blit(s, (tx + ox - trail_size // 2, ty + oy - trail_size // 2))

        # Subtle shadow
        shadow_size = int(self.size * 0.8)
        shadow_surf = pygame.Surface((shadow_size * 2, shadow_size // 2), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 100), (0, 0, shadow_size * 2, shadow_size // 2))
        screen.blit(shadow_surf, (self.x + ox - shadow_size, self.y + oy + self.size - 4))

        glow_size = int(5 + math.sin(self.glow_phase) * 3)
        glow_surf = pygame.Surface((self.display_size + glow_size * 2,
                                     self.display_size + glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (settings.CYAN[0], settings.CYAN[1], settings.CYAN[2], 30),
                           (self.display_size // 2 + glow_size, self.display_size // 2 + glow_size),
                           self.display_size // 2 + glow_size)
        screen.blit(glow_surf, (self.x + ox - self.display_size // 2 - glow_size,
                                 self.y + oy - self.display_size // 2 - glow_size))

        color = settings.COLOR_PLAYER
        if self.flash_timer > 0:
            color = settings.WHITE
        elif self.invulnerable > 0:
            if int(self.invulnerable * 10) % 2 == 0:
                color = (100, 200, 200)

        sprite = self.get_current_sprite()
        if sprite:
            if self.dir_x < 0:
                sprite = pygame.transform.flip(sprite, True, False)

            # Scale up for better visibility
            sprite = pygame.transform.scale(sprite, (self.display_size, self.display_size))

            if color == settings.WHITE:
                # Flash effect for damage
                flash_surf = sprite.copy()
                flash_surf.fill((255, 255, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
                screen.blit(flash_surf, (self.x + ox - self.display_size // 2, self.y + oy - self.display_size // 2))
            else:
                screen.blit(sprite, (self.x + ox - self.display_size // 2, self.y + oy - self.display_size // 2))

            # Overlay effects
            if self.current_anim == "fire" and self.anim_frame == 0:
                muzzle = self.effects.get("muzzle")
                if muzzle:
                    try:
                        m_surf = muzzle.subsurface(pygame.Rect(0, 0, 16, 8))
                        m_surf = pygame.transform.scale(m_surf, (self.display_size, self.display_size // 2))
                        if self.dir_x < 0:
                            m_surf = pygame.transform.flip(m_surf, True, False)
                        screen.blit(m_surf, (self.x + ox - self.display_size // 2, self.y + oy - self.display_size // 2))
                    except: pass
            elif self.current_anim in ("hit", "death") and self.anim_frame == 0:
                blood = self.effects.get("blood")
                if blood:
                    try:
                        b_surf = blood.subsurface(pygame.Rect(0, 0, 16, 8))
                        b_surf = pygame.transform.scale(b_surf, (self.display_size, self.display_size // 2))
                        if self.dir_x < 0:
                            b_surf = pygame.transform.flip(b_surf, True, False)
                        screen.blit(b_surf, (self.x + ox - self.display_size // 2, self.y + oy - self.display_size // 2))
                    except: pass
        else:
            rect = pygame.Rect(self.x + ox - self.size, self.y + oy - self.size,
                               self.size * 2, self.size * 2)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, settings.WHITE, rect, 1)

        tip_x = self.x + ox + self.dir_x * self.size * 1.8
        tip_y = self.y + oy + self.dir_y * self.size * 1.8
        pygame.draw.line(screen, settings.WHITE,
                         (self.x + ox, self.y + oy), (tip_x, tip_y), 3)

        if abs(self.dir_x) + abs(self.dir_y) > 0:
            font = pygame.font.Font(None, 14)
            symbol = "f"
            if self.last_crit:
                symbol = "f'"
                sym_color = settings.GOLD
            else:
                sym_color = settings.CYAN
            label = font.render(symbol, True, sym_color)
            screen.blit(label, (self.x + ox - label.get_width() // 2,
                                self.y + oy - self.size - 12))
