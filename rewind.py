import pygame

import settings


class RewindBuffer:
    def __init__(self):
        self.buffer = []
        self.timer = 0

    def record(self, player_pos, player_hp, player_max_hp, dt):
        self.timer += dt
        if self.timer >= settings.REWIND_SNAPSHOT_INTERVAL:
            self.timer = 0
            self.buffer.append({
                'pos': (player_pos[0], player_pos[1]),
                'hp': player_hp,
                'max_hp': player_max_hp,
                'time': pygame.time.get_ticks()
            })
            cutoff = pygame.time.get_ticks() - settings.REWIND_BUFFER_SECONDS * 1000
            while self.buffer and self.buffer[0]['time'] < cutoff:
                self.buffer.pop(0)

    def rewind(self):
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
        return (best['pos'], best['hp'], best['max_hp'])

    def clear(self):
        self.buffer.clear()
        self.timer = 0
