print("MAIN FILE LOADED")

from datetime import datetime
import os
import tempfile
import shutil
import json
import subprocess
import random

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
# HOOK SYSTEM
# Styles: challenge | shame | curiosity | dare
# Avoid dead phrases like "95% FAIL" — audiences are blind to them
# =====================================================
HOOK_TEMPLATES = [
    # CHALLENGE
    {"hook": "Bet you can't answer all 5", "style": "challenge"},
    {"hook": "Only 1 in 100 gets all 5 right", "style": "challenge"},
    {"hook": "Most adults fail question 3", "style": "challenge"},
    {"hook": "Can you score 5 out of 5?", "style": "challenge"},
    {"hook": "Your score reveals your IQ level", "style": "challenge"},
    {"hook": "5 questions. Most people fail 2.", "style": "challenge"},
    # SHAME
    {"hook": "You probably learned this in school", "style": "shame"},
    {"hook": "Things you forgot after school", "style": "shame"},
    {"hook": "Simple facts most people get wrong", "style": "shame"},
    {"hook": "Would you pass a 5th grade quiz?", "style": "shame"},
    {"hook": "Don't be embarrassed if you miss one", "style": "shame"},
    # CURIOSITY
    {"hook": "5 facts that sound fake but aren't", "style": "curiosity"},
    {"hook": "These answers will surprise you", "style": "curiosity"},
    {"hook": "Things most people never knew", "style": "curiosity"},
    {"hook": "How many can you actually get right?", "style": "curiosity"},
    {"hook": "General knowledge that schools skip", "style": "curiosity"},
    # DARE
    {"hook": "Comment your score below", "style": "dare"},
    {"hook": "No Googling. Be honest.", "style": "dare"},
    {"hook": "Tag someone who thinks they're smart", "style": "dare"},
    {"hook": "Smarter than average? Prove it.", "style": "dare"},
]


def pick_hook() -> dict:
    return random.choice(HOOK_TEMPLATES)


# =====================================================
# YOUTUBE TITLE — tested patterns for Shorts discovery
# =====================================================
TITLE_PATTERNS = [
    lambda hook: f"{hook} \U0001f9e0 General Knowledge Quiz",
    lambda hook: f"Quiz: {hook}",
    lambda hook: f"{hook} | How Many Can YOU Get?",
    lambda hook: f"5-Question Quiz \u2014 {hook}",
    lambda hook: f"General Knowledge: {hook}",
    lambda hook: f"{hook} #shorts",
]

HASHTAGS = (
    "#shorts #quiz #trivia #generalknowledge "
    "#didyouknow #facts #brainteaser #howsmart"
)


def build_yt_title(hook: str) -> str:
    pattern = random.choice(TITLE_PATTERNS)
    return pattern(hook)


def build_yt_description(episode: dict, hook: str) -> str:
    lines = [
        hook,
        "",
        "Can you answer all 5? Comment your score \U0001f447",
        "",
        "QUESTIONS:",
    ]
    for i, q in enumerate(episode["questions"], 1):
        lines.append(f"  {i}. {q['question']}")
    lines.extend([
        "",
        "Answers in pinned comment.",
        "",
        HASHTAGS,
    ])
    return "\n".join(lines)


# =====================================================
# MAIN
# =====================================================
def main():
    print("main() entered")

    episode = build_episode()
    hook_data = pick_hook()
    episode["hook"] = hook_data["hook"]

    print("\nEPISODE GENERATED")
    print("Hook:", episode["hook"], "| Style:", hook_data["style"])
    print("Outro:", episode["outro"])
    for i, q in enumerate(episode["questions"], 1):
        print(f"{i}. [{q['difficulty'].upper()}] {q['question']}")

    print("\nGenerating narration...")
    audio_files = generate_episode_audio(episode)
    print("Building master timeline...")
    master_audio, timestamps = build_timeline(audio_files)

    print("\nConverting timeline to scenes...")
    scenes = group_timeline(timestamps)

    frames_dir = tempfile.mkdtemp(prefix="episode_frames_")
    final_video = None

    try:
        frame_index = 0
        print("\nRendering video from scenes...")
        for scene in scenes:
            used = render_scene(scene, frame_index, frames_dir, episode)
            frame_index += used
            print(f"  Rendered {scene['type']} -> {used} frames")

        print("Total frames:", frame_index)
        print("Building silent video...")
        video_path = build_video(
            frames_dir=frames_dir,
            output_dir="output/renders",
            fps=FPS,
            music=None,
            prefix="episode",
        )

        print("Attaching narration audio...")
        final_video = video_path.replace(".mp4", "_final.mp4")
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", master_audio,
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                final_video,
            ],
            check=True,
        )
        print("Episode video ready:", final_video)

    finally:
        shutil.rmtree(frames_dir, ignore_errors=True)
        print("Temp frames removed")

    if not final_video:
        print("Video not created — skipping upload")
        return None

    title = build_yt_title(episode["hook"])
    description = build_yt_description(episode, episode["hook"])
    print("Title:", title)

    if DRY_RUN:
        print("DRY RUN — skipping upload")
        return final_video

    print("Uploading to YouTube...")
    video_id = upload_short(final_video, title, description)

    if video_id:
        print("Posting pinned answers comment...")
        answers = "\n".join(
            f"{i+1}. {q['answer']}" for i, q in enumerate(episode["questions"])
        )
        post_comment(video_id, f"ANSWERS:\n{answers}\n\nComment your score below!")

    return final_video


if __name__ == "__main__":
    main()
