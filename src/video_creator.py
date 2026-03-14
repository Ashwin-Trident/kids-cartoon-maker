import os
import numpy as np
from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeAudioClip,
    CompositeVideoClip, TextClip, concatenate_videoclips, concatenate_audioclips
)

# -------------------------------------------------
# GLOBAL SETTINGS
# -------------------------------------------------
FPS = 30
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920


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
                      scene_text, min_duration=3.0, music_volume=0.15, fps=FPS):

    speech_duration = _get_audio_duration(audio_path)
    clip_duration = max(speech_duration + 0.5, min_duration)

    # Image with Ken Burns zoom effect
    video = (
        ImageClip(image_path)
        .resize(height=VIDEO_HEIGHT)
        .set_duration(clip_duration)
        .set_fps(fps)
        .resize(lambda t: 1 + 0.04 * t)  # zoom animation
        .set_position("center")
    )

    try:
        txt = TextClip(
            scene_text,
            fontsize=70,
            font="DejaVu-Sans-Bold",
            color="white",
            stroke_color="black",
            stroke_width=4,
            method="caption",
            align="center",
            size=(VIDEO_WIDTH - 120, None)
        )

        txt = txt.set_duration(clip_duration).set_position(("center", VIDEO_HEIGHT - 400))

        video = CompositeVideoClip([video, txt])

    except Exception:
        pass

    try:
        mixed_audio, _ = _mix_audio(audio_path, music_path, music_start, music_volume)

        if clip_duration > speech_duration:
            silence_dur = clip_duration - speech_duration

            silence = (
                AudioFileClip(music_path)
                .subclip(
                    music_start + speech_duration,
                    music_start + speech_duration + silence_dur
                )
                .volumex(music_volume)
            )

            mixed_audio = concatenate_audioclips([mixed_audio, silence])

        video = video.set_audio(mixed_audio)

    except Exception:
        video = video.set_audio(AudioFileClip(audio_path))

    return video, clip_duration


def create_title_card(title, duration=3.0, fps=FPS):

    frame = np.zeros((VIDEO_HEIGHT, VIDEO_WIDTH, 3), dtype=np.uint8)

    for y in range(VIDEO_HEIGHT):
        t = y / VIDEO_HEIGHT
        frame[y, :] = [
            int(255 * (0.3 + 0.4 * t)),
            int(255 * (0.6 - 0.3 * t)),
            int(255 * (0.9 - 0.5 * t))
        ]

    bg = ImageClip(frame, duration=duration).set_fps(fps)

    try:

        title_txt = TextClip(
            title,
            fontsize=110,
            font="DejaVu-Sans-Bold",
            color="white",
            stroke_color="#FFD700",
            stroke_width=5,
            method="label"
        ).set_duration(duration).set_position("center")

        sub_txt = TextClip(
            "Kids Cartoon Maker",
            fontsize=50,
            font="DejaVu-Sans",
            color="#FFD700",
            method="label"
        ).set_duration(duration).set_position(("center", VIDEO_HEIGHT * 0.65))

        return CompositeVideoClip([bg, title_txt, sub_txt])

    except Exception:
        return bg


def assemble_video(
        scenes,
        image_files,
        audio_files,
        music_path,
        output_path,
        rhyme_title="Kids Cartoon",
        rhyme_name="custom",
        music_volume=0.18,
        fps=FPS,
        min_scene_duration=3.5
):

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"\n🎬 Assembling: {rhyme_title}")

    clips = []

    clips.append(create_title_card(rhyme_title, duration=3.0, fps=fps))

    music_offset = 3.0

    for i, (scene, img, aud) in enumerate(zip(scenes, image_files, audio_files)):

        print(f"  📽️ Scene {i+1}/{len(scenes)}: \"{scene.text[:35]}\"")

        clip, dur = create_scene_clip(
            img,
            aud,
            music_path,
            music_offset,
            scene.text,
            min_scene_duration,
            music_volume,
            fps
        )

        clips.append(clip)

        music_offset += dur

    clips.append(create_title_card("The End! 🌟", duration=3.0, fps=fps))

    print("  🔧 Concatenating clips...")
    final = concatenate_videoclips(clips, method="compose")

    print(f"  💾 Exporting video: {output_path}")

    final.write_videofile(
        output_path,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="/tmp/temp_audio.m4a",
        remove_temp=True,
        verbose=False,
        logger=None
    )

    for c in clips:
        c.close()

    final.close()

    print(f"✅ Done: {output_path}")

    return output_path
