import os
import pickle
import time
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]

BASE_DIR = Path(__file__).parent.parent

CLIENT_SECRETS_FILE = BASE_DIR / "credentials" / "client_secrets.json"
TOKEN_FILE = BASE_DIR / "credentials" / "token.pickle"

CHUNK_SIZE = 5 * 1024 * 1024


KIDS_TAGS = [
    "kids",
    "cartoon",
    "nursery rhyme",
    "children",
    "kids animation",
    "kids learning",
    "toddler",
    "preschool"
]


# -------------------------------------------------------
# AUTHENTICATION
# -------------------------------------------------------

def get_credentials():

    if not TOKEN_FILE.exists():
        raise FileNotFoundError(
            "❌ token.pickle missing. Add it in credentials folder."
        )

    with open(TOKEN_FILE, "rb") as f:
        creds = pickle.load(f)

    if creds.expired and creds.refresh_token:
        print("🔄 Refreshing YouTube token...")
        creds.refresh(Request())

    return creds


def get_youtube_client():

    creds = get_credentials()

    return build(
        "youtube",
        "v3",
        credentials=creds,
        cache_discovery=False
    )


# -------------------------------------------------------
# VIDEO UPLOAD
# -------------------------------------------------------

def upload_video(
        video_path,
        title,
        description=None,
        tags=None,
        privacy="public",
        made_for_kids=True,
        category_id="27",
        thumbnail_path=None
):

    if not os.path.exists(video_path):
        raise FileNotFoundError(video_path)

    if description is None:
        description = (
            f"{title}\n\n"
            "Fun kids cartoon animation.\n\n"
            "#kids #cartoon #nurseryrhyme"
        )

    tags = list(set((tags or []) + KIDS_TAGS))

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en"
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": made_for_kids,
            "embeddable": True
        }
    }

    print("🔐 Connecting to YouTube API...")

    youtube = get_youtube_client()

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        chunksize=CHUNK_SIZE,
        resumable=True
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    retry = 0

    print("📤 Uploading video...")

    while response is None:

        try:

            status, response = request.next_chunk()

            if status:
                progress = int(status.progress() * 100)
                bar = "█" * (progress // 5) + "░" * (20 - progress // 5)

                print(f"\r⬆️  [{bar}] {progress}% ", end="", flush=True)

        except HttpError as e:

            if e.resp.status in [500, 502, 503, 504] and retry < 10:

                retry += 1
                wait = 2 ** retry

                print(f"\n⚠️ Upload error. Retry {retry} in {wait}s...")
                time.sleep(wait)

            else:
                raise

    print()

    video_id = response["id"]

    video_url = f"https://www.youtube.com/watch?v={video_id}"

    print("🎉 Upload successful!")
    print("🔗", video_url)

    # -------------------------------------------------------
    # Upload thumbnail
    # -------------------------------------------------------

    if thumbnail_path and os.path.exists(thumbnail_path):

        try:

            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()

            print("🖼️ Thumbnail uploaded")

        except Exception:
            print("⚠️ Thumbnail upload failed")

    return video_url


# -------------------------------------------------------
# CHANNEL INFO
# -------------------------------------------------------

def get_channel_info():

    youtube = get_youtube_client()

    response = youtube.channels().list(
        part="snippet,statistics",
        mine=True
    ).execute()

    if not response["items"]:
        return {}

    ch = response["items"][0]

    return {
        "name": ch["snippet"]["title"],
        "channel_id": ch["id"],
        "subscribers": ch["statistics"].get("subscriberCount"),
        "videos": ch["statistics"].get("videoCount")
    }


# -------------------------------------------------------
# REMOVE TOKEN
# -------------------------------------------------------

def revoke_credentials():

    if TOKEN_FILE.exists():

        TOKEN_FILE.unlink()

        print("✅ Token removed")

    else:
        print("ℹ️ No token found")
