"""
video_creator.py — Assembles cartoon images, voice-over, and music into an MP4 video.

Uses moviepy (free, open source) to:
  1. Create image clips from cartoon frames
  2. Add speech audio per scene
  3. Mix in background music (lower volume)
  4. Add subtitle text overlays
  5. Export final MP4

All free, all local, no cloud rendering needed.
"""

import os
import re
from pathlib import Path
from typing import List, Optional

from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    TextClip,
    concatenate_videoclips,
    concatenate_audioclips,
    AudioSegment,
)
from moviepy.audio.AudioClip import AudioArrayClip
import numpy as np


# ─────────────────────────────────────────────
# SUBTITLE STYLE
# ─────────────────────────────────────────────

SUBTITLE_STYLE = {
    "fontsize": 42,
    "font": "DejaVu-Sans-Bold",
    "color": "white",
    "stroke_color": "black",
    "stroke_width": 3,
    "method": "caption",
    "align": "center",
    "size": (700, None),
}


def _get_audio_duration(audio_path: str) -> float:
    """Get duration of an audio file in seconds."""
    clip = AudioFileClip(audio_path)
    duration = clip.duration
    clip.close()
    return duration


def _mix_audio(
    speech_path: str,
    music_path: str,
    speech_start: float,
    music_volume: float = 0.15,
) -> Optional[object]:
    """
    Mix a speech segment with background music.
    
    Args:
        speech_path: Path to the speech MP3
        music_path: Path to the background music MP3
        speech_start: When the speech starts in the music timeline (seconds)
        music_volume: Volume multiplier for music (0.0-1.0)
    
    Returns:
        Composite audio clip
    """
    speech = AudioFileClip(speech_path)
    duration = speech.duration

    # Slice the correct portion of the music
    try:
        music = AudioFileClip(music_path).subclip(speech_start, speech_start + duration)
        music = music.volumex(music_volume)
        mixed = CompositeAudioClip([speech, music])
    except Exception:
        # If music mixing fails, just use speech
        mixed = speech

    return mixed, duration


def create_scene_clip(
    image_path: str,
    audio_path: str,
    music_path: str,
    music_start: float,
    scene_text: str,
    min_duration: float = 3.0,
    music_volume: float = 0.15,
    fps: int = 24,
) -> object:
    """
    Create a single scene clip: image + voice + music + subtitle.
    
    Returns:
        A moviepy VideoClip
    """
    # Get speech duration and ensure minimum clip length
    speech_duration = _get_audio_duration(audio_path)
    clip_duration = max(speech_duration + 0.5, min_duration)

    # Image base clip
    video = ImageClip(image_path, duration=clip_duration)

    # Ken Burns zoom effect (slow zoom in — makes static images feel alive)
    zoom_end = 1.08
    video = video.resize(lambda t: 1 + (zoom_end - 1) * (t / clip_duration))
    video = video.set_position("center")
    video = video.set_fps(fps)

    # Subtitle text
    try:
        txt = TextClip(
            scene_text,
            **SUBTITLE_STYLE,
        ).set_duration(clip_duration).set_position(("center", "bottom"))
        # Add semi-transparent background behind text
        video = CompositeVideoClip([
            video,
            txt.margin(bottom=30, opacity=0),
        ])
    except Exception:
        # TextClip may fail if ImageMagick not installed — skip subtitles gracefully
        pass

    # Audio: mix speech + music
    try:
        mixed_audio, _ = _mix_audio(audio_path, music_path, music_start, music_volume)
        # Pad audio if clip is longer than speech
        if clip_duration > speech_duration:
            silence_dur = clip_duration - speech_duration
            silence = AudioFileClip(music_path).subclip(
                music_start + speech_duration,
                music_start + speech_duration + silence_dur,
            ).volumex(music_volume)
            mixed_audio = concatenate_audioclips([mixed_audio, silence])
        video = video.set_audio(mixed_audio)
    except Exception as e:
        print(f"    ⚠️  Audio mixing error (using speech only): {e}")
        video = video.set_audio(AudioFileClip(audio_path))

    return video, clip_duration


def create_title_card(
    title: str,
    duration: float = 3.0,
    fps: int = 24,
    width: int = 768,
    height: int = 512,
) -> object:
    """Create a colorful animated title card."""
    # Generate a colorful gradient background using numpy
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        t = y / height
        frame[y, :] = [
            int(255 * (0.3 + 0.4 * t)),   # R
            int(255 * (0.6 - 0.3 * t)),   # G  
            int(255 * (0.9 - 0.5 * t)),   # B
        ]

    bg = ImageClip(frame, duration=duration).set_fps(fps)

    try:
        title_txt = TextClip(
            title,
            fontsize=64,
            font="DejaVu-Sans-Bold",
            color="white",
            stroke_color="#FFD700",
            stroke_width=4,
            method="label",
        ).set_duration(duration).set_position("center")

        subtitle_txt = TextClip(
            "🌟 Kids Cartoon Maker 🌟",
            fontsize=28,
            font="DejaVu-Sans",
            color="#FFD700",
            method="label",
        ).set_duration(duration).set_position(("center", height * 0.65))

        return CompositeVideoClip([bg, title_txt, subtitle_txt])
    except Exception:
        return bg


def assemble_video(
    scenes: list,
    image_files: list[str],
    audio_files: list[str],
    music_path: str,
    output_path: str,
    rhyme_title: str = "Kids Cartoon",
    music_volume: float = 0.15,
    fps: int = 24,
    min_scene_duration: float = 3.0,
) -> str:
    """
    Assemble the final cartoon video from all components.
    
    Args:
        scenes: List of RhymeScene objects
        image_files: List of image file paths (one per scene)
        audio_files: List of audio file paths (one per scene)
        music_path: Path to background music
        output_path: Where to save the final MP4
        rhyme_title: Title of the rhyme (for title card)
        music_volume: Background music volume (0-1)
        fps: Frames per second
        min_scene_duration: Minimum seconds per scene
    
    Returns:
        Path to the output video
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"\n🎬 Assembling video: {rhyme_title}")
    print(f"   Scenes: {len(scenes)}")

    clips = []

    # Title card
    print("  📽️  Creating title card...")
    title_card = create_title_card(rhyme_title, duration=3.0, fps=fps)
    clips.append(title_card)

    # Build scene clips
    music_offset = 3.0  # Start music after title card
    for i, (scene, img, aud) in enumerate(zip(scenes, image_files, audio_files)):
        print(f"  📽️  Building scene {i+1}/{len(scenes)}: \"{scene.text[:35]}...\"")
        clip, dur = create_scene_clip(
            image_path=img,
            audio_path=aud,
            music_path=music_path,
            music_start=music_offset,
            scene_text=scene.text,
            min_duration=min_scene_duration,
            music_volume=music_volume,
            fps=fps,
        )
        clips.append(clip)
        music_offset += dur

    # End card
    end_card = create_title_card("The End! 🌟", duration=3.0, fps=fps)
    clips.append(end_card)

    # Concatenate all clips
    print("  🔧 Concatenating clips...")
    final = concatenate_videoclips(clips, method="compose")

    # Export
    print(f"  💾 Exporting to: {output_path}")
    final.write_videofile(
        output_path,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="/tmp/temp_audio.m4a",
        remove_temp=True,
        verbose=False,
        logger=None,
    )

    # Clean up
    for c in clips:
        c.close()
    final.close()

    print(f"\n✅ Video saved: {output_path}")
    return output_path
