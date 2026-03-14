import os
import asyncio
import edge_tts

VOICE = "en-US-AriaNeural"
OUTPUT_DIR = "temp_audio"


async def _generate(text, file_path):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(file_path)


def generate_voice(scenes):

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    audio_files = []

    for i, scene in enumerate(scenes):

        path = f"{OUTPUT_DIR}/voice_{i}.mp3"

        asyncio.run(_generate(scene.text, path))

        audio_files.append(path)

    return audio_files
