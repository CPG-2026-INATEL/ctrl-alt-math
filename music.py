import math
import random
import struct

import pygame


SAMPLE_RATE = 22050
AMPLITUDE = 32767


def _note_freq(semitone, octave=4):
    return 440.0 * (2 ** ((semitone - 9) / 12.0)) * (2 ** (octave - 4))


_MAJOR = [0, 2, 4, 5, 7, 9, 11]
_MINOR = [0, 2, 3, 5, 7, 8, 10]
_PENTATONIC_MAJOR = [0, 2, 4, 7, 9]
_PENTATONIC_MINOR = [0, 3, 5, 7, 10]
_PHRYGIAN = [0, 1, 3, 5, 7, 8, 10]


def _osc(t, wave="sine"):
    t = t % 1.0
    if wave == "sine":
        return math.sin(2 * math.pi * t)
    elif wave == "square":
        return 1.0 if t < 0.5 else -1.0
    elif wave == "saw":
        return 2.0 * t - 1.0
    elif wave == "triangle":
        return 4.0 * abs(t - 0.5) - 1.0
    return 0.0


def _clip(v):
    return max(-AMPLITUDE, min(AMPLITUDE, int(v)))


def _write_sample(buf, val):
    buf.extend(struct.pack("<h", _clip(val)))


def _generate_track(patterns, duration=4.0):
    """patterns: list of (layer_volume, [(start_t, end_t, freq, wave), ...])"""
    n_samples = int(SAMPLE_RATE * duration)
    left = [0.0] * n_samples
    right = [0.0] * n_samples

    for pan, layer_notes in patterns:
        for start_t, end_t, freq, wave in layer_notes:
            if freq <= 0:
                continue
            start_i = max(0, int(start_t * SAMPLE_RATE))
            end_i = min(n_samples, int(end_t * SAMPLE_RATE))
            for i in range(start_i, end_i):
                t = i / SAMPLE_RATE
                env = 1.0
                fade_in = 0.02
                fade_out = 0.03
                local_t = t - start_t
                length = end_t - start_t
                if local_t < fade_in:
                    env = local_t / fade_in
                elif length - local_t < fade_out:
                    env = (length - local_t) / fade_out
                val = _osc(freq * t, wave) * env
                lpan = min(1.0, 1.0 - pan) if pan >= 0 else 1.0
                rpan = min(1.0, 1.0 + pan) if pan <= 0 else 1.0
                left[i] += val * lpan
                right[i] += val * rpan

    max_val = max(max(abs(v) for v in left), max(abs(v) for v in right))
    scale = AMPLITUDE / max_val * 0.7 if max_val > 0 else 1.0

    buf = bytearray()
    for i in range(n_samples):
        _write_sample(buf, left[i] * scale)
        _write_sample(buf, right[i] * scale)

    return pygame.mixer.Sound(buffer=bytes(buf))


def _arpeggio(scale, root_semitone, octave, beats, bpm, note_len, wave, vol, pan=0.0):
    """Generate an arpeggio pattern walking up and down the scale."""
    notes = []
    beat_dur = 60.0 / bpm
    t = 0.0
    scale_len = len(scale)
    dir_up = True
    idx = 0
    for b in range(beats):
        interval = scale[idx % scale_len]
        oct_off = idx // scale_len
        freq = _note_freq(root_semitone + interval, octave + oct_off)
        notes.append((t, t + note_len * beat_dur, freq * vol, wave))
        t += beat_dur
        if dir_up:
            idx += 1
            if idx >= scale_len * 2:
                dir_up = False
                idx = scale_len * 2 - 2
        else:
            idx -= 1
            if idx < 0:
                dir_up = True
                idx = 1
    return notes


def _bass_line(root_semitone, octave, bpm, pattern, note_len, wave, vol, pan=0.0):
    """pattern: list of (interval, beats_duration) pairs."""
    notes = []
    beat_dur = 60.0 / bpm
    t = 0.0
    for interval, dur_beats in pattern:
        freq = _note_freq(root_semitone + interval, octave)
        notes.append((t, t + dur_beats * beat_dur * note_len, freq * vol, wave))
        t += dur_beats * beat_dur
    return notes


def _hihat(bpm, beats, vol, pan=0.0):
    notes = []
    beat_dur = 60.0 / bpm
    t = 0.0
    for b in range(beats):
        # hi-hat on each 8th note
        notes.append((t, t + 0.04, 8000.0, "noise"))
        t += beat_dur * 0.5
    # scale volume
    return [(nt[0], nt[1], nt[2], nt[3]) for nt in notes]


def _kick(beats, bpm, vol, pan=0.0):
    notes = []
    beat_dur = 60.0 / bpm
    t = 0.0
    for b in range(beats):
        if b % 2 == 0:
            freq_sweep = 150.0 - 50.0 * (b % 4)
            notes.append((t, t + 0.12, freq_sweep, "sine"))
        t += beat_dur
    return notes


class MusicTrack:
    def __init__(self, name):
        self.name = name
        self.sound = None
        self.channel = None

    def generate(self):
        raise NotImplementedError

    def play(self, volume=0.4, loops=-1):
        if self.sound is None:
            self.generate()
        if self.sound is None:
            return
        self.sound.set_volume(volume)
        self.channel = self.sound.play(loops=loops)

    def stop(self, fade_ms=300):
        if self.channel:
            self.channel.fadeout(fade_ms)
            self.channel = None
        if self.sound:
            self.sound.fadeout(fade_ms)


class MenuMusic(MusicTrack):
    def __init__(self):
        super().__init__("menu")
        self._sample = None

    def generate(self):
        bpm = 72
        root = 0  # C
        scale = _PENTATONIC_MINOR
        notes = []
        duration_beats = 8.0
        duration = duration_beats * 60.0 / bpm

        arp1 = _arpeggio(scale, root, 3, int(duration_beats * 2), bpm, 0.5, "triangle", 0.35, 0.0)
        arp2 = _arpeggio(scale, root, 4, int(duration_beats * 2), bpm, 0.5, "sine", 0.22, -0.3)
        pad1 = _bass_line(root, 3, bpm, [(0, duration_beats)], 0.98, "sine", 0.20, 0.4)
        pad2 = _bass_line(root + 7, 4, bpm, [(0, duration_beats)], 0.98, "sine", 0.15, -0.4)
        bass = _bass_line(root, 2, bpm, [
            (0, 2), (7, 1), (0, 1),
            (3, 2), (0, 1), (7, 1),
        ], 0.85, "square", 0.25, 0.0)

        self.sound = _generate_track(
            [(0.0, arp1), (-0.3, arp2), (0.4, pad1), (-0.4, pad2), (0.0, bass)],
            duration=duration,
        )


class MapMusic(MusicTrack):
    def __init__(self):
        super().__init__("map")

    def generate(self):
        bpm = 80
        root = 2  # D
        scale = _PHRYGIAN
        notes = []
        duration_beats = 16.0
        duration = duration_beats * 60.0 / bpm

        arp = _arpeggio(scale, root, 3, int(duration_beats * 2), bpm, 0.4, "sine", 0.30, 0.0)
        pad1 = _bass_line(root, 3, bpm, [(0, duration_beats)], 0.97, "triangle", 0.18, 0.2)
        pad2 = _bass_line(root + 7, 4, bpm, [(0, duration_beats)], 0.97, "sine", 0.12, -0.3)
        bass = _bass_line(root, 2, bpm, [
            (0, 2), (1, 1), (0, 1), (3, 2), (1, 1), (0, 1),
        ], 0.80, "square", 0.22, 0.0)

        self.sound = _generate_track(
            [(0.0, arp), (0.2, pad1), (-0.3, pad2), (0.0, bass)],
            duration=duration,
        )


class CombatMusic(MusicTrack):
    def __init__(self):
        super().__init__("combat")

    def generate(self):
        bpm = 120
        root = 4  # E
        scale = _MINOR
        duration_beats = 16.0
        duration = duration_beats * 60.0 / bpm

        arp1 = _arpeggio(scale, root, 4, int(duration_beats * 4), bpm, 0.25, "square", 0.30, -0.2)
        arp2 = _arpeggio(scale, root, 5, int(duration_beats * 4), bpm, 0.25, "saw", 0.18, 0.2)
        pad = _bass_line(root, 3, bpm, [(0, duration_beats)], 0.97, "saw", 0.12, 0.0)
        bass = _bass_line(root, 2, bpm, [
            (0, 1), (0, 1), (7, 1), (0, 1),
            (3, 1), (3, 1), (0, 1), (7, 1),
        ], 0.75, "square", 0.28, 0.0)

        self.sound = _generate_track(
            [(-0.2, arp1), (0.2, arp2), (0.0, pad), (0.0, bass)],
            duration=duration,
        )


class BossMusic(MusicTrack):
    def __init__(self):
        super().__init__("boss")

    def generate(self):
        bpm = 140
        root = 6  # F#
        scale = _PHRYGIAN
        duration_beats = 16.0
        duration = duration_beats * 60.0 / bpm

        arp1 = _arpeggio(scale, root, 4, int(duration_beats * 4), bpm, 0.2, "square", 0.35, 0.0)
        arp2 = _arpeggio(scale, root, 5, int(duration_beats * 4), bpm, 0.2, "saw", 0.25, -0.2)
        pad = _bass_line(root, 3, bpm, [(0, duration_beats)], 0.97, "saw", 0.18, 0.0)
        bass = _bass_line(root, 1, bpm, [
            (0, 0.5), (1, 0.5), (0, 0.5), (1, 0.5),
            (0, 0.5), (3, 0.5), (0, 0.5), (3, 0.5),
        ] * 2, 0.65, "square", 0.35, 0.0)

        self.sound = _generate_track(
            [(0.0, arp1), (-0.2, arp2), (0.0, pad), (0.0, bass)],
            duration=duration,
        )


class VictoryMusic(MusicTrack):
    def __init__(self):
        super().__init__("victory")

    def generate(self):
        bpm = 100
        root = 0  # C
        scale = _PENTATONIC_MAJOR
        notes = []
        # ascending then held
        beat_dur = 60.0 / bpm
        for i, interval in enumerate(scale * 2):
            freq = _note_freq(root + interval, 4 + i // len(scale))
            t = i * beat_dur * 0.6
            notes.append((t, t + beat_dur * 0.55, freq * 0.35, "sine"))
        # final chord
        final_t = len(scale) * 2 * beat_dur * 0.6
        for interval in scale:
            freq = _note_freq(root + interval, 5)
            notes.append((final_t, final_t + 1.5, freq * 0.22, "triangle"))
        duration = final_t + 1.8

        bass = []
        for i in range(4):
            bass.append((i * 2 * beat_dur, (i * 2 + 1.8) * beat_dur, _note_freq(root, 2 + i // 2) * 0.28, "sine"))

        self.sound = _generate_track(
            [(0.0, notes), (0.0, bass)],
            duration=duration,
        )


class GameOverMusic(MusicTrack):
    def __init__(self):
        super().__init__("game_over")

    def generate(self):
        bpm = 50
        root = 9  # A
        scale = _MINOR
        duration_beats = 8.0
        duration = duration_beats * 60.0 / bpm

        notes = []
        beat_dur = 60.0 / bpm
        for i, interval in enumerate(reversed(scale * 2)):
            freq = _note_freq(root + interval, 3 + (len(scale) * 2 - i) // len(scale))
            t = i * beat_dur * 0.8
            notes.append((t, t + beat_dur * 0.7, freq * 0.30, "sine"))
        pad = _bass_line(root, 3, bpm, [(0, duration_beats)], 0.97, "sine", 0.15, 0.0)
        bass = _bass_line(root, 2, bpm, [
            (0, 2), (7, 1), (5, 1), (3, 2), (0, 2),
        ], 0.80, "triangle", 0.20, 0.0)

        self.sound = _generate_track(
            [(0.0, notes), (0.0, pad), (0.0, bass)],
            duration=duration,
        )


class MusicManager:
    def __init__(self):
        self.enabled = True
        self.volume = 0.35
        self.tracks = {}
        self.current_name = None

        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=1024)
            except Exception:
                self.enabled = False

    def _get_or_create(self, cls, name):
        if name not in self.tracks:
            track = cls()
            track.generate()
            self.tracks[name] = track
        return self.tracks[name]

    def play(self, name, fade_ms=400):
        if not self.enabled:
            return
        if self.current_name is not None and self.current_name in self.tracks:
            self.tracks[self.current_name].stop(fade_ms=fade_ms)

        track_map = {
            "menu": (MenuMusic, "menu"),
            "map": (MapMusic, "map"),
            "gameplay": (CombatMusic, "combat"),
            "combat": (CombatMusic, "combat"),
            "boss": (BossMusic, "boss"),
            "victory": (VictoryMusic, "victory"),
            "game_over": (GameOverMusic, "game_over"),
        }

        if name in track_map:
            cls, key = track_map[name]
            track = self._get_or_create(cls, key)
            track.play(volume=self.volume, loops=-1)
            self.current_name = name if name in track_map else key
        elif name not in track_map and name != "stop":
            return

    def stop(self, fade_ms=400):
        if self.current_name and self.current_name in self.tracks:
            self.tracks[self.current_name].stop(fade_ms=fade_ms)
        self.current_name = None

    def set_volume(self, vol):
        self.volume = max(0.0, min(1.0, vol))
        if self.current_name and self.current_name in self.tracks:
            snd = self.tracks[self.current_name].sound
            if snd:
                snd.set_volume(self.volume)
