import requests
import time


class FacebookVideoUploader:
    GRAPH = "https://graph.facebook.com/v19.0"

    def __init__(self, page_id: str, page_token: str):
        self.page_id = page_id
        self.token = page_token

    def upload_video(self, video_path: str, caption: str) -> str:
        url = f"{self.GRAPH}/{self.page_id}/videos"

        with open(video_path, "rb") as f:
            files = {"source": f}
            data = {
                "access_token": self.token,
                "description": caption,
                "published": "true",
            }

            r = requests.post(url, files=files, data=data)
            r.raise_for_status()

        video_id = r.json().get("id")
        if not video_id:
            raise RuntimeError("Facebook video upload failed")

        return video_id


    def _wait_until_ready(self, video_id: str, timeout=300):
        start = time.time()

        while time.time() - start < timeout:
            r = requests.get(
                f"{self.GRAPH}/{video_id}",
                params={
                    "fields": "status",
                    "access_token": self.token,
                },
            )
            r.raise_for_status()

            status = r.json().get("status", {}).get("video_status")
            print("[facebook] status:", status)

            if status == "ready":
                return

            time.sleep(5)

        raise TimeoutError("Facebook video processing timed out")


def upload_facebook_with_retry(uploader, video_path, caption, retries=3):
    for attempt in range(1, retries + 1):
        try:
            print(f"[facebook] Upload attempt {attempt}")
            return uploader.upload_reel(video_path, caption)
        except Exception as e:
            print("[facebook] Upload failed:", e)
            if attempt == retries:
                raise
            time.sleep(10)
