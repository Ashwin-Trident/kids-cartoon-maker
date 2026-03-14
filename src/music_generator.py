import numpy as np
import os
from pydub import AudioSegment
from pydub.generators import Sine
from typing import Optional

SAMPLE_RATE = 44100

PENTATONIC_C4 = [261.63, 293.66, 329.63, 392.00, 440.00]
PENTATONIC_C3 = [130.81, 146.83, 164.81, 196.00, 220.00]

THEMES = {
    "playful":   {"tempo": 120, "scale": PENTATONIC_C4},
    "dreamy":    {"tempo": 80,  "scale": PENTATONIC_C3},
    "adventure": {"tempo": 140, "scale": PENTATONIC_C4},
    "lullaby":   {"tempo": 60,  "scale": PENTATONIC_C3},
}


def _soft_tone(freq, duration_ms, volume_db=-22.0):
    samples = int(SAMPLE_RATE * duration_ms / 1000)
    t = np.linspace(0, duration_ms/1000, samples, endpoint=False)
    wave = (np.sin(2*np.pi*freq*t)*0.6 + np.sin(2*np.pi*freq*2*t)*0.25
            + np.sin(2*np.pi*freq*3*t)*0.1 + np.sin(2*np.pi*freq*4*t)*0.05)
    attack_samples = min(int(0.02*SAMPLE_RATE), samples//4)
    decay = np.exp(-3*t/(duration_ms/1000))
    attack = np.minimum(np.linspace(0,1,attack_samples), 1.0)
    envelope = decay.copy()
    envelope[:attack_samples] *= attack / decay[:attack_samples].clip(min=1e-6)
    wave *= envelope
    wave = (wave * 32767 * 0.7).astype(np.int16)
    audio = AudioSegment(wave.tobytes(), frame_rate=SAMPLE_RATE, sample_width=2, channels=1)
    return audio + volume_db


def _percussion_kick(volume_db=-25.0):
    duration_ms = 150
    samples = int(SAMPLE_RATE * duration_ms / 1000)
    t = np.linspace(0, duration_ms/1000, samples, endpoint=False)
    freq_sweep = 80 * np.exp(-20*t) + 40
    wave = np.sin(2*np.pi*np.cumsum(freq_sweep)/SAMPLE_RATE)
    envelope = np.exp(-15*t)
    wave = (wave * envelope * 32767 * 0.5).astype(np.int16)
    audio = AudioSegment(wave.tobytes(), frame_rate=SAMPLE_RATE, sample_width=2, channels=1)
    return audio + volume_db


def _percussion_hihat(volume_db=-28.0):
    duration_ms = 80
    samples = int(SAMPLE_RATE * duration_ms / 1000)
    t = np.linspace(0, duration_ms/1000, samples, endpoint=False)
    noise = np.random.randn(samples)
    for i in range(1, len(noise)):
        noise[i] = noise[i] - 0.95*noise[i-1]
    envelope = np.exp(-30*t)
    wave = (noise * envelope * 32767 * 0.3).astype(np.int16)
    audio = AudioSegment(wave.tobytes(), frame_rate=SAMPLE_RATE, sample_width=2, channels=1)
    return audio + volume_db


def generate_bar(scale, tempo):
    beat_ms = int(60000 / tempo)
    durations = [beat_ms//2, beat_ms//2, beat_ms, beat_ms]
    bar = AudioSegment.silent(duration=0)
    total_ms = beat_ms * 4
    elapsed = 0
    while elapsed < total_ms:
        freq = float(np.random.choice(scale))
        dur = min(int(np.random.choice(durations)), total_ms - elapsed)
        if dur <= 0:
            break
        bar += _soft_tone(freq, dur, -18.0)
        elapsed += dur
    bass_scale = [f/2 for f in scale]
    bass = AudioSegment.silent(duration=0)
    for _ in range(4):
        freq = float(np.random.choice(bass_scale[:3]))
        bass += _soft_tone(freq, beat_ms, -26.0)
    perc = AudioSegment.silent(duration=beat_ms*4)
    kick = _percussion_kick()
    hihat = _percussion_hihat()
    perc = perc.overlay(kick, position=0).overlay(kick, position=beat_ms*2)
    for b in range(4):
        perc = perc.overlay(hihat, position=beat_ms*b)
        perc = perc.overlay(hihat, position=int(beat_ms*(b+0.5)))
    bar_len = min(len(bar), len(bass), len(perc), beat_ms*4)
    mixed = AudioSegment.silent(duration=bar_len)
    mixed = mixed.overlay(bar[:bar_len]).overlay(bass[:bar_len]).overlay(perc[:bar_len])
    return mixed


def generate_music(duration_seconds, theme="playful", output_path=None):
    config = THEMES.get(theme, THEMES["playful"])
    tempo = config["tempo"]
    scale = config["scale"]
    total_ms = int(duration_seconds * 1000)
    print(f"  🎵 Generating {theme} music ({duration_seconds:.1f}s)...")
    music = AudioSegment.silent(duration=0)
    while len(music) < total_ms:
        music += generate_bar(scale, tempo)
    music = music[:total_ms].fade_in(1000).fade_out(2000)
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        music.export(output_path, format="mp3", bitrate="128k")
    return music


def generate_music_for_video(total_duration_seconds, output_path, theme="playful"):
    generate_music(total_duration_seconds + 2, theme, output_path)
    return output_path
