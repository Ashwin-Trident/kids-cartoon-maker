import asyncio
import os
import edge_tts

KIDS_VOICES = {
    "friendly_girl": "en-US-AriaNeural",
    "friendly_boy":  "en-US-GuyNeural",
    "uk_girl":       "en-GB-SoniaNeural",
    "uk_boy":        "en-GB-RyanNeural",
    "cheerful":      "en-US-JennyNeural",
    "animated":      "en-AU-NatashaNeural",
}

DEFAULT_VOICE = "en-GB-SoniaNeural"
DEFAULT_RATE  = "+10%"
DEFAULT_PITCH = "+5Hz"


async def _synthesize(text, output_path, voice, rate, pitch):
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(output_path)


def text_to_speech(text, output_path, voice=DEFAULT_VOICE, rate=DEFAULT_RATE, pitch=DEFAULT_PITCH):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    asyncio.run(_synthesize(text, output_path, voice, rate, pitch))
    return output_path


def generate_scene_audio(scenes, output_dir, voice=DEFAULT_VOICE, rate=DEFAULT_RATE, pitch=DEFAULT_PITCH):
    os.makedirs(output_dir, exist_ok=True)
    audio_files = []
    for i, scene in enumerate(scenes):
        output_path = os.path.join(output_dir, f"scene_{i:03d}.mp3")
        print(f"  🎤 Voice scene {i+1}/{len(scenes)}: \"{scene.text[:40]}\"")
        text_to_speech(scene.text, output_path, voice, rate, pitch)
        audio_files.append(output_path)
    return audio_files
