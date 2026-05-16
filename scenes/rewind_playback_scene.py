import pygame

import settings
from utils import draw_text
from scenes.scene import Scene


class RewindPlaybackScene(Scene):
    overlay = True

    def __init__(self, game):
        super().__init__(game)
        self.playback_index = 0
        self.playback_timer = 0

    def enter(self, prev_scene=None):
        self.playback_index = len(self.game.rewind_buffer.buffer) - 1
        self.playback_timer = 0

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.game.scene_manager.pop()

    def update(self, dt):
        self.playback_timer += dt * 4
        step = int(self.playback_timer * 15)
        target_index = max(0, self.playback_index - step)

        if target_index <= 0:
            if self.game.rewind_buffer.buffer:
                self._apply_snapshot(self.game.rewind_buffer.buffer[0])
            self.game.rewind_cooldown = 2.0
            ent_inc = settings.REWIND_ENTROPY_INCREASE
            if self.game.skill_tree.is_unlocked("entropia"):
                ent_inc *= 0.5
            self.game.entropy = min(settings.MAX_ENTROPY, self.game.entropy + ent_inc)
            self.game.particles.emit_burst(
                self.game.player.x, self.game.player.y,
                settings.CYAN, 30, 100, 0.6
            )
            self.game.hit_stop_timer = 0.08
            self.game.hit_stop_duration = 0.08
            self.game.scene_manager.pop()
            return

        snapshot = self.game.rewind_buffer.buffer[target_index]
        self.playback_index = target_index
        self._apply_snapshot(snapshot)

        self.game.particles.update(dt)
        self.game.floating_text.update(dt)

    def _apply_snapshot(self, snapshot):
        self.game.player.x = snapshot['player']['x']
        self.game.player.y = snapshot['player']['y']
        self.game.player.hp = snapshot['player']['hp']
        self.game.player.max_hp = snapshot['player']['max_hp']

        for e_data in snapshot['enemies']:
            found = False
            for e in self.game.enemies:
                if e.type == e_data['type'] and not e.dead:
                    e.x = e_data['x']
                    e.y = e_data['y']
                    e.hp = e_data['hp']
                    e.max_hp = e_data['max_hp']
                    found = True
                    break
            if not found:
                from enemy import Enemy
                new_enemy = Enemy(e_data['x'], e_data['y'], e_data['type'])
                new_enemy.hp = e_data['hp']
                new_enemy.max_hp = e_data['max_hp']
                new_enemy.size = e_data['size']
                new_enemy.color = e_data['color']
                self.game.enemies.append(new_enemy)

        for e in self.game.enemies:
            if not e.dead:
                match = False
                for e_data in snapshot['enemies']:
                    if (e.type == e_data['type'] and
                        abs(e.x - e_data['x']) < 5 and
                        abs(e.y - e_data['y']) < 5):
                        match = True
                        break
                if not match:
                    e.alive = False
                    e.dead = True

        self.game.projectiles = []
        for p_data in snapshot['projectiles']:
            from projectile import Projectile
            proj = Projectile(
                p_data['x'], p_data['y'],
                p_data['vx'], p_data['vy'],
                p_data['damage'], p_data['owner'],
                color=p_data['color'], size=p_data['size']
            )
            self.game.projectiles.append(proj)

    def draw(self, screen):
        self.game.scene_manager.get("gameplay").draw(screen)
        self.game.rewind_fx.apply_rewind_fx(screen, pygame.time.get_ticks() / 1000.0)
