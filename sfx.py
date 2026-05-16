import pygame
import math


class SFX:
    def __init__(self):
        self.enabled = True
        self.volume = 0.3
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        except Exception:
            self.enabled = False

    def _tone(self, freq, duration, vol=0.3, wave="square", decay=0.8):
        if not self.enabled:
            return None
        sample_rate = 22050
        n_samples = int(sample_rate * duration)
        buf = bytearray(n_samples * 2)
        for i in range(n_samples):
            t = i / sample_rate
            env = math.exp(-decay * t / duration)
            if wave == "square":
                val = int(32767 * vol * env * (1 if math.sin(2 * math.pi * freq * t) >= 0 else -1))
            elif wave == "sine":
                val = int(32767 * vol * env * math.sin(2 * math.pi * freq * t))
            elif wave == "saw":
                phase = (freq * t) % 1.0
                val = int(32767 * vol * env * (2 * phase - 1))
            elif wave == "noise":
                import random
                val = int(32767 * vol * env * (2 * random.random() - 1))
            else:
                val = int(32767 * vol * env * math.sin(2 * math.pi * freq * t))
            val = max(-32768, min(32767, val))
            buf[i * 2] = val & 0xFF
            buf[i * 2 + 1] = (val >> 8) & 0xFF
        snd = pygame.mixer.Sound(buffer=bytes(buf))
        snd.set_volume(self.volume)
        return snd

    def play(self, name):
        if not self.enabled:
            return
        sounds = {
            "basic_attack": lambda: self._tone(440, 0.08, 0.2, "square"),
            "pitagoras": lambda: self._tone(660, 0.15, 0.25, "sine"),
            "reflexao": lambda: self._tone(880, 0.2, 0.2, "sine"),
            "rewind": lambda: self._tone(330, 0.3, 0.25, "saw", decay=1.5),
            "hit": lambda: self._tone(220, 0.1, 0.3, "square", decay=2),
            "enemy_hit": lambda: self._tone(180, 0.12, 0.25, "saw", decay=2),
            "enemy_die": lambda: self._tone(120, 0.25, 0.3, "noise", decay=1),
            "player_hit": lambda: self._tone(100, 0.2, 0.35, "square", decay=1.5),
            "skill_unlock": lambda: self._tone(523, 0.15, 0.2, "sine"),
            "wave_start": lambda: self._tone(440, 0.2, 0.2, "sine"),
            "wave_complete": lambda: self._tone(660, 0.3, 0.25, "sine"),
            "boss_phase": lambda: self._tone(150, 0.4, 0.3, "saw", decay=1),
            "projectile": lambda: self._tone(800, 0.05, 0.1, "sine"),
            "reflect": lambda: self._tone(1000, 0.1, 0.2, "sine"),
            "menu_select": lambda: self._tone(500, 0.08, 0.15, "sine"),
            "menu_confirm": lambda: self._tone(600, 0.1, 0.2, "sine"),
            "game_over": lambda: self._tone(200, 0.5, 0.3, "saw", decay=0.8),
            "victory": lambda: self._tone(523, 0.3, 0.3, "sine"),
        }
        if name in sounds:
            snd = sounds[name]()
            if snd:
                snd.play()

    def play_combo(self, names, delay=0.05):
        for i, name in enumerate(names):
            pygame.time.set_timer(pygame.USEREVENT + i, int(delay * 1000))
            self.play(name)
