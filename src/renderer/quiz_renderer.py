import os
import random
import shutil
import subprocess
from datetime import datetime
from typing import Any, Optional, Tuple
from .watermark import apply_watermark

from PIL import Image, ImageDraw, ImageFont, ImageEnhance

from ..config import OUTPUT_DIR, FONTS_DIR, MUSIC_DIR
from ..utils.text import wrap_lines


W, H, FPS = 1080, 1920, 30
DURATION = 13


LOGO_PATH = "assets/logo.png"


def load_logo():
    if not LOGO_PATH or not os.path.isfile(LOGO_PATH):
        return None
    return Image.open(LOGO_PATH).convert("RGBA")


def log(*args):
    print("[quiz-renderer]", *args)


def abs_path(p: str) -> str:
    return os.path.abspath(p)


# Pillow resampling compatibility (kills LANCZOS warning forever)
try:
    RESAMPLE: Any = Image.Resampling.LANCZOS
except Exception:
    RESAMPLE = getattr(Image, "LANCZOS", Image.BICUBIC)


def pick_music() -> Optional[str]:
    if not os.path.isdir(MUSIC_DIR):
        return None
    tracks = [
        os.path.join(MUSIC_DIR, f)
        for f in os.listdir(MUSIC_DIR)
        if f.lower().endswith((".mp3", ".wav", ".m4a"))
    ]
    return random.choice(tracks) if tracks else None


W, H, FPS = 1080, 1920, 30
QUIZ_DURATION = 13  # seconds


def load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(os.path.join(FONTS_DIR, name), size)


def render_quiz_frames(q: dict, frames_dir: str) -> int:
    os.makedirs(frames_dir, exist_ok=True)

    font_small = load_font("Inter-Regular.ttf", 38)
    font_big = load_font("Inter-Bold.ttf", 54)
    font_opt = load_font("Inter-Regular.ttf", 44)

    category = q["category"].replace("_", " ").title()
    difficulty = q["difficulty"].title()

    question = wrap_lines(q["question"], 40)
    if isinstance(question, list):  # safety if wrap_lines returns list
        question = "\n".join(question)

    A, B, C, D = q["options"]

    logo = load_logo()
    total_frames = FPS * QUIZ_DURATION

    for frame in range(total_frames):
        img = Image.new("RGB", (W, H), (8, 10, 18))
        draw = ImageDraw.Draw(img)

        # Header
        if frame >= int(0.8 * FPS):
            text = f"{category} - {difficulty}"
            tw = int(draw.textlength(text, font=font_small))
            draw.text(((W - tw) // 2, 260), text, fill="white", font=font_small)

        # Question
        if frame >= int(1.8 * FPS):
            draw.multiline_text(
                (W // 2, 520),
                question,
                fill="white",
                font=font_big,
                anchor="ma",
                align="center",
                spacing=10,
            )

        # Options
        options = [("A. " + A, 0), ("B. " + B, 1), ("C. " + C, 2), ("D. " + D, 3)]
        y0 = 980

        for opt_text, idx in options:
            start = int((4 + idx * 0.9) * FPS)
            if frame >= start:
                tw = int(draw.textlength(opt_text, font=font_opt))
                draw.text(
                    ((W - tw) // 2, y0 + idx * 110),
                    opt_text,
                    fill="white",
                    font=font_opt,
                )

        # ✅ Watermark LAST (so no draw-pointer bug)
        if logo:
            img = apply_watermark(
                base=img.convert("RGBA"),
                logo=logo,
                frame=frame,
                corner="top-right",
                opacity=0.7,
            ).convert("RGB")

        img.save(os.path.join(frames_dir, f"frame_{frame:04d}.png"))

    return total_frames - 1


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def draw_gradient(draw: ImageDraw.ImageDraw, top, bottom):
    for y in range(H):
        t = y / (H - 1)
        r = lerp(top[0], bottom[0], t)
        g = lerp(top[1], bottom[1], t)
        b = lerp(top[2], bottom[2], t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))


def safe_load_rgba(
    path: str, size: Optional[Tuple[int, int]] = None, opacity: Optional[float] = None
) -> Optional[Image.Image]:
    path = abs_path(path)
    if not os.path.isfile(path):
        return None

    img = Image.open(path).convert("RGBA")
    if size:
        img = img.resize(size, RESAMPLE)

    if opacity is not None:
        alpha = img.getchannel("A")
        alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
        img.putalpha(alpha)

    return img


def render_video(q: dict) -> str:
    frames_dir = abs_path("output/frames")
    os.makedirs(frames_dir, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    music = pick_music()

    gradients = [
        ((5, 5, 7), (20, 20, 40)),
        ((10, 10, 20), (5, 5, 7)),
        ((15, 5, 30), (5, 5, 15)),
    ]
    top_color, bottom_color = random.choice(gradients)

    category = q["category"].replace("_", " ").title()
    difficulty = q["difficulty"].title()
    question = wrap_lines(q["question"], 40)
    A, B, C, D = q["options"]

    font_small = load_font("Inter-Regular.ttf", 38)
    font_big = load_font("Inter-Bold.ttf", 54)
    font_opt = load_font("Inter-Regular.ttf", 44)

    total_frames = FPS * DURATION

    def slide_y(base: int, frame: int, start: int, dist: int = 60) -> int:
        if frame < start:
            return base + dist
        t = min(1.0, (frame - start) / FPS)
        eased = 1 - (1 - t) ** 3
        return int(base + (1 - eased) * dist)

    def slide_x(base: int, frame: int, start: int, offset: int) -> int:
        if frame < start:
            return base + offset
        t = min(1.0, (frame - start) / FPS)
        eased = 1 - (1 - t) ** 3
        return int(base + (1 - eased) * offset)

    for frame in range(total_frames):
        img = Image.new("RGB", (W, H))
        draw = ImageDraw.Draw(img)

        draw_gradient(draw, top_color, bottom_color)

        if frame >= int(0.8 * FPS):
            y = slide_y(260, frame, int(0.8 * FPS))
            text = f"{category} - {difficulty}"
            tw = int(draw.textlength(text, font=font_small))
            draw.text(((W - tw) // 2, y), text, font=font_small, fill="white")

        if frame >= int(1.8 * FPS):
            y = slide_y(520, frame, int(1.8 * FPS))
            draw.multiline_text(
                (W // 2, y),
                question,
                font=font_big,
                fill="white",
                anchor="ma",
                align="center",
                spacing=10,
            )

        options = [
            ("A. " + A, 0, -80),
            ("B. " + B, 1, 80),
            ("C. " + C, 2, -80),
            ("D. " + D, 3, 80),
        ]
        y0 = 980

        for text, i, offset in options:
            start = int((4 + i * 0.9) * FPS)
            if frame >= start:
                y = slide_y(y0 + i * 110, frame, start)
                tw = int(draw.textlength(text, font=font_opt))
                x = slide_x((W - tw) // 2, frame, start, offset)
                draw.text((x, y), text, font=font_opt, fill="white")

        img.save(os.path.join(frames_dir, f"frame_{frame:04d}.png"))

    out = abs_path(
        os.path.join(OUTPUT_DIR, f"quiz_{datetime.utcnow():%Y%m%d_%H%M%S}.mp4")
    )

    cmd = ["ffmpeg", "-y", "-framerate", str(FPS), "-i", f"{frames_dir}/frame_%04d.png"]
    if music:
        cmd += ["-i", abs_path(music), "-shortest", "-af", "volume=0.18"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]

    subprocess.run(cmd, check=True)
    shutil.rmtree(frames_dir, ignore_errors=True)

    return out
