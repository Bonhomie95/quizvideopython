from .youtube_uploader import get_youtube_client


def comment_answer(video_id: str, answer_text: str) -> str:
    yt = get_youtube_client()

    body = {
        "snippet": {
            "videoId": video_id,
            "topLevelComment": {
                "snippet": {"textOriginal": f"✅ Answer: {answer_text}"}
            },
        }
    }

    res = yt.commentThreads().insert(part="snippet", body=body).execute()

    return res["id"]
