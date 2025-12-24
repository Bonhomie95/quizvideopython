import time
from datetime import datetime
from .db import get_due_comments, mark_posted, mark_failed
from .youtube_uploader import post_comment

MAX_ATTEMPTS = 6


def run():
    due = get_due_comments(datetime.utcnow())

    if not due:
        print("[comment-worker] No due comments.")
        return

    for item in due:
        video_id = item["video_id"]
        comment = item["comment"]
        attempts = int(item.get("attempts", 0))

        if attempts >= MAX_ATTEMPTS:
            print(f"[comment-worker] Skipping {video_id} (attempts={attempts})")
            continue

        try:
            print(
                f"[comment-worker] Posting comment for {video_id} (attempt {attempts+1}/{MAX_ATTEMPTS})"
            )
            comment_id = post_comment(video_id, comment)
            mark_posted(video_id)

            # Pinning not supported in official API → manual
            print(
                f"[comment-worker] Comment posted: {comment_id} | PIN MANUALLY if you want it pinned."
            )

        except Exception as e:
            err = str(e)
            print("[comment-worker] FAILED:", err)
            mark_failed(video_id, err)

            # small backoff so we don't hammer API
            time.sleep(min(20, 2 + attempts * 3))


if __name__ == "__main__":
    run()
