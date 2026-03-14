"""
tts_engine.py — Free text-to-speech using Microsoft Edge TTS (no API key needed).
Uses edge-tts library which accesses the same engine as Microsoft Edge browser.

Voices are completely free and include child-friendly options.
"""

import asyncio
import os
import edge_tts
from pathlib import Path
from typing import Optional


# Child-friendly voices (all free via edge-tts)
KIDS_VOICES = {
    "friendly_girl": "en-US-AriaNeural",       # Warm, friendly female voice
    "friendly_boy":  "en-US-GuyNeural",         # Friendly male voice
    "uk_girl":       "en-GB-SoniaNeural",        # British female, great for nursery rhymes
    "uk_boy":        "en-GB-RyanNeural",         # British male
    "cheerful":      "en-US-JennyNeural",        # Cheerful, expressive
    "animated":      "en-AU-NatashaNeural",      # Australian, animated
}

DEFAULT_VOICE = "en-GB-SoniaNeural"   # Classic British voice for nursery rhymes
DEFAULT_RATE  = "+10%"                  # Slightly faster, more energetic for kids
DEFAULT_PITCH = "+5Hz"                  # Slightly higher pitch, child-friendly


async def _synthesize(text: str, output_path: str, voice: str, rate: str, pitch: str) -> None:
    """Internal async function to call edge-tts."""
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(output_path)


def text_to_speech(
    text: str,
    output_path: str,
    voice: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
    pitch: str = DEFAULT_PITCH,
) -> str:
    """
    Convert text to speech and save as MP3.
    
    Args:
        text: Text to speak
        output_path: Where to save the audio file (.mp3)
        voice: Edge TTS voice name (see KIDS_VOICES)
        rate: Speech rate adjustment e.g. "+10%", "-5%"
        pitch: Pitch adjustment e.g. "+5Hz", "-3Hz"
    
    Returns:
        Path to the generated audio file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    asyncio.run(_synthesize(text, output_path, voice, rate, pitch))
    return output_path


def generate_scene_audio(
    scenes: list,
    output_dir: str,
    voice: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
    pitch: str = DEFAULT_PITCH,
) -> list[str]:
    """
    Generate separate audio files for each scene.
    
    Args:
        scenes: List of RhymeScene objects
        output_dir: Directory to save audio files
        voice: TTS voice
        rate: Speech rate
        pitch: Pitch
    
    Returns:
        List of audio file paths
    """
    os.makedirs(output_dir, exist_ok=True)
    audio_files = []

    for i, scene in enumerate(scenes):
        output_path = os.path.join(output_dir, f"scene_{i:03d}.mp3")
        print(f"  🎤 Generating voice for scene {i+1}/{len(scenes)}: \"{scene.text[:40]}...\"")
        text_to_speech(scene.text, output_path, voice, rate, pitch)
        audio_files.append(output_path)

    return audio_files


def list_voices() -> dict:
    """Return all available child-friendly voices."""
    return KIDS_VOICES


async def _get_all_voices() -> list:
    """Fetch all available edge-tts voices."""
    return await edge_tts.list_voices()


def get_available_voices() -> list:
    """Return all available edge-tts voices."""
    return asyncio.run(_get_all_voices())
