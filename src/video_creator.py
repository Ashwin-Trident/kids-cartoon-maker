from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips


def assemble_video(
        scenes,
        image_files,
        audio_files,
        music_path,
        output_path,
        rhyme_title="Cartoon",
        fps=30):

    clips = []

    for img, audio in zip(image_files, audio_files):

        audio_clip = AudioFileClip(audio)

        clip = (
            ImageClip(img)
            .set_duration(audio_clip.duration)
            .resize(lambda t: 1 + 0.03 * t)
            .set_audio(audio_clip)
        )

        clips.append(clip)

    final = concatenate_videoclips(clips)

    final.write_videofile(
        output_path,
        fps=fps,
        codec="libx264",
        audio_codec="aac"
    )
