import math
import struct

import pygame


SAMPLE_RATE = 22050
AMPLITUDE = 32767


def _note_freq(semitone, octave=4):
    return 440.0 * (2 ** ((semitone - 9) / 12.0)) * (2 ** (octave - 4))


_SCALES = {
    "major":           [0, 2, 4, 5, 7, 9, 11],
    "minor":           [0, 2, 3, 5, 7, 8, 10],
    "phrygian":        [0, 1, 3, 5, 7, 8, 10],
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "pentatonic_major": [0, 2, 4, 7, 9],
    "dorian":          [0, 2, 3, 5, 7, 9, 10],
    "lydian":          [0, 2, 4, 6, 7, 9, 11],
    "locrian":         [0, 1, 3, 5, 6, 8, 10],
}

_WAVES = ["sine", "square", "saw", "triangle"]


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
    n_samples = int(SAMPLE_RATE * duration)
    left = [0.0] * n_samples
    right = [0.0] * n_samples

    for pan, layer_notes in patterns:
        for start_t, end_t, freq, wave in layer_notes:
            if freq <= 0:
                continue
            start_i = max(0, int(start_t * SAMPLE_RATE))
            end_i = min(n_samples, int(end_t * SAMPLE_RATE))
            length = end_t - start_t
            for i in range(start_i, end_i):
                t = i / SAMPLE_RATE
                local_t = t - start_t
                env = 1.0
                fade_dur = 0.008
                if local_t < fade_dur:
                    env = local_t / fade_dur
                elif length - local_t < fade_dur:
                    env = (length - local_t) / fade_dur
                val = _osc(freq * local_t, wave) * env
                lpan = min(1.0, 1.0 - pan) if pan >= 0 else 1.0
                rpan = min(1.0, 1.0 + pan) if pan <= 0 else 1.0
                left[i] += val * lpan
                right[i] += val * rpan

    max_val = max(max(abs(v) for v in left), max(abs(v) for v in right))
    scale = AMPLITUDE / max_val if max_val > 0 else 1.0
    headroom = 0.75
    scale *= headroom

    buf = bytearray()
    for i in range(n_samples):
        _write_sample(buf, left[i] * scale)
        _write_sample(buf, right[i] * scale)

    return pygame.mixer.Sound(buffer=bytes(buf))


def _arpeggio(scale, root_semitone, octave, beats, bpm, note_len, wave, vol, offset=0):
    notes = []
    beat_dur = 60.0 / bpm
    t = 0.0
    scale_len = len(scale)
    dir_up = True
    idx = offset % (scale_len * 2)
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


def _bass_line(root_semitone, octave, bpm, pattern, note_len, wave, vol):
    notes = []
    beat_dur = 60.0 / bpm
    t = 0.0
    for interval, dur_beats in pattern:
        freq = _note_freq(root_semitone + interval, octave)
        notes.append((t, t + dur_beats * beat_dur * note_len, freq * vol, wave))
        t += dur_beats * beat_dur
    return notes


def _xor_shift(x):
    x ^= (x << 13) & 0xFFFFFFFF
    x ^= (x >> 17)
    x ^= (x << 5) & 0xFFFFFFFF
    return x & 0xFFFFFFFF


def _rand(seed):
    s = _xor_shift(seed)
    return s / 0xFFFFFFFF


def _choice(seed, seq):
    return seq[int(_rand(seed) * len(seq)) % len(seq)]


def _rand_int(seed, lo, hi):
    return lo + int(_rand(seed) * (hi - lo + 1))


ROOT_NOTES = {
    "menu": 0,       # C
    "map": 2,        # D
    "game_over": 9,  # A
}


def generate_room_track(seed):
    """Generate a unique music track for a room based on its seed (col, row)."""
    duration_beats = 16.0
    bpm = 65 + int(_rand(seed + 1) * 55)
    duration = duration_beats * 60.0 / bpm

    root = int(_rand(seed + 2) * 12)
    scale_names = list(_SCALES.keys())
    scale_name = _choice(seed + 3, scale_names)
    scale = _SCALES[scale_name]

    arp_wave = _choice(seed + 4, _WAVES)
    arp_oct = _rand_int(seed + 5, 3, 5)
    arp_vol = 0.20 + _rand(seed + 6) * 0.20
    arp_pan = -0.4 + _rand(seed + 7) * 0.8
    arp_offset = int(_rand(seed + 8) * len(scale) * 2)

    pad_wave = _choice(seed + 9, ["sine", "triangle"])
    pad_oct = _rand_int(seed + 10, 3, 4)
    pad_vol = 0.10 + _rand(seed + 11) * 0.12
    pad_pan = -0.3 + _rand(seed + 12) * 0.6

    pad2_wave = _choice(seed + 13, ["sine", "triangle"])
    pad2_oct = _rand_int(seed + 14, 4, 5)
    pad2_vol = 0.08 + _rand(seed + 15) * 0.10
    pad2_pan = -0.4 + _rand(seed + 16) * 0.8

    bass_wave = _choice(seed + 17, ["square", "saw"])
    bass_oct = _rand_int(seed + 18, 1, 2)
    bass_vol = 0.18 + _rand(seed + 19) * 0.20

    bass_patterns = [
        [(0, 2), (7, 1), (0, 1), (3, 2), (0, 1), (7, 1)],
        [(0, 1), (0, 1), (7, 1), (0, 1), (3, 1), (3, 1), (0, 1), (7, 1)],
        [(0, 2), (3, 1), (0, 1), (5, 2), (3, 1), (0, 1)],
        [(0, 0.5), (1, 0.5), (0, 0.5), (1, 0.5), (0, 0.5), (3, 0.5), (0, 0.5), (3, 0.5)],
        [(0, 1.5), (7, 0.5), (0, 1), (10, 1), (7, 0.5), (5, 0.5), (3, 1), (0, 1)],
        [(0, 2), (10, 1), (7, 1), (5, 2), (3, 1), (0, 1)],
    ]
    bass_pat = _choice(seed + 20, bass_patterns)
    bass_note_len = 0.75 + _rand(seed + 21) * 0.20

    arp = _arpeggio(scale, root, arp_oct, int(duration_beats / (60.0 / bpm)), bpm, 0.4, arp_wave, arp_vol, offset=arp_offset)
    pad = _bass_line(root, pad_oct, bpm, [(0, duration_beats)], 0.97, pad_wave, pad_vol)
    pad2_int = _choice(seed + 22, [4, 5, 7, 8, 10, 11])
    pad2 = _bass_line(root + pad2_int, pad2_oct, bpm, [(0, duration_beats)], 0.97, pad2_wave, pad2_vol)
    bass = _bass_line(root, bass_oct, bpm, bass_pat, bass_note_len, bass_wave, bass_vol)

    return _generate_track(
        [(arp_pan, arp), (pad_pan, pad), (pad2_pan, pad2), (0.0, bass)],
        duration=duration,
    )


def generate_fixed_track(ref_name):
    """Generate a non-room track (menu, map, game_over) deterministically."""
    if ref_name == "victory":
        bpm = 100
        root = 0
        scale = _SCALES["pentatonic_major"]
        notes = []
        beat_dur = 60.0 / bpm
        for i, interval in enumerate(scale * 2):
            freq = _note_freq(root + interval, 4 + i // len(scale))
            t = i * beat_dur * 0.6
            notes.append((t, t + beat_dur * 0.55, freq * 0.35, "sine"))
        final_t = len(scale) * 2 * beat_dur * 0.6
        for interval in scale:
            freq = _note_freq(root + interval, 5)
            notes.append((final_t, final_t + 1.5, freq * 0.22, "triangle"))
        duration = final_t + 1.8
        bass = []
        for i in range(4):
            bass.append((i * 2 * beat_dur, (i * 2 + 1.8) * beat_dur, _note_freq(root, 2 + i // 2) * 0.28, "sine"))
        return _generate_track([(0.0, notes), (0.0, bass)], duration=duration)

    elif ref_name == "game_over":
        bpm = 50
        root = ROOT_NOTES["game_over"]
        scale = _SCALES["minor"]
        duration_beats = 8.0
        duration = duration_beats * 60.0 / bpm
        notes = []
        beat_dur = 60.0 / bpm
        for i, interval in enumerate(reversed(scale * 2)):
            freq = _note_freq(root + interval, 3 + (len(scale) * 2 - i) // len(scale))
            t = i * beat_dur * 0.8
            notes.append((t, t + beat_dur * 0.7, freq * 0.30, "sine"))
        pad = _bass_line(root, 3, bpm, [(0, duration_beats)], 0.97, "sine", 0.15)
        bass = _bass_line(root, 2, bpm, [(0, 2), (7, 1), (5, 1), (3, 2), (0, 2)], 0.80, "triangle", 0.20)
        return _generate_track([(0.0, notes), (0.0, pad), (0.0, bass)], duration=duration)

    else:
        seed = abs(hash(ref_name)) % 100000
        return generate_room_track(seed + 1000)


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


class FixedTrack(MusicTrack):
    def __init__(self, ref_name):
        super().__init__(ref_name)
        self.ref_name = ref_name

    def generate(self):
        self.sound = generate_fixed_track(self.ref_name)


class RoomTrack(MusicTrack):
    def __init__(self, room_key):
        super().__init__(room_key)
        self.room_key = room_key

    def generate(self):
        seed = abs(hash(self.room_key)) % 100000
        self.sound = generate_room_track(seed)


class MusicManager:
    def __init__(self):
        self.enabled = True
        self.volume = 0.35
        self.tracks = {}
        self.current_key = None

        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=1024)
            except Exception:
                self.enabled = False

    def _get_or_create(self, key, factory):
        if key not in self.tracks:
            track = factory(key)
            track.generate()
            self.tracks[key] = track
        return self.tracks[key]

    def play_fixed(self, name, fade_ms=400):
        if not self.enabled:
            return
        key = "fixed:" + name
        if key == self.current_key:
            return
        self._stop_current(fade_ms)
        track = self._get_or_create(key, lambda k: FixedTrack(k.split(":", 1)[1]))
        track.play(volume=self.volume, loops=-1)
        self.current_key = key

    def play_room(self, col, row, fade_ms=400):
        if not self.enabled:
            return
        key = f"room:{col}:{row}"
        if key == self.current_key:
            return
        self._stop_current(fade_ms)
        track = self._get_or_create(key, lambda k: RoomTrack(k))
        track.play(volume=self.volume, loops=-1)
        self.current_key = key

    def _stop_current(self, fade_ms):
        if self.current_key and self.current_key in self.tracks:
            self.tracks[self.current_key].stop(fade_ms=fade_ms)

    def stop(self, fade_ms=400):
        self._stop_current(fade_ms)
        self.current_key = None

    def set_volume(self, vol):
        self.volume = max(0.0, min(1.0, vol))
        if self.current_key and self.current_key in self.tracks:
            snd = self.tracks[self.current_key].sound
            if snd:
                snd.set_volume(self.volume)
