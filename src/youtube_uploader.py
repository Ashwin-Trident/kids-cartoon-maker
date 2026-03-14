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
            f"#KidsCartoon #NurseryRhymes #KidsSong
