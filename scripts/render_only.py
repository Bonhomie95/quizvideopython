from ..src.picker import pick_question
from ..src.renderer.quiz_renderer import render_quiz_frames
from ..src.renderer.video_builder import build_video
import tempfile
import os

FPS = 30

def run():
    q = pick_question()
    frames_dir = tempfile.mkdtemp(prefix="quiz_preview_")

    last_frame = render_quiz_frames(q, frames_dir)
    print("Frames up to:", last_frame)

    out = build_video(
        frames_dir=frames_dir,
        output_dir="output/renders",
        fps=FPS,
        music=None,
        prefix="preview",
    )
    print("✅ Preview video:", os.path.abspath(out))

if __name__ == "__main__":
    run()
