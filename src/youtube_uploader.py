import os
import json
import pickle
import time
from pathlib import Path
from typing import Optional

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

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube"]

CLIENT_SECRETS_FILE = Path(__file__).parent.parent / "credentials" / "client_secrets.json"
TOKEN_FILE          = Path(__file__).parent.parent / "credentials" / "token.pickle"

KIDS_TAGS = ["kids", "children", "cartoon", "nursery rhyme", "educational",
             "animation", "kids songs", "toddler", "preschool", "learning"]

CHUNK_SIZE = 5 * 1024 * 1024


def _check_deps():
    if not GOOGLE_LIBS_AVAILABLE:
        raise ImportError("Run: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2")


def _get_credentials():
    _check_deps()
    creds = None
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)
    if creds and creds.expired and creds.refresh_token:
        print("  🔄 Refreshing token...")
        creds.refresh(Request())
    if not creds or not creds.valid:
        if not CLIENT_SECRETS_FILE.exists():
            raise FileNotFoundError(
                f"\n❌ credentials/client_secrets.json not found!\n"
                f"   See YOUTUBE_SETUP.md for setup instructions.\n"
            )
        print("  🌐 Opening browser for YouTube authorization...")
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), SCOPES)
        creds = flow.run_local_server(port=0, prompt="consent",
                                      success_message="✅ Authorized! Close this tab.")
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
        print("  ✅ Token saved!\n")
    return creds


def get_youtube_client():
    return build("youtube", "v3", credentials=_get_credentials())


def upload_video(video_path, title, description=None, tags=None,
                 privacy="public", made_for_kids=True, category_id="27",
                 thumbnail_path=None):
    _check_deps()
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    if description is None:
        description = (
            f"🎨 {title}\n\nA fun cartoon for kids! 🌟\n\n"
            f"Watch and sing along to this classic nursery rhyme.\n\n"
            f"#KidsCartoon #NurseryRhymes #KidsSongs #ChildrensEducation"
        )

    all_tags = list(set((tags or []) + KIDS_TAGS))
    body = {
        "snippet": {"title": title, "description": description,
                    "tags": all_tags, "categoryId": category_id,
                    "defaultLanguage": "en", "defaultAudioLanguage": "en"},
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": made_for_kids,
                   "embeddable": True},
    }

    print("  🔐 Authenticating with YouTube...")
    youtube = get_youtube_client()
    size_mb = os.path.getsize(video_path) / 1_000_000
    print(f"  📤 Uploading: {os.path.basename(video_path)} ({size_mb:.1f} MB)")

    media = MediaFileUpload(video_path, mimetype="video/mp4",
                            chunksize=CHUNK_SIZE, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    retry = 0
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                bar = "█" * (pct//5) + "░" * (20 - pct//5)
                print(f"\r  ⬆️  [{bar}] {pct}%", end="", flush=True)
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504] and retry < 10:
                retry += 1
                wait = 2 ** retry
                print(f"\n  ⚠️  Retry {retry}/10 in {wait}s...")
                time.sleep(wait)
            else:
                raise

    print()
    video_id = response["id"]
    url = f"https://www.youtube.com/watch?v={video_id}"

    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            youtube.thumbnails().set(videoId=video_id,
                                     media_body=MediaFileUpload(thumbnail_path, mimetype="image/png")
                                     ).execute()
        except Exception:
            pass

    print(f"  🎉 Uploaded! {url}")
    return {"video_id": video_id, "url": url, "title": response["snippet"]["title"],
            "privacy": response["status"]["privacyStatus"], "status": "uploaded"}


def get_channel_info():
    _check_deps()
    youtube = get_youtube_client()
    response = youtube.channels().list(part="snippet,statistics", mine=True).execute()
    if response.get("items"):
        ch = response["items"][0]
        return {"name": ch["snippet"]["title"], "id": ch["id"],
                "url": f"https://www.youtube.com/channel/{ch['id']}",
                "subscribers": ch["statistics"].get("subscriberCount", "hidden"),
                "videos": ch["statistics"].get("videoCount", "0")}
    return {}


def revoke_credentials():
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
        print("✅ YouTube credentials removed.")
    else:
        print("ℹ️  No credentials found.")
