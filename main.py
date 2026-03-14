#!/usr/bin/env python3
"""
Kids Cartoon Maker — main.py
============================
100% free, open-source cartoon video generator for kids.
Every single API and tool used is completely free — no credit card,
no paid tiers, no API keys required (except YouTube OAuth which is free).

FREE SERVICES USED:
  🖼️  Images  — Pollinations.ai   (free, no key, no sign-up)
  🎤  Voice   — edge-tts           (free, Microsoft Edge engine)
  🎵  Music   — procedural numpy   (no API at all, generated locally)
  📖  Rhymes  — built-in library   (public domain)
  🎬  Video   — moviepy + ffmpeg   (open source)
  📺  YouTube — YouTube Data API   (free, 10k units/day)

Usage:
    python main.py --rhyme twinkle
    python main.py --random --upload
    python main.py --text "Roses are red..." --title "My Poem" --upload
    python main.py --list
    python main.py --yt-info
    python main.py --yt-logout
"""

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


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════╗
║   🎨  Kids Cartoon Maker  —  100% Free & Open Source  🎨 ║
║   No paid APIs. No credit card. No sign-up required.     ║
╚══════════════════════════════════════════════════════════╝
""")


@click.command()
# Rhyme selection
@click.option("--rhyme",     "-r",   default=None,     help="Built-in rhyme name. Use --list to see all.")
@click.option("--random",    "use_random", is_flag=True, help="Pick a random built-in rhyme.")
@click.option("--text",      "-t",   default=None,     help="Your own rhyme text (one line per verse).")
@click.option("--title",             default="My Rhyme",help="Title when using --text.")
@click.option("--list",      "show_list", is_flag=True, help="List all built-in rhymes and exit.")
# Media options
@click.option("--voice",     default="uk_girl",
              type=click.Choice(list(KIDS_VOICES.keys())), help="Narrator voice style.")
@click.option("--music",     "music_theme", default="playful",
              type=click.Choice(MUSIC_THEMES),            help="Background music theme.")
@click.option("--music-volume", default=0.15, type=float, help="Music volume 0.0-1.0 (default 0.15).")
@click.option("--no-ai",     is_flag=True,  help="Use procedural art only (faster, works offline).")
@click.option("--fps",       default=24, type=int,       help="Video frame rate (default 24).")
@click.option("--output",    "-o",  default=None,        help="Output MP4 path.")
# YouTube upload
@click.option("--upload",    is_flag=True,  help="Upload the video to your YouTube channel (free).")
@click.option("--privacy",   default="public",
              type=click.Choice(PRIVACY_OPTS),            help="YouTube privacy (default: public).")
@click.option("--yt-description", default=None,           help="Custom YouTube description.")
@click.option("--yt-tags",        default=None,           help="Comma-separated extra YouTube tags.")
@click.option("--yt-not-for-kids", is_flag=True,          help="Do NOT mark as 'made for kids'.")
# YouTube account management
@click.option("--yt-info",   is_flag=True, help="Show connected YouTube channel info.")
@click.option("--yt-logout", is_flag=True, help="Disconnect YouTube account.")
def main(
    rhyme, use_random, text, title, show_list,
    voice, music_theme, music_volume, no_ai, fps, output,
    upload, privacy, yt_description, yt_tags, yt_not_for_kids,
    yt_info, yt_logout,
):
    """🎨 Kids Cartoon Maker — 100% free cartoon videos, auto-uploaded to YouTube."""
    print_banner()

    # ── YouTube account management
    if yt_logout:
        revoke_credentials()
        return

    if yt_info:
        click.echo("🔐 Fetching your YouTube channel info...\n")
        try:
            info = get_channel_info()
            if info:
                click.echo(f"  📺 Channel : {info['name']}")
                click.echo(f"  🔗 URL     : {info['url']}")
                click.echo(f"  👥 Subs    : {info['subscribers']}")
                click.echo(f"  🎬 Videos  : {info['videos']}")
            else:
                click.echo("  ⚠️  Could not retrieve channel info.")
        except FileNotFoundError as e:
            click.echo(str(e))
        return

    # ── Rhyme list
    if show_list:
        click.echo("📚 Available built-in rhymes:\n")
        for name in list_rhymes():
            r = get_rhyme(name)
            click.echo(f"  • {name:12} — {r.title} ({len(r.scenes)} scenes)")
        click.echo("\nExamples:")
        click.echo("  python main.py --rhyme twinkle")
        click.echo("  python main.py --rhyme twinkle --upload\n")
        return

    # ── Resolve rhyme
    if text:
        selected_rhyme = get_rhyme_from_text(text, title=title)
        click.echo(f"📝 Custom rhyme: {title}")
    elif use_random:
        selected_rhyme = get_random_rhyme()
        click.echo(f"🎲 Random rhyme: {selected_rhyme.title}")
    elif rhyme:
        selected_rhyme = get_rhyme(rhyme)
        if not selected_rhyme:
            click.echo(f"❌ Rhyme '{rhyme}' not found. Use --list to see options.", err=True)
            sys.exit(1)
        click.echo(f"🎵 Rhyme: {selected_rhyme.title}")
    else:
        click.echo("❌ Specify --rhyme, --random, or --text. Run --list to see options.", err=True)
        sys.exit(1)

    # ── Output path
    safe_name   = selected_rhyme.name.replace(" ", "_").lower()
    output_path = output or str(OUTPUT_DIR / f"{safe_name}.mp4")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # ─── PRODUCTION PIPELINE ──────────────────────────────
    with tempfile.TemporaryDirectory(prefix="kids_cartoon_") as tmpdir:
        img_dir    = os.path.join(tmpdir, "images")
        audio_dir  = os.path.join(tmpdir, "audio")
        music_path = os.path.join(tmpdir, "music.mp3")

        click.echo(f"\n{'─'*56}")
        click.echo(f"🎬 Creating  : {selected_rhyme.title}")
        click.echo(f"   Scenes    : {len(selected_rhyme.scenes)}")
        click.echo(f"   Images    : {'Pollinations.ai (free)' if not no_ai else 'Procedural art (offline)'}")
        click.echo(f"   Voice     : {voice} — edge-tts (free)")
        click.echo(f"   Music     : {music_theme} — procedural (free)")
        click.echo(f"   Output    : {output_path}")
        if upload:
            click.echo(f"   YouTube   : ✅ Will upload ({privacy}) — free API")
        click.echo(f"{'─'*56}\n")

        # STEP 1 — Cartoon images via Pollinations.ai (free, no key)
        click.echo("Step 1/4 — Generating cartoon images  [Pollinations.ai — free, no key]")
        image_files = generate_scene_images(
            scenes=selected_rhyme.scenes,
            output_dir=img_dir,
            use_ai=not no_ai,
        )

        # STEP 2 — Voice narration via edge-tts (free)
        click.echo("\nStep 2/4 — Generating voice narration  [edge-tts — free, no key]")
        audio_files = generate_scene_audio(
            scenes=selected_rhyme.scenes,
            output_dir=audio_dir,
            voice=KIDS_VOICES[voice],
        )

        # STEP 3 — Background music procedurally (no API at all)
        click.echo("\nStep 3/4 — Generating background music  [procedural numpy — no API]")
        total_duration = sum(max(s.duration_seconds, 3.5) for s in selected_rhyme.scenes) + 8
        generate_music_for_video(
            total_duration_seconds=total_duration,
            output_path=music_path,
            theme=music_theme,
        )

        # STEP 4 — Assemble MP4
        click.echo("\nStep 4/4 — Assembling final video  [moviepy — free, open source]")
        assemble_video(
            scenes=selected_rhyme.scenes,
            image_files=image_files,
            audio_files=audio_files,
            music_path=music_path,
            output_path=output_path,
            rhyme_title=selected_rhyme.title,
            music_volume=music_volume,
            fps=fps,
        )

    size_mb = os.path.getsize(output_path) / 1_000_000
    click.echo(f"\n{'═'*56}")
    click.echo(f"🎉 Video ready!")
    click.echo(f"   📁 File : {output_path}")
    click.echo(f"   📦 Size : {size_mb:.1f} MB")
    click.echo(f"{'═'*56}\n")

    # ─── YOUTUBE UPLOAD (free — YouTube Data API v3) ──────
    if upload:
        click.echo("📺 Uploading to YouTube  [YouTube Data API v3 — free]\n")
        extra_tags = [t.strip() for t in yt_tags.split(",")] if yt_tags else []
        try:
            result = upload_video(
                video_path=output_path,
                title=selected_rhyme.title,
                description=yt_description,
                tags=extra_tags,
                privacy=privacy,
                made_for_kids=not yt_not_for_kids,
            )
            click.echo(f"\n{'═'*56}")
            click.echo(f"🚀 Uploaded to YouTube!")
            click.echo(f"   📺 Title    : {result['title']}")
            click.echo(f"   🔗 URL      : {result['url']}")
            click.echo(f"   🔒 Privacy  : {result['privacy']}")
            click.echo(f"   🆔 Video ID : {result['video_id']}")
            click.echo(f"{'═'*56}\n")
        except FileNotFoundError as e:
            click.echo(str(e), err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"\n❌ YouTube upload failed: {e}", err=True)
            click.echo("   Video was saved locally — upload it manually if needed.", err=True)
            sys.exit(1)
    else:
        click.echo("💡 Add --upload to post this automatically to your YouTube channel!\n")

    click.echo("Keep creating! 🌟\n")


if __name__ == "__main__":
    main()
