print("🔥 MAIN FILE LOADED")

from datetime import datetime
import os
import tempfile
import shutil
import hashlib
import json
import subprocess

from .picker_episode import build_episode
from .audio.narrator import generate_episode_audio
from .audio.timeline import build_timeline
from .renderer.scene_renderer import render_scene
from .renderer.timeline_renderer import group_timeline
from .renderer.video_builder import build_video

from .youtube_uploader import upload_short, post_comment
from .config import DRY_RUN, CACHE_DIR

FPS = 30

# =====================================================
# HASHTAGS
# =====================================================
YT_HASHTAGS = (
    "#shorts #quiz #trivia #brainchallenge "
    "#canYouAnswer #noGoogle #beHonest #thinkFast #viral"
)


# =====================================================
# YOUTUBE META
# =====================================================
def build_yt_title(hook: str) -> str:
    return f"{hook} | 5 Question Quiz"


def build_yt_description(episode: dict, hook: str) -> str:
    lines = [hook, "", "🧠 QUESTIONS:"]

    for i, q in enumerate(episode["questions"], 1):
        lines.append(f"{i}. {q['question']}")

    lines.append("")
    lines.append("👇 Comment how many you got right!")
    lines.append("")
    lines.append(YT_HASHTAGS)

    return "\n".join(lines)


# =====================================================
# MAIN
# =====================================================
def main():
    print("🚀 main() entered")

    # =========================
    # BUILD EPISODE
    # =========================
    episode = build_episode()

    print("\n🎬 EPISODE GENERATED")
    print("Hook:", episode["hook"])
    print("Outro:", episode["outro"])

    for i, q in enumerate(episode["questions"], 1):
        print(f"{i}. [{q['difficulty'].upper()}] {q['question']}")

    # =========================
    # AUDIO GENERATION
    # =========================
    print("\n🔊 Generating narration...")
    audio_files = generate_episode_audio(episode)

    print("🎬 Building master timeline...")
    master_audio, timestamps = build_timeline(audio_files)

    # =========================
    # SCENES
    # =========================
    print("\n🎞 Converting timeline to scenes...")
    scenes = group_timeline(timestamps)

    # =========================
    # RENDER VIDEO
    # =========================
    frames_dir = tempfile.mkdtemp(prefix="episode_frames_")
    final_video = None

    try:
        frame_index = 0

        print("\n🎨 Rendering video from scenes...")
        for scene in scenes:
            used = render_scene(scene, frame_index, frames_dir, episode)
            frame_index += used
            print(f"Rendered {scene['type']} → {used} frames")

        print("🧩 Total frames:", frame_index)

        print("🎬 Building silent video...")
        video_path = build_video(
            frames_dir=frames_dir,
            output_dir="output/renders",
            fps=FPS,
            music=None,
            prefix="episode",
        )

        print("🎤 Attaching narration audio...")
        final_video = video_path.replace(".mp4", "_final.mp4")

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                video_path,
                "-i",
                master_audio,
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                final_video,
            ],
            check=True,
        )

        print("✅ Episode video ready:", final_video)

    finally:
        shutil.rmtree(frames_dir, ignore_errors=True)
        print("🧹 Temp frames removed")

    # =========================
    # UPLOAD TO YOUTUBE
    # =========================
    if not final_video:
        print("❌ Video not created — skipping upload")
        return None

    title = build_yt_title(episode["hook"])
    description = build_yt_description(episode, episode["hook"])

    if DRY_RUN:
        print("🧪 DRY RUN — skipping upload")
        return final_video

    print("📤 Uploading to YouTube...")
    video_id = upload_short(final_video, title, description)

    if video_id:
        print("🗨 Posting answers comment...")

        answers = "\n".join(
            f"{i+1}. {q['answer']}" for i, q in enumerate(episode["questions"])
        )

        post_comment(video_id, f"✅ Answers:\n{answers}")

    return final_video


if __name__ == "__main__":
    print("▶ __main__ block hit")
    main()
