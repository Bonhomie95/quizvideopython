from datetime import datetime
from pymongo import MongoClient
from .config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client.quiz_video_bot
uploads = db.uploads

# doc shape:
# {
#   video_id, comment, run_at, posted=False,
#   attempts=0, last_error=None, created_at, posted_at
# }


def save_pending_comment(video_id: str, comment: str, run_at: datetime):
    uploads.update_one(
        {"video_id": video_id},
        {
            "$set": {
                "video_id": video_id,
                "comment": comment,
                "run_at": run_at,
                "posted": False,
                "attempts": 0,
                "last_error": None,
                "created_at": datetime.utcnow(),
            }
        },
        upsert=True,
    )


def get_due_comments(now: datetime, limit: int = 20):
    return list(
        uploads.find({"posted": False, "run_at": {"$lte": now}})
        .sort("run_at", 1)
        .limit(limit)
    )


def mark_posted(video_id: str):
    uploads.update_one(
        {"video_id": video_id},
        {"$set": {"posted": True, "posted_at": datetime.utcnow(), "last_error": None}},
    )


def mark_failed(video_id: str, err: str):
    uploads.update_one(
        {"video_id": video_id},
        {
            "$inc": {"attempts": 1},
            "$set": {"last_error": err, "last_try_at": datetime.utcnow()},
        },
    )
