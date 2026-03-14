#!/usr/bin/env python3
import os
import sys
import click
import tempfile
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from src.rhyme_generator  import get_rhyme, get_random_rhyme, get_rhyme_from_text, list_rhymes
from src.tts_engine        import generate_scene_audio, KIDS_VOICES
from src.image_generator   import generate_scene_images
from src.music_generator   import generate_music_for_video
from src.video_creator     import assemble_video
from src.youtube_uploader  import upload_video, get_channel_info, revoke_credentials

OUTPUT_DIR   = Path(__file__).parent / "output"
MUSIC_THEMES = ["playful", "dreamy", "adventure", "lullaby"]
PRIVACY_OPTS = ["public", "unlisted", "private"]


@click.command()
@click.option("--rhyme",     "-r",  default=None)
@click.option("--random",    "use_random", is_flag=True)
@click.option("--text",      "-t",  default=None)
@click.option("--title",           default="My Rhyme")
@click.option("--list",      "show_list", is_flag=True)
@click.option("--voice",     default="uk_girl", type=click.Choice(list(KIDS_VOICES.keys())))
@click.option("--music",     "music_theme", default="playful", type=click.Choice(MUSIC_THEMES))
@click.option("--music-volume", default=0.15, type=float)
@click.option("--no-ai",     is_flag=True)
@click.option("--fps",       default=24, type=int)
@click.option("--output",    "-o", default=None)
@click.option("--upload",    is_flag=True)
@click.option("--privacy",   default="public", type=click.Choice(PRIVACY_OPTS))
@click.option("--yt-description", default=None)
@click.option("--yt-tags",        default=None)
@click.option("--yt-not-for-kids", is_flag=True)
@click.option("--yt-info",   is_flag=True)
@click.option("--yt-logout", is_flag=True)
def main(rhyme, use_random, text, title, show_list, voice, music_theme,
         music_volume, no_ai, fps, output, upload, privacy, yt_description,
         yt_tags, yt_not_for_kids, yt_info, yt_logout):
    """🎨 Kids Cartoon Maker — 100% free cartoon videos auto-uploaded to YouTube."""

    if yt_logout:
        revoke_credentials(); return

    if yt_info:
        try:
            info = get_channel_info()
            if info:
                click.echo(f"📺 {info['name']}  |  {info['url']}  |  {info['videos']} videos")
        except FileNotFoundError as e:
            click.echo(str(e))
        return

    if show_list:
        click.echo("\n📚 Available rhymes:\n")
        for name in list_rhymes():
            r = get_rhyme(name)
            click.echo(f"  • {name:12} — {r.title} ({len(r.scenes)} scenes)")
        return

    if text:
        selected = get_rhyme_from_text(text, title=title)
    elif use_random:
        selected = get_random_rhyme()
        click.echo(f"🎲 Random: {selected.title}")
    elif rhyme:
        selected = get_rhyme(rhyme)
        if not selected:
            click.echo(f"❌ Rhyme '{rhyme}' not found. Use --list.", err=True); sys.exit(1)
        click.echo(f"🎵 {selected.title}")
    else:
        click.echo("❌ Use --rhyme, --random, or --text. Use --list to see options.", err=True)
        sys.exit(1)

    safe_name   = selected.name.replace(" ", "_").lower()
    output_path = output or str(OUTPUT_DIR / f"{safe_name}.mp4")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="kids_cartoon_") as tmpdir:
        img_dir    = os.path.join(tmpdir, "images")
        audio_dir  = os.path.join(tmpdir, "audio")
        music_path = os.path.join(tmpdir, "music.mp3")

        click.echo(f"\n{'─'*50}")
        click.echo(f"🎬 {selected.title}  ({len(selected.scenes)} scenes)")
        click.echo(f"{'─'*50}\n")

        click.echo("Step 1/4 — Images  [Pollinations.ai — free, no key]")
        image_files = generate_scene_images(selected.scenes, img_dir, use_ai=not no_ai)

        click.echo("\nStep 2/4 — Voice  [edge-tts — free]")
        audio_files = generate_scene_audio(selected.scenes, audio_dir, voice=KIDS_VOICES[voice])

        click.echo("\nStep 3/4 — Music  [procedural — no API]")
        total_dur = sum(max(s.duration_seconds, 3.5) for s in selected.scenes) + 8
        generate_music_for_video(total_dur, music_path, music_theme)

        click.echo("\nStep 4/4 — Assemble video  [moviepy — free]")
        assemble_video(selected.scenes, image_files, audio_files, music_path,
                       output_path, selected.title, music_volume, fps)

    size_mb = os.path.getsize(output_path) / 1_000_000
    click.echo(f"\n🎉 Video ready:  {output_path}  ({size_mb:.1f} MB)\n")

    if upload:
        click.echo("📺 Uploading to YouTube  [YouTube Data API — free]\n")
        extra_tags = [t.strip() for t in yt_tags.split(",")] if yt_tags else []
        try:
            result = upload_video(output_path, selected.title, yt_description,
                                  extra_tags, privacy, not yt_not_for_kids)
            click.echo(f"\n🚀 Live on YouTube!")
            click.echo(f"   {result['url']}")
            click.echo(f"   Privacy: {result['privacy']}\n")
        except FileNotFoundError as e:
            click.echo(str(e), err=True); sys.exit(1)
        except Exception as e:
            click.echo(f"❌ Upload failed: {e}", err=True); sys.exit(1)
    else:
        click.echo("💡 Add --upload to post to YouTube automatically!\n")


if __name__ == "__main__":
    main()
