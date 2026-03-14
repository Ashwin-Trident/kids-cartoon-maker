import os
import numpy as np
from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeAudioClip,
    CompositeVideoClip, TextClip, concatenate_videoclips, concatenate_audioclips
)


def _get_audio_duration(audio_path):
    clip = AudioFileClip(audio_path)
    dur = clip.duration
    clip.close()
    return dur


def _mix_audio(speech_path, music_path, music_start, music_volume=0.15):
    speech = AudioFileClip(speech_path)
    duration = speech.duration
    try:
        music = AudioFileClip(music_path).subclip(music_start, music_start + duration)
        music = music.volumex(music_volume)
        mixed = CompositeAudioClip([speech, music])
    except Exception:
        mixed = speech
    return mixed, duration


def create_scene_clip(image_path, audio_path, music_path, music_start,
                      scene_text, min_duration=3.0, music_volume=0.15, fps=24):
    speech_duration = _get_audio_duration(audio_path)
    clip_duration = max(speech_duration + 0.5, min_duration)
    video = ImageClip(image_path, duration=clip_duration)
    zoom_end = 1.08
    video = video.resize(lambda t: 1 + (zoom_end-1)*(t/clip_duration))
    video = video.set_position("center").set_fps(fps)
    try:
        txt = TextClip(scene_text, fontsize=42, font="DejaVu-Sans-Bold",
                       color="white", stroke_color="black", stroke_width=3,
                       method="caption", align="center", size=(700, None))
        txt = txt.set_duration(clip_duration).set_position(("center", "bottom"))
        video = CompositeVideoClip([video, txt.margin(bottom=30, opacity=0)])
    except Exception:
        pass
    try:
        mixed_audio, _ = _mix_audio(audio_path, music_path, music_start, music_volume)
        if clip_duration > speech_duration:
            silence_dur = clip_duration - speech_duration
            silence = AudioFileClip(music_path).subclip(
                music_start + speech_duration,
                music_start + speech_duration + silence_dur
            ).volumex(music_volume)
            mixed_audio = concatenate_audioclips([mixed_audio, silence])
        video = video.set_audio(mixed_audio)
    except Exception:
        video = video.set_audio(AudioFileClip(audio_path))
    return video, clip_duration


def create_title_card(title, duration=3.0, fps=24, width=768, height=512):
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        t = y / height
        frame[y, :] = [int(255*(0.3+0.4*t)), int(255*(0.6-0.3*t)), int(255*(0.9-0.5*t))]
    bg = ImageClip(frame, duration=duration).set_fps(fps)
    try:
        title_txt = TextClip(title, fontsize=64, font="DejaVu-Sans-Bold",
                             color="white", stroke_color="#FFD700", stroke_width=4,
                             method="label").set_duration(duration).set_position("center")
        sub_txt = TextClip("Kids Cartoon Maker", fontsize=28, font="DejaVu-Sans",
                           color="#FFD700", method="label").set_duration(duration)\
                           .set_position(("center", height*0.65))
        return CompositeVideoClip([bg, title_txt, sub_txt])
    except Exception:
        return bg


def assemble_video(scenes, imag
