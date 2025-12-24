print("🔥 MAIN FILE LOADED")

from datetime import datetime, timedelta
import os
import tempfile
import shutil
import hashlib
import json

from .picker import pick_question
from .renderer.quiz_renderer import render_quiz_frames
from .renderer.cta_renderer import render_cta_frames
from .renderer.video_builder import build_video

from .platforms.youtube import YOUTUBE_PLATFORM
from .platforms.facebook import FACEBOOK_PLATFORM
from .youtube_uploader import upload_short
from .db import save_pending_comment
from .config import DRY_RUN, CACHE_DIR

FPS = 30


def _copy_quiz_frames(src_dir: str, dst_dir: str):
    os.makedirs(dst_dir, exist_ok=True)
    for name in os.listdir(src_dir):
        if name.startswith("frame_") and name.endswith(".png"):
            shutil.copy2(
                os.path.join(src_dir, name),
                os.path.join(dst_dir, name),
            )


def _cache_key(q: dict) -> str:
    # stable key: same question/options/answer => same render cache
    payload = {
        "question": q.get("question"),
        "options": q.get("options"),
        "answer": q.get("answer"),
        "category": q.get("category"),
        "difficulty": q.get("difficulty"),
    }
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:16]


def main():
    print("🚀 main() entered")

    q = pick_question()
    print("🧠 Question picked:", q["question"])

    key = _cache_key(q)
    os.makedirs(CACHE_DIR, exist_ok=True)

    cached_yt = os.path.join(CACHE_DIR, f"youtube_{key}.mp4")
    cached_fb = os.path.join(CACHE_DIR, f"facebook_{key}.mp4")

    base_frames_dir = tempfile.mkdtemp(prefix="quiz_base_frames_")
    print("📂 Base frames dir:", base_frames_dir)

    results = {}

    try:
        # 1) Render quiz frames once
        last_frame = render_quiz_frames(q, base_frames_dir)
        print("🎞 Quiz frames rendered up to:", last_frame)

        # =========================
        # YOUTUBE (CTA + BUILD + UPLOAD)
        # =========================
        yt_frames_dir = tempfile.mkdtemp(prefix="quiz_yt_frames_")
        _copy_quiz_frames(base_frames_dir, yt_frames_dir)

        print("🎯 Rendering CTA for youtube")
        cta_frames = render_cta_frames(
            frames_dir=yt_frames_dir,
            start_index=last_frame + 1,
            platform=YOUTUBE_PLATFORM,
        )
        if not isinstance(cta_frames, int):
            raise RuntimeError("CTA renderer must return frame count")

        if os.path.isfile(cached_yt):
            yt_video_path = cached_yt
            print("♻️ Using cached YouTube video:", yt_video_path)
        else:
            yt_video_path = build_video(
                frames_dir=yt_frames_dir,
                output_dir="output/renders",
                fps=FPS,
                music=None,
                prefix="youtube",
            )
            print("🎬 YouTube video built:", yt_video_path)
            shutil.copy2(yt_video_path, cached_yt)
            print("✅ Cached YouTube video:", cached_yt)

        video_id = None

        if DRY_RUN:
            print("🧪 DRY_RUN=true → skipping YouTube upload")
        else:
            video_id = upload_short(
                yt_video_path,
                title=YOUTUBE_PLATFORM["title"](q),
                description=YOUTUBE_PLATFORM["description"](q),
            )

        if video_id:
            print("📤 Uploaded to YouTube:", video_id)

            save_pending_comment(
                video_id=video_id,
                comment=f"✅ Correct answer: {q['answer']}",
                run_at=datetime.utcnow() + timedelta(hours=24),
            )
            print("🕒 Comment scheduled")
        else:
            print("⏭ YouTube upload skipped (limit hit or DRY_RUN)")

        results["youtube"] = video_id
        results["youtube_video_path"] = yt_video_path

        shutil.rmtree(yt_frames_dir, ignore_errors=True)

        # =========================
        # FACEBOOK (CTA + BUILD ONLY)
        # =========================
        fb_frames_dir = tempfile.mkdtemp(prefix="quiz_fb_frames_")
        _copy_quiz_frames(base_frames_dir, fb_frames_dir)

        print("🎯 Rendering CTA for facebook")
        fb_cta_frames = render_cta_frames(
            frames_dir=fb_frames_dir,
            start_index=last_frame + 1,
            platform=FACEBOOK_PLATFORM,
        )
        if not isinstance(fb_cta_frames, int):
            raise RuntimeError("CTA renderer must return frame count")

        if os.path.isfile(cached_fb):
            fb_video_path = cached_fb
            print("♻️ Using cached Facebook video:", fb_video_path)
        else:
            fb_video_path = build_video(
                frames_dir=fb_frames_dir,
                output_dir="output/renders",
                fps=FPS,
                music=None,
                prefix="facebook",
            )
            print("🎬 Facebook video built:", fb_video_path)
            shutil.copy2(fb_video_path, cached_fb)
            print("✅ Cached Facebook video:", cached_fb)

        results["facebook_video_path"] = fb_video_path

        shutil.rmtree(fb_frames_dir, ignore_errors=True)

        print("✅ DONE:", results)
        return {
            "video_id": results["youtube"],
            "question": q["question"],
            "answer": q["answer"],
            "category": q["category"],
            "difficulty": q["difficulty"],
            "youtube_video_path": results["youtube_video_path"],
            "facebook_video_path": results["facebook_video_path"],
        }

    finally:
        shutil.rmtree(base_frames_dir, ignore_errors=True)
        print("🧹 Base frames cleaned:", base_frames_dir)


if __name__ == "__main__":
    print("▶ __main__ block hit")
    main()
