"""
music_generator.py — Procedural copyright-free background music for Kids Cartoon Maker.

Generates gentle, child-friendly background music using pure Python (numpy + pydub).
No external music files needed. 100% royalty-free since it's generated from scratch.

Musical style: Pentatonic scale melodies with soft percussion,
               similar to gentle toy piano or music box sounds.
"""

import numpy as np
import os
from pydub import AudioSegment
from pydub.generators import Sine
from typing import Optional


# ─────────────────────────────────────────────
# MUSICAL CONSTANTS
# ─────────────────────────────────────────────

SAMPLE_RATE = 44100

# Pentatonic major scale frequencies (C4 pentatonic: C D E G A)
# Great for kids music — always sounds happy and harmonious!
PENTATONIC_C4 = [261.63, 293.66, 329.63, 392.00, 440.00]  # C D E G A
PENTATONIC_C5 = [523.25, 587.33, 659.25, 784.00, 880.00]  # C5 D5 E5 G5 A5
PENTATONIC_C3 = [130.81, 146.83, 164.81, 196.00, 220.00]  # C3 bass notes

# Simple chord progressions (frequency ratios for harmony)
CHORD_I  = [1.0, 1.25, 1.5]   # Major chord
CHORD_V  = [1.5, 1.875, 2.25] # Dominant
CHORD_VI = [1.667, 2.0, 2.5]  # Relative minor (still pretty)

THEMES = {
    "playful":    {"tempo": 120, "base_note": 261.63, "scale": PENTATONIC_C4},
    "dreamy":     {"tempo": 80,  "base_note": 220.00, "scale": PENTATONIC_C3},
    "adventure":  {"tempo": 140, "base_note": 293.66, "scale": PENTATONIC_C4},
    "lullaby":    {"tempo": 60,  "base_note": 196.00, "scale": PENTATONIC_C3},
}


# ─────────────────────────────────────────────
# SYNTHESIS FUNCTIONS
# ─────────────────────────────────────────────

def _sine_wave(freq: float, duration_ms: int, volume_db: float = -20.0) -> AudioSegment:
    """Generate a sine wave tone."""
    tone = Sine(freq).to_audio_segment(duration=duration_ms)
    return tone + volume_db


def _soft_tone(freq: float, duration_ms: int, volume_db: float = -22.0) -> AudioSegment:
    """Generate a soft tone with attack and decay envelope (like a toy piano)."""
    samples = int(SAMPLE_RATE * duration_ms / 1000)
    t = np.linspace(0, duration_ms / 1000, samples, endpoint=False)

    # Mix sine + slight harmonics for warmth
    wave = (
        np.sin(2 * np.pi * freq * t) * 0.6
        + np.sin(2 * np.pi * freq * 2 * t) * 0.25
        + np.sin(2 * np.pi * freq * 3 * t) * 0.1
        + np.sin(2 * np.pi * freq * 4 * t) * 0.05
    )

    # Envelope: quick attack, exponential decay
    attack_samples = min(int(0.02 * SAMPLE_RATE), samples // 4)
    decay = np.exp(-3 * t / (duration_ms / 1000))
    attack = np.minimum(np.linspace(0, 1, attack_samples), 1.0)
    envelope = decay.copy()
    envelope[:attack_samples] *= attack / decay[:attack_samples].clip(min=1e-6)
    wave *= envelope

    # Convert to 16-bit PCM
    wave = (wave * 32767 * 0.7).astype(np.int16)
    audio = AudioSegment(
        wave.tobytes(),
        frame_rate=SAMPLE_RATE,
        sample_width=2,
        channels=1,
    )
    return audio + volume_db


def _percussion_kick(volume_db: float = -25.0) -> AudioSegment:
    """Simple kick drum using frequency sweep."""
    duration_ms = 150
    samples = int(SAMPLE_RATE * duration_ms / 1000)
    t = np.linspace(0, duration_ms / 1000, samples, endpoint=False)
    freq_sweep = 80 * np.exp(-20 * t) + 40
    wave = np.sin(2 * np.pi * np.cumsum(freq_sweep) / SAMPLE_RATE)
    envelope = np.exp(-15 * t)
    wave = (wave * envelope * 32767 * 0.5).astype(np.int16)
    audio = AudioSegment(wave.tobytes(), frame_rate=SAMPLE_RATE, sample_width=2, channels=1)
    return audio + volume_db


def _percussion_hi_hat(volume_db: float = -28.0) -> AudioSegment:
    """Simple hi-hat using filtered noise."""
    duration_ms = 80
    samples = int(SAMPLE_RATE * duration_ms / 1000)
    t = np.linspace(0, duration_ms / 1000, samples, endpoint=False)
    noise = np.random.randn(samples)
    # High-pass filter approximation
    for i in range(1, len(noise)):
        noise[i] = noise[i] - 0.95 * noise[i - 1]
    envelope = np.exp(-30 * t)
    wave = (noise * envelope * 32767 * 0.3).astype(np.int16)
    audio = AudioSegment(wave.tobytes(), frame_rate=SAMPLE_RATE, sample_width=2, channels=1)
    return audio + volume_db


# ─────────────────────────────────────────────
# MUSIC GENERATION
# ─────────────────────────────────────────────

def generate_melody_bar(scale: list, tempo_bpm: int, volume_db: float = -20.0) -> AudioSegment:
    """Generate one bar of random pentatonic melody."""
    beat_ms = int(60000 / tempo_bpm)
    note_durations = [beat_ms // 2, beat_ms // 2, beat_ms, beat_ms]  # Mix of half and full beats
    bar = AudioSegment.silent(duration=0)
    total_ms = beat_ms * 4  # One bar = 4 beats
    elapsed = 0

    while elapsed < total_ms:
        freq = np.random.choice(scale)
        dur = np.random.choice(note_durations)
        dur = min(dur, total_ms - elapsed)
        if dur <= 0:
            break
        note = _soft_tone(float(freq), int(dur), volume_db)
        bar += note
        elapsed += int(dur)

    return bar


def generate_bass_bar(scale: list, tempo_bpm: int, volume_db: float = -25.0) -> AudioSegment:
    """Generate simple bass line (root + fifth pattern)."""
    beat_ms = int(60000 / tempo_bpm)
    bar = AudioSegment.silent(duration=0)
    bass_scale = [f / 2 for f in scale]  # One octave down

    for _ in range(4):
        freq = np.random.choice(bass_scale[:3])  # Only low notes for bass
        note = _soft_tone(float(freq), beat_ms, volume_db)
        bar += note

    return bar


def generate_percussion_bar(tempo_bpm: int) -> AudioSegment:
    """Generate one bar of simple percussion."""
    beat_ms = int(60000 / tempo_bpm)
    bar = AudioSegment.silent(duration=beat_ms * 4)

    # Kick on beats 1 and 3
    kick = _percussion_kick()
    bar = bar.overlay(kick, position=0)
    bar = bar.overlay(kick, position=beat_ms * 2)

    # Hi-hat on every beat
    hihat = _percussion_hi_hat()
    for b in range(4):
        bar = bar.overlay(hihat, position=beat_ms * b)
    # Extra hi-hat on offbeats
    for b in range(4):
        bar = bar.overlay(hihat, position=int(beat_ms * (b + 0.5)))

    return bar


def generate_music(
    duration_seconds: float,
    theme: str = "playful",
    output_path: Optional[str] = None,
    fade_in_ms: int = 1000,
    fade_out_ms: int = 2000,
) -> AudioSegment:
    """
    Generate procedural kids background music.
    
    Args:
        duration_seconds: How long the music should be
        theme: One of 'playful', 'dreamy', 'adventure', 'lullaby'
        output_path: If given, save to this MP3 path
        fade_in_ms: Fade in duration
        fade_out_ms: Fade out duration
    
    Returns:
        AudioSegment of the generated music
    """
    config = THEMES.get(theme, THEMES["playful"])
    tempo = config["tempo"]
    scale = config["scale"]

    beat_ms = int(60000 / tempo)
    bar_ms = beat_ms * 4
    total_ms = int(duration_seconds * 1000)

    print(f"  🎵 Generating {theme} background music ({duration_seconds:.1f}s, {tempo}bpm)...")

    music = AudioSegment.silent(duration=0)

    while len(music) < total_ms:
        melody = generate_melody_bar(scale, tempo, volume_db=-18.0)
        bass   = generate_bass_bar(scale, tempo, volume_db=-26.0)
        perc   = generate_percussion_bar(tempo)

        # Mix layers
        bar_len = min(len(melody), len(bass), len(perc), bar_ms)
        bar = AudioSegment.silent(duration=bar_len)
        bar = bar.overlay(melody[:bar_len])
        bar = bar.overlay(bass[:bar_len])
        bar = bar.overlay(perc[:bar_len])

        music += bar

    # Trim to exact length
    music = music[:total_ms]

    # Add fade in/out
    music = music.fade_in(min(fade_in_ms, total_ms // 4))
    music = music.fade_out(min(fade_out_ms, total_ms // 4))

    # Save if path given
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        music.export(output_path, format="mp3", bitrate="128k")
        print(f"  ✅ Music saved: {output_path}")

    return music


def generate_music_for_video(
    total_duration_seconds: float,
    output_path: str,
    theme: str = "playful",
) -> str:
    """
    Convenience function: generate music matching a video duration.
    Returns the path to the saved music file.
    """
    # Add a little extra length so fade-out doesn't cut off
    generate_music(
        duration_seconds=total_duration_seconds + 2,
        theme=theme,
        output_path=output_path,
    )
    return output_path
