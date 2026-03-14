import os
import random
from datetime import datetime

from src.rhyme_generator import generate_story
from src.image_generator import generate_images
from src.tts_engine import generate_voice
from src.music_generator import generate_music
from src.video_creator import assemble_video
from src.youtube_uploader import upload_video


OUTPUT_DIR = "output"


def main():

    print("\n🎬 Kids Cartoon Generator Started\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # -------------------------------------------------
    # 1. Generate Story
    # -------------------------------------------------

    print("📖 Generating story...")

    scenes = generate_story()

    for i, scene in enumerate(scenes):
        print(f"  Scene {i+1}: {scene.text}")

    # -------------------------------------------------
    # 2. Generate Images
    # -------------------------------------------------

    print("\n🖼 Generating images...")

    image_files = generate_images(scenes)

    # -------------------------------------------------
    # 3. Generate Voice
    # -------------------------------------------------

    print("\n🎤 Generating voice...")

    audio_files = generate_voice(scenes)

    # -------------------------------------------------
    # 4. Generate Music
    # -------------------------------------------------

    print("\n🎵 Generating background music...")

    music_path = generate_music()

    # -------------------------------------------------
    # 5. Create Video
    # -------------------------------------------------

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_video = os.path.join(
        OUTPUT_DIR,
        f"cartoon_{timestamp}.mp4"
    )

    print("\n🎞 Creating video...")

    assemble_video(
        scenes,
        image_files,
        audio_files,
        music_path,
        output_video,
        rhyme_title="Funny Kids Cartoon"
    )

    print("\n✅ Video created:", output_video)

    # -------------------------------------------------
    # 6. Upload to YouTube
    # -------------------------------------------------

    try:

        print("\n📤 Uploading to YouTube...")

        title = random.choice([
            "Funny Kids Cartoon Adventure",
            "Kids Cartoon Story Time",
            "Fun Cartoon Story For Kids",
            "Kids Animation Short Story"
        ])

        video_url = upload_video(
            video_path=output_video,
            title=title
        )

        print("\n🎉 Upload successful!")
        print("🔗", video_url)

    except Exception as e:

        print("\n⚠️ Upload skipped:", e)

    print("\n🏁 Process Finished\n")


if __name__ == "__main__":
    main()
