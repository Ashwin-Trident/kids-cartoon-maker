import numpy as np
import soundfile as sf


def generate_music():

    sr = 22050

    duration = 30

    t = np.linspace(0, duration, sr * duration)

    music = 0.1 * np.sin(2 * np.pi * 220 * t)

    path = "temp_music.wav"

    sf.write(path, music, sr)

    return path
