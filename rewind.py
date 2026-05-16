import pygame

import settings


class RewindBuffer:
    def __init__(self):
        self.buffer = []
        self.timer = 0

    def record(self, player, enemies, projectiles, dt):
        self.timer += dt
        interval = 0.08
        if self.timer >= interval:
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
            cutoff = pygame.time.get_ticks() - 3000
            while self.buffer and self.buffer[0]['time'] < cutoff:
                self.buffer.pop(0)

    def rewind(self):
        if not self.buffer:
            return None
        target_time = pygame.time.get_ticks() - 1500
        best = None
        for entry in reversed(self.buffer):
            if entry['time'] <= target_time:
                best = entry
                break
        if best is None:
            best = self.buffer[0]
        return best

    def clear(self):
        self.buffer.clear()
        self.timer = 0
