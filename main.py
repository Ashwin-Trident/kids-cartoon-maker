import os
from src.rhyme_generator import generate_story
from src.image_generator import generate_images
from src.tts_engine import generate_voice
from src.music_generator import generate_music
from src.video_creator import assemble_video

OUTPUT_DIR = "output"


def main():

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Generating story...")
    scenes = generate_story()

    print("Generating images...")
    image_files = generate_images(scenes)

    print("Generating voice...")
    audio_files = generate_voice(scenes)

    print("Generating music...")
    music_path = generate_music()

    output_video = os.path.join(OUTPUT_DIR, "cartoon.mp4")

    assemble_video(
        scenes,
        image_files,
        audio_files,
        music_path,
        output_video,
        rhyme_title="Funny Cartoon Story"
    )

    print("Video created:", output_video)


if __name__ == "__main__":
    main()
