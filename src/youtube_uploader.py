import os
import time
import random
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from typing import Optional

from .config import (
    YOUTUBE_CLIENT_ID,
    YOUTUBE_CLIENT_SECRET,
    YOUTUBE_REFRESH_TOKEN,
    YOUTUBE_CHANNEL_ID,
)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_youtube_client():
    creds = Credentials(
        None,
        refresh_token=YOUTUBE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=YOUTUBE_CLIENT_ID,
        client_secret=YOUTUBE_CLIENT_SECRET,
        scopes=SCOPES,
    )

    return build("youtube", "v3", credentials=creds)


def upload_short(
    video_path: str, title: str, description: str, max_retries: int = 6
) -> Optional[str]:
    youtube = get_youtube_client()

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    if not os.path.isfile(video_path):
        raise FileNotFoundError(video_path)

    media = MediaFileUpload(
        video_path,
        chunksize=-1,
        resumable=True,
        mimetype="video/mp4",
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    attempt = 0

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"[youtube] Upload {int(status.progress() * 100)}%")

        except HttpError as e:
            # Try to detect "uploadLimitExceeded"
            reason = ""

            try:
                data = e.error_details if hasattr(e, "error_details") else None
                if not data:
                    import json

                    payload = json.loads(e.content.decode("utf-8"))
                    reason = payload["error"]["errors"][0].get("reason", "")
                else:
                    reason = str(data)
            except Exception:
                reason = ""

            if "uploadLimitExceeded" in str(e) or "uploadLimitExceeded" in reason:
                print("[youtube] ❗ uploadLimitExceeded → auto-skip upload")
                return None  # ✅ SKIP

            attempt += 1
            if attempt > max_retries:
                raise

            sleep_s = min(60, (2**attempt) + random.uniform(0.2, 1.5))
            print(
                f"[youtube] Upload chunk failed (attempt {attempt}/{max_retries}): {e}"
            )
            print(f"[youtube] Retrying in {sleep_s:.1f}s...")
            time.sleep(sleep_s)

        except Exception as e:
            attempt += 1
            if attempt > max_retries:
                raise

            sleep_s = min(60, (2**attempt) + random.uniform(0.2, 1.5))
            print(
                f"[youtube] Upload chunk failed (attempt {attempt}/{max_retries}): {e}"
            )
            print(f"[youtube] Retrying in {sleep_s:.1f}s...")
            time.sleep(sleep_s)

    vid = response["id"]
    print("[youtube] Upload complete:", vid)
    return vid


def post_comment(video_id: str, text: str) -> str:
    youtube = get_youtube_client()

    res = (
        youtube.commentThreads()
        .insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": text,
                        }
                    },
                }
            },
        )
        .execute()
    )

    comment_id = res["snippet"]["topLevelComment"]["id"]
    print(f"[youtube] Comment posted: {comment_id}")

    return comment_id
