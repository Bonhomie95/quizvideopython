from datetime import datetime, timedelta, timezone
from pymongo.errors import PyMongoError

from .config import UPLOAD_EVERY_HOURS, COMMENT_DELAY_HOURS
from . import db
from .main import main as run_once
from .youtube_commenter import comment_answer


def now():
    return datetime.now(timezone.utc)


def should_upload():
    try:
        uploads = db.uploads

        last = uploads.find_one(
            {"uploaded_at": {"$exists": True}},
            sort=[("uploaded_at", -1)],
        )

        if not last:
            return True

        uploaded_at = last["uploaded_at"]
        if uploaded_at.tzinfo is None:
            uploaded_at = uploaded_at.replace(tzinfo=timezone.utc)

        return (now() - uploaded_at) >= timedelta(hours=UPLOAD_EVERY_HOURS)

    except PyMongoError as e:
        print("⚠️ Mongo unavailable → skipping upload check:", e)
        return False


def handle_upload():
    print("📤 Uploading new video...")

    uploads = db.uploads  # ✅ FIX (THIS WAS MISSING)

    result = run_once()

    if not result or "video_id" not in result:
        raise RuntimeError("run_once() returned invalid result")

    uploads.insert_one(
        {
            "video_id": result["video_id"],
            "question": result["question"],
            "answer": result["answer"],
            "category": result["category"],
            "difficulty": result["difficulty"],
            "uploaded_at": now(),
            "commented": False,
            "commented_at": None,
        }
    )

    print("✅ Uploaded:", result["video_id"])


def handle_comments():
    try:
        uploads = db.uploads

        due = uploads.find(
            {
                "commented": False,
                "uploaded_at": {
                    "$lte": now() - timedelta(hours=COMMENT_DELAY_HOURS)
                },
            }
        )

        for item in due:
            try:
                print("💬 Commenting answer on:", item["video_id"])
                comment_answer(item["video_id"], item["answer"])

                uploads.update_one(
                    {"_id": item["_id"]},
                    {
                        "$set": {
                            "commented": True,
                            "commented_at": now(),
                        }
                    },
                )

                print("✅ Commented:", item["video_id"])

            except Exception as e:
                print("❌ Comment failed for", item["video_id"], "→", e)

    except PyMongoError as e:
        print("⚠️ Mongo unavailable → skipping comments:", e)


def run():
    print("⏳ Scheduler tick:", now().isoformat())

    if should_upload():
        handle_upload()
    else:
        print("⏭ Upload not due yet")

    handle_comments()


if __name__ == "__main__":
    run()
