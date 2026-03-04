from .quiz_renderer import draw_question_frame, draw_answer_frame
from .cta_renderer import draw_cta_frame
from PIL import Image, ImageDraw, ImageFont
from ..config import FONTS_DIR
import os

WIDTH = 1080
HEIGHT = 1920


def draw_hook(frame_path, text):
    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)

    # Deep dark gradient — bold, clean
    for y in range(HEIGHT):
        r = int(8 + (15 - 8) * (y / HEIGHT))
        g = int(8 + (18 - 8) * (y / HEIGHT))
        b = int(18 + (35 - 18) * (y / HEIGHT))
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

    title_font = ImageFont.truetype(os.path.join(FONTS_DIR, "Inter-Bold.ttf"), 120)
    hook_font = ImageFont.truetype(os.path.join(FONTS_DIR, "Inter-Bold.ttf"), 70)

    # title
    draw.text(
        (WIDTH // 2, 520),
        "🧠 GENERAL KNOWLEDGE",
        fill=(255, 255, 255),
        anchor="mm",
        font=title_font,
    )

    # hook wrapped
    words = text.split()
    lines = []
    line = ""
    for w in words:
        test = (line + " " + w).strip()
        if draw.textlength(test, font=hook_font) < WIDTH * 0.8:
            line = test
        else:
            lines.append(line)
            line = w
    lines.append(line)

    y = 900
    for l in lines:
        draw.text((WIDTH // 2, y), l, fill=(255, 220, 60), anchor="mm", font=hook_font)
        y += hook_font.size + 20

    img.save(frame_path)


def render_scene(scene, frame_index, frames_dir, episode):
    """
    scene = {'type': 'q1', 'frames': 120}
    """

    t = scene["type"]

    if t == "hook":
        for i in range(scene["frames"]):
            draw_hook(f"{frames_dir}/frame_{frame_index+i:05d}.png", episode["hook"])
        return scene["frames"]

    if t.startswith("q"):
        q_index = int(t[1:]) - 1
        q = dict(episode["questions"][q_index])
        q["_episode_hook"] = episode.get("hook", "")
        return draw_question_frame(frames_dir, frame_index, q, scene["frames"])

    if t.startswith("a"):
        q_index = int(t[1:]) - 1
        return draw_answer_frame(
            frames_dir, frame_index, episode["questions"][q_index], scene["frames"]
        )

    if t == "outro":
        return draw_cta_frame(
            frames_dir, frame_index, episode["outro"], scene["frames"]
        )

    return 0
