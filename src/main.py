print("🔥 MAIN FILE LOADED")

from datetime import datetime, timedelta
import os
import tempfile
import shutil
import hashlib
import json

from .picker import pick_question
from .renderer.quiz_renderer import render_quiz_frames, pick_music
from .renderer.cta_renderer import render_cta_frames
from .renderer.video_builder import build_video

from .platforms.youtube import YOUTUBE_PLATFORM
from .platforms.facebook import FACEBOOK_PLATFORM
from .platforms.tiktok import TIKTOK_PLATFORM

from .youtube_uploader import upload_short
from .db import save_pending_comment
from .config import DRY_RUN, CACHE_DIR

FPS = 30


# =====================================================
# HASHTAGS (GENERAL QUIZ – SAFE DEFAULT)
# =====================================================
YT_HASHTAGS = (
    "#shorts #quiz #trivia #brainchallenge "
    "#canYouAnswer #noGoogle #beHonest #thinkFast #viral"
)


# =====================================================
# HELPERS
# =====================================================
def _copy_quiz_frames(src_dir: str, dst_dir: str):
    os.makedirs(dst_dir, exist_ok=True)
    for name in os.listdir(src_dir):
        if name.startswith("frame_") and name.endswith(".png"):
            shutil.copy2(
                os.path.join(src_dir, name),
                os.path.join(dst_dir, name),
            )


def _cache_key(q: dict) -> str:
    payload = {
        "question": q.get("question"),
        "options": q.get("options"),
        "answer": q.get("answer"),
        "category": q.get("category"),
        "difficulty": q.get("difficulty"),
    }
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:16]


def build_yt_title(hook: str) -> str:
    """
    Short, punchy, hook-based title for Shorts
    """
    return hook.strip()


def build_yt_description(q: dict, hook: str) -> str:
    """
    Hook + question + CTA + hashtags
    """
    return f"""
{hook}

🧠 Question:
{q['question']}

👇 Comment your answer before checking!

{YT_HASHTAGS}
""".strip()


# =====================================================
# MAIN
# =====================================================
def main():
    print("🚀 main() entered")

    # =========================
    # PICK QUESTION
    # =========================
    q = pick_question()
    print("🧠 Question picked:", q["question"])

    key = _cache_key(q)
    os.makedirs(CACHE_DIR, exist_ok=True)

    cached_yt = os.path.join(CACHE_DIR, f"youtube_{key}.mp4")

    # =========================
    # PICK MUSIC ONCE (GLOBAL)
    # =========================
    music = pick_music()
    print("🎵 Picked music for ALL platforms:", music)

    base_frames_dir = tempfile.mkdtemp(prefix="quiz_base_frames_")
    print("📂 Base frames dir:", base_frames_dir)

    results = {}

    try:
        # =========================
        # BASE QUIZ FRAMES
        # =========================
        quiz_result = render_quiz_frames(q, base_frames_dir)
        last_frame = quiz_result["frames"]
        hook_text = quiz_result["hook"]

        print("🎞 Quiz frames rendered up to:", last_frame)
        print("🪝 Hook used:", hook_text)

        yt_title = build_yt_title(hook_text)
        yt_description = build_yt_description(q, hook_text)

        # =====================================================
        # YOUTUBE (CTA + BUILD + UPLOAD)
        # =====================================================
        yt_frames_dir = tempfile.mkdtemp(prefix="quiz_yt_frames_")
        _copy_quiz_frames(base_frames_dir, yt_frames_dir)

        print("🎯 Rendering CTA for YouTube")
        yt_cta_frames = render_cta_frames(
            frames_dir=yt_frames_dir,
            start_index=last_frame + 1,
            platform=YOUTUBE_PLATFORM,
        )
        if not isinstance(yt_cta_frames, int):
            raise RuntimeError("CTA renderer must return frame count")

        if os.path.isfile(cached_yt):
            yt_video_path = cached_yt
            print("♻️ Using cached YouTube video:", yt_video_path)
        else:
            yt_video_path = build_video(
                frames_dir=yt_frames_dir,
                output_dir="output/renders",
                fps=FPS,
                music=music,
                prefix="youtube",
            )
            shutil.copy2(yt_video_path, cached_yt)
            print("✅ Cached YouTube video:", cached_yt)

        video_id = None
        if DRY_RUN:
            print("🧪 DRY_RUN=true → skipping YouTube upload")
        else:
            video_id = upload_short(
                yt_video_path,
                title=yt_title,
                description=yt_description,
            )

        if video_id:
            print("📤 Uploaded to YouTube:", video_id)
            save_pending_comment(
                video_id=video_id,
                comment=f"✅ Correct answer: {q['answer']}",
                run_at=datetime.utcnow() + timedelta(hours=24),
            )

        results["youtube"] = video_id
        results["youtube_video_path"] = yt_video_path
        shutil.rmtree(yt_frames_dir, ignore_errors=True)

        # =====================================================
        # FACEBOOK (CTA + BUILD ONLY)
        # =====================================================
        fb_frames_dir = tempfile.mkdtemp(prefix="quiz_fb_frames_")
        _copy_quiz_frames(base_frames_dir, fb_frames_dir)

        render_cta_frames(
            frames_dir=fb_frames_dir,
            start_index=last_frame + 1,
            platform=FACEBOOK_PLATFORM,
        )

        results["facebook_video_path"] = build_video(
            frames_dir=fb_frames_dir,
            output_dir="output/renders",
            fps=FPS,
            music=music,
            prefix="facebook",
        )
        shutil.rmtree(fb_frames_dir, ignore_errors=True)

        # =====================================================
        # TIKTOK (CTA + BUILD ONLY)
        # =====================================================
        tt_frames_dir = tempfile.mkdtemp(prefix="quiz_tt_frames_")
        _copy_quiz_frames(base_frames_dir, tt_frames_dir)

        render_cta_frames(
            frames_dir=tt_frames_dir,
            start_index=last_frame + 1,
            platform=TIKTOK_PLATFORM,
        )

        results["tiktok_video_path"] = build_video(
            frames_dir=tt_frames_dir,
            output_dir="output/renders",
            fps=FPS,
            music=music,
            prefix="tiktok",
        )
        shutil.rmtree(tt_frames_dir, ignore_errors=True)

        print("✅ DONE:", results)

        return {
            "video_id": results.get("youtube"),
            "question": q["question"],
            "answer": q["answer"],
            "category": q["category"],
            "difficulty": q["difficulty"],
            "youtube_video_path": results.get("youtube_video_path"),
            "facebook_video_path": results.get("facebook_video_path"),
            "tiktok_video_path": results.get("tiktok_video_path"),
        }

    finally:
        shutil.rmtree(base_frames_dir, ignore_errors=True)
        print("🧹 Base frames cleaned:", base_frames_dir)


if __name__ == "__main__":
    print("▶ __main__ block hit")
    main()
