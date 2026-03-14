"""
youtube_uploader.py — Upload cartoon videos to YouTube automatically.

Uses YouTube Data API v3 (FREE — included with every Google account).
Requires one-time OAuth2 setup with your Google account.

SETUP (one time only):
  1. Go to https://console.cloud.google.com
  2. Create a new project (e.g. "Kids Cartoon Maker")
  3. Enable "YouTube Data API v3"
  4. Create OAuth 2.0 credentials → Desktop App
  5. Download the JSON and save as: credentials/client_secrets.json
  6. Run: python main.py --rhyme twinkle --upload
     (A browser window opens to authorize once, then it's automatic!)

Quota: YouTube API gives 10,000 units/day free.
       One video upload costs ~1,600 units → ~6 uploads/day free.
"""

import os
import json
import pickle
import time
from pathlib import Path
from typing import Optional

# Google API libraries
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    GOOGLE_LIBS_AVAILABLE = False


# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube"]

CLIENT_SECRETS_FILE = Path(__file__).parent.parent / "credentials" / "client_secrets.json"
TOKEN_FILE          = Path(__file__).parent.parent / "credentials" / "token.pickle"

YOUTUBE_API_SERVICE = "youtube"
YOUTUBE_API_VERSION = "v3"

# Resumable upload chunk size (5MB)
CHUNK_SIZE = 5 * 1024 * 1024

# Default video metadata for kids content
DEFAULT_CATEGORY_ID = "27"   # Education
KIDS_TAGS = [
    "kids", "children", "cartoon", "nursery rhyme", "educational",
    "animation", "kids songs", "toddler", "preschool", "learning",
    "kids cartoon", "free kids video", "nursery rhymes for kids"
]


# ─────────────────────────────────────────────
# AUTHENTICATION
# ─────────────────────────────────────────────

def _check_dependencies():
    """Make sure Google API libraries are installed."""
    if not GOOGLE_LIBS_AVAILABLE:
        raise ImportError(
            "Google API libraries not installed. Run:\n"
            "  pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
        )


def _get_credentials() -> Credentials:
    """
    Get or refresh OAuth2 credentials.
    Opens browser for authorization on first run, then stores token locally.
    """
    _check_dependencies()
    creds = None

    # Load existing token if available
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    # Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        print("  🔄 Refreshing YouTube access token...")
        creds.refresh(Request())

    # Full OAuth flow if no valid credentials
    if not creds or not creds.valid:
        if not CLIENT_SECRETS_FILE.exists():
            raise FileNotFoundError(
                f"\n❌ YouTube credentials not found at:\n"
                f"   {CLIENT_SECRETS_FILE}\n\n"
                f"📋 Setup Instructions:\n"
                f"   1. Visit: https://console.cloud.google.com\n"
                f"   2. Create project → Enable 'YouTube Data API v3'\n"
                f"   3. Create OAuth 2.0 credentials (Desktop App)\n"
                f"   4. Download JSON → save as: credentials/client_secrets.json\n"
                f"   5. Run again — a browser window will open to authorize\n"
            )

        print("  🌐 Opening browser for YouTube authorization...")
        print("  (This only happens once — your token will be saved locally)\n")

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CLIENT_SECRETS_FILE), SCOPES
        )
        creds = flow.run_local_server(
            port=0,
            prompt="consent",
            success_message="✅ Authorization successful! You can close this tab.",
        )

        # Save token for future runs
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
        print("  ✅ Credentials saved — future uploads will be automatic!\n")

    return creds


def get_youtube_client():
    """Return an authenticated YouTube API client."""
    creds = _get_credentials()
    return build(YOUTUBE_API_SERVICE, YOUTUBE_API_VERSION, credentials=creds)


# ─────────────────────────────────────────────
# UPLOAD
# ─────────────────────────────────────────────

def build_video_metadata(
    title: str,
    description: str,
    tags: list[str],
    category_id: str = DEFAULT_CATEGORY_ID,
    privacy: str = "public",
    made_for_kids: bool = True,
    language: str = "en",
) -> dict:
    """Build the YouTube video metadata body."""
    return {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
            "defaultLanguage": language,
            "defaultAudioLanguage": language,
        },
        "status": {
            "privacyStatus": privacy,          # "public", "unlisted", "private"
            "selfDeclaredMadeForKids": made_for_kids,
            "embeddable": True,
            "publicStatsViewable": True,
        },
    }


def upload_video(
    video_path: str,
    title: str,
    description: Optional[str] = None,
    tags: Optional[list[str]] = None,
    privacy: str = "public",
    made_for_kids: bool = True,
    category_id: str = DEFAULT_CATEGORY_ID,
    thumbnail_path: Optional[str] = None,
) -> dict:
    """
    Upload a video to YouTube.

    Args:
        video_path:      Path to the MP4 file
        title:           Video title
        description:     Video description (auto-generated if None)
        tags:            List of tags (kids tags added automatically)
        privacy:         "public", "unlisted", or "private"
        made_for_kids:   Mark as made for kids (COPPA compliance)
        category_id:     YouTube category (27 = Education)
        thumbnail_path:  Optional custom thumbnail image

    Returns:
        dict with video_id, url, title, and upload status
    """
    _check_dependencies()

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Auto-generate description
    if description is None:
        description = (
            f"🎨 {title}\n\n"
            f"A fun, educational cartoon for kids! 🌟\n\n"
            f"Watch and sing along to this classic nursery rhyme, "
            f"brought to life with colorful cartoon animation.\n\n"
            f"Perfect for:\n"
            f"✅ Toddlers & preschoolers\n"
            f"✅ Learning words and rhymes\n"
            f"✅ Bedtime or playtime\n\n"
            f"Created with Kids Cartoon Maker — free & open source!\n"
            f"https://github.com/YOUR_USERNAME/kids-cartoon-maker\n\n"
            f"#KidsCartoon #NurseryRhymes #KidsSongs #ChildrensEducation #FreeKidsVideo"
        )

    # Merge custom tags with default kids tags
    all_tags = list(set((tags or []) + KIDS_TAGS))

    # Build metadata
    body = build_video_metadata(
        title=title,
        description=description,
        tags=all_tags,
        category_id=category_id,
        privacy=privacy,
        made_for_kids=made_for_kids,
    )

    # Get YouTube client
    print("  🔐 Authenticating with YouTube...")
    youtube = get_youtube_client()

    # Set up resumable upload
    file_size_mb = os.path.getsize(video_path) / 1_000_000
    print(f"  📤 Uploading: {os.path.basename(video_path)} ({file_size_mb:.1f} MB)")
    print(f"  📺 Title: {title}")
    print(f"  🔒 Privacy: {privacy}")

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        chunksize=CHUNK_SIZE,
        resumable=True,
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    # Execute upload with progress reporting
    response = None
    retry_count = 0
    max_retries = 10

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
                print(f"\r  ⬆️  [{bar}] {pct}%", end="", flush=True)
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504] and retry_count < max_retries:
                retry_count += 1
                wait = 2 ** retry_count
                print(f"\n  ⚠️  Server error, retrying in {wait}s (attempt {retry_count}/{max_retries})...")
                time.sleep(wait)
            else:
                raise

    print()  # newline after progress bar

    video_id  = response["id"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    # Upload custom thumbnail if provided
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            print("  🖼️  Uploading thumbnail...")
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype="image/png"),
            ).execute()
            print("  ✅ Thumbnail uploaded!")
        except HttpError as e:
            print(f"  ⚠️  Thumbnail upload failed (video still uploaded): {e}")

    result = {
        "video_id":  video_id,
        "url":       video_url,
        "title":     response["snippet"]["title"],
        "privacy":   response["status"]["privacyStatus"],
        "status":    "uploaded",
    }

    print(f"\n  🎉 Upload complete!")
    print(f"  📺 Watch at: {video_url}")

    return result


# ─────────────────────────────────────────────
# CHANNEL INFO
# ─────────────────────────────────────────────

def get_channel_info() -> dict:
    """Return info about the authenticated YouTube channel."""
    _check_dependencies()
    youtube = get_youtube_client()
    response = youtube.channels().list(part="snippet,statistics", mine=True).execute()
    if response.get("items"):
        ch = response["items"][0]
        return {
            "name":       ch["snippet"]["title"],
            "id":         ch["id"],
            "url":        f"https://www.youtube.com/channel/{ch['id']}",
            "subscribers": ch["statistics"].get("subscriberCount", "hidden"),
            "videos":     ch["statistics"].get("videoCount", "0"),
        }
    return {}


def revoke_credentials() -> None:
    """Delete saved token (forces re-authorization next run)."""
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
        print("✅ YouTube credentials revoked. Run again to re-authorize.")
    else:
        print("ℹ️  No saved credentials found.")
