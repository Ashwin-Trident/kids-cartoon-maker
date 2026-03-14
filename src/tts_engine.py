import os
from gtts import gTTS

OUTPUT = "temp_audio"


def generate_voice(scenes):

    os.makedirs(OUTPUT, exist_ok=True)

    audio_files = []

    for i, scene in enumerate(scenes):

        tts = gTTS(scene.text)

        path = f"{OUTPUT}/voice_{i}.mp3"

        tts.save(path)

        audio_files.append(path)

    return audio_files
