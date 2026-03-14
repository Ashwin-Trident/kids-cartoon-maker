"""
video_creator.py — YouTube Shorts video assembly (1080x1920, 9:16 vertical).
Uses the animator module to create fully animated scenes.
"""

import os
import numpy as np
from moviepy.editor import (
    VideoClip, AudioFileClip, CompositeAudioClip,
    concatenate_videoclips, concatenate_audioclips, ImageClip
)
from src.animator import make_frame, W, H


FPS = 30


def _get_audio_duration(audio_path):
    clip = AudioFileClip(audio_path)
    dur = clip.duration
    clip.close()
    return dur


def _mix_audio(speech_path, music_path, music_start, music_volume=0.18):
    speech = AudioFileClip(speech_path)
    duration = speech.duration
    try:
        music = AudioFileClip(music_path).subclip(
            music_start, music_start + duration
        ).volumex(music_volume)
        mixed = CompositeAudioClip([speech, music])
    except Exception:
        mixed = speech
    return mixed, duration


def make_scene_clip(rhyme_name, scene_text, scene_index,
                    audio_path, music_path, music_start,
                    min_duration=3.5, music_volume=0.18):
    """Create a fully animated scene clip."""
    speech_dur = _get_audio_duration(audio_path)
    clip_dur   = max(speech_dur + 0.8, min_duration)

    # Animated video using make_frame from animator
    def frame_func(t):
        return make_frame(t, rhyme_name, scene_text, scene_index,
                          is_title=False)

    video = VideoClip(frame_func, duration=clip_dur).set_fps(FPS)

    # Audio mix
    try:
        mixed, _ = _mix_audio(audio_path, music_path, music_start, music_volume)
        if clip_dur > speech_dur:
            silence_dur = clip_dur - speech_dur
            try:
                tail = AudioFileClip(music_path).subclip(
                    music_start + speech_dur,
                    music_start + speech_dur + silence_dur
                ).volumex(music_volume)
                mixed = concatenate_audioclips([mixed, tail])
            except Exception:
                pass
        video = video.set_audio(mixed)
    except Exception:
        video = video.set_audio(AudioFileClip(audio_path))

    return video, clip_dur


def make_title_clip(title, rhyme_name, duration=3.0):
    """Create an animated title card."""
    def frame_func(t):
        return make_frame(t, rhyme_name, "", 0, is_title=True, title=title)
    return VideoClip(frame_func, duration=duration).set_fps(FPS)


def assemble_video(scenes, image_files, audio_files, music_path, output_path,
                   rhyme_title="Kids Cartoon", rhyme_name="custom",
                   music_volume=0.18, fps=FPS, min_scene_duration=3.5):
    """
    Assemble all animated scenes into a YouTube Shorts MP4 (1080x1920).
    image_files is kept for API compatibility but not used — animation is procedural.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"\n🎬 Assembling Shorts: {rhyme_title}  [{W}x{H}]")

    clips = []

    # Intro title card (3s)
    print("  🎬 Intro title card...")
    clips.append(make_title_clip(rhyme_title, rhyme_name, duration=3.0))

    # Scene clips
    music_offset = 3.0
    for i, (scene, aud) in enumerate(zip(scenes, audio_files)):
        print(f"  📽️  Scene {i+1}/{len(scenes)}: \"{scene.text[:40]}\"")
        clip, dur = make_scene_clip(
            rhyme_name=rhyme_name,
            scene_text=scene.text,
            scene_index=i,
            audio_path=aud,
            music_path=music_path,
            music_start=music_offset,
            min_duration=min_scene_duration,
            music_volume=music_volume,
        )
        clips.append(clip)
        music_offset += dur

    # Outro (2.5s)
    print("  🎬 Outro card...")
    clips.append(make_title_clip("Subscribe! 🌟", rhyme_name, duration=2.5))

    # Concatenate & export
    print("  🔧 Concatenating...")
    final = concatenate_videoclips(clips, method="compose")

    print(f"  💾 Exporting {W}x{H} Shorts video...")
    final.write_videofile(
        output_path,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="/tmp/temp_audio.m4a",
        remove_temp=True,
        verbose=False,
        logger=None,
        threads=2,
    )

    for c in clips:
        c.close()
    final.close()
    print(f"✅ Done: {output_path}")
    return output_path
