import os
import random
import shutil
import subprocess
from datetime import datetime
from typing import Any, Optional

from PIL import Image, ImageDraw, ImageFont

from .watermark import apply_watermark
from ..config import OUTPUT_DIR, FONTS_DIR, MUSIC_DIR
from ..utils.text import wrap_lines
from ..utils.wiki_images import get_cached_image, fetch_and_cache_image

# =========================
# CONSTANTS
# =========================
W, H, FPS = 1080, 1920, 30
QUIZ_DURATION = 13  # seconds

LOGO_PATH = "assets/logo.png"
BG_DIR = "assets/backgrounds"

CATEGORY_BG_MAP = {
    "football": "football.png",
    "basketball": "basketball.png",
    "tennis": "tennis.png",
    "general": "general.png",
}

# Pillow resampling compatibility
try:
    RESAMPLE: Any = Image.Resampling.LANCZOS
except Exception:
    RESAMPLE = getattr(Image, "LANCZOS", Image.BICUBIC)


# =========================
# HELPERS
# =========================
def log(*args):
    print("[quiz-renderer]", *args)


def abs_path(p: str) -> str:
    return os.path.abspath(p)


def load_logo() -> Optional[Image.Image]:
    if not LOGO_PATH or not os.path.isfile(LOGO_PATH):
        return None
    return Image.open(LOGO_PATH).convert("RGBA")


def load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(os.path.join(FONTS_DIR, name), size)


def pick_music() -> Optional[str]:
    if not os.path.isdir(MUSIC_DIR):
        return None
    tracks = [
        os.path.join(MUSIC_DIR, f)
        for f in os.listdir(MUSIC_DIR)
        if f.lower().endswith((".mp3", ".wav", ".m4a"))
    ]
    return random.choice(tracks) if tracks else None


# =========================
# VISUAL LAYERS
# =========================
def get_background(category: Optional[str]) -> Image.Image:
    key = (category or "general").lower()
    filename = CATEGORY_BG_MAP.get(key, CATEGORY_BG_MAP["general"])
    path = os.path.join(BG_DIR, filename)

    if not os.path.isfile(path):
        path = os.path.join(BG_DIR, "general.png")

    bg = Image.open(path).convert("RGB")
    if bg.size != (W, H):
        bg = bg.resize((W, H), RESAMPLE)

    return bg


def apply_dark_overlay(img: Image.Image, opacity: float = 0.45) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, int(255 * opacity)))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def draw_text_shadow(
    draw: ImageDraw.ImageDraw,
    pos: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill="white",
    shadow_color=(0, 0, 0),
    offset=(2, 2),
):
    x, y = pos
    draw.text((x + offset[0], y + offset[1]), text, font=font, fill=shadow_color)
    draw.text((x, y), text, font=font, fill=fill)


def draw_question_box(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    center_y: int,
):
    padding = 44
    radius = 26
    lines = text.split("\n")
    line_h = font.size + 10
    box_h = len(lines) * line_h + padding * 2
    box_w = int(W * 0.9)

    x0 = (W - box_w) // 2
    y0 = center_y - box_h // 2
    x1 = x0 + box_w
    y1 = y0 + box_h

    layer = Image.new("RGBA", img.size)
    d = ImageDraw.Draw(layer)

    d.rounded_rectangle(
        (x0, y0, x1, y1),
        radius=radius,
        fill=(0, 0, 0, 150),
    )

    img.alpha_composite(layer)

    draw.multiline_text(
        (W // 2, center_y),
        text,
        font=font,
        fill="white",
        anchor="ma",
        align="center",
        spacing=10,
    )


def draw_option_strip(img: Image.Image, y: int, height: int = 90):
    strip = Image.new("RGBA", (W, height), (0, 0, 0, 130))
    img.alpha_composite(strip, (0, y))


# =========================
# TEXT UTILS
# =========================
def fit_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: str,
    max_size: int,
    min_size: int,
    max_width: int,
):
    for size in range(max_size, min_size - 1, -2):
        font = ImageFont.truetype(font_path, size)
        if draw.textlength(text, font=font) <= max_width:
            return font
    return ImageFont.truetype(font_path, min_size)


def preload_option_images(options: list[str]) -> dict[str, str | None]:
    images: dict[str, str | None] = {}
    for value in options:
        path = get_cached_image(value)
        if not path:
            path = fetch_and_cache_image(value)
        images[value] = path
    return images


# =========================
# MAIN RENDERER
# =========================
def render_quiz_frames(q: dict, frames_dir: str) -> int:
    os.makedirs(frames_dir, exist_ok=True)

    font_small = load_font("Inter-Regular.ttf", 38)
    font_big = load_font("Inter-Bold.ttf", 56)

    category_label = (q.get("category") or "general").replace("_", " ").title()
    difficulty_label = (q.get("difficulty") or "easy").title()

    question = wrap_lines(q["question"], 40)
    if isinstance(question, list):
        question = "\n".join(question)

    options = q["options"]
    option_rows = [(chr(65 + i), opt, i) for i, opt in enumerate(options)]

    logo = load_logo()
    option_images = preload_option_images(options)

    # layout
    y_header = 260
    y_question = 520
    y0 = 980

    img_size = 72
    img_x = W // 2 - 320
    text_x = img_x + img_size + 22
    max_text_width = 520
    opt_font_path = os.path.join(FONTS_DIR, "Inter-Regular.ttf")

    total_frames = FPS * QUIZ_DURATION

    for frame in range(total_frames):
        img = get_background(q.get("category"))
        img = apply_dark_overlay(img)
        img = img.convert("RGBA")
        draw = ImageDraw.Draw(img)

        # header
        if frame >= int(0.8 * FPS):
            header = f"{category_label} • {difficulty_label}"
            tw = int(draw.textlength(header, font=font_small))
            draw_text_shadow(
                draw,
                ((W - tw) // 2, y_header),
                header,
                font_small,
            )

        # question
        if frame >= int(1.8 * FPS):
            draw_question_box(
                img,
                draw,
                question,
                font_big,
                center_y=y_question,
            )

        # options
        for letter, value, idx in option_rows:
            start = int((4 + idx * 0.9) * FPS)
            if frame < start:
                continue

            y = y0 + idx * 110
            draw_option_strip(img, y - 8)

            label = f"{letter}. {value}"
            font_opt = fit_text(
                draw,
                label,
                opt_font_path,
                max_size=44,
                min_size=30,
                max_width=max_text_width,
            )

            opt_img_path = option_images.get(value)
            if opt_img_path:
                try:
                    opt_img = Image.open(opt_img_path).convert("RGBA")
                    opt_img = opt_img.resize((img_size, img_size), RESAMPLE)
                    img.paste(opt_img, (img_x, y), opt_img)
                except Exception:
                    pass

            text_y = int(y + (img_size - font_opt.size) // 2)
            draw_text_shadow(
                draw,
                (text_x, text_y),
                label,
                font_opt,
            )

        # watermark
        if logo:
            img = apply_watermark(
                base=img,
                logo=logo,
                frame=frame,
                corner="top-right",
                opacity=0.7,
            )

        img.convert("RGB").save(os.path.join(frames_dir, f"frame_{frame:04d}.png"))

    return total_frames - 1


# =========================
# OPTIONAL STANDALONE VIDEO
# =========================
def render_video(q: dict) -> str:
    frames_dir = abs_path("output/frames")
    os.makedirs(frames_dir, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    render_quiz_frames(q, frames_dir)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out = abs_path(os.path.join(OUTPUT_DIR, f"quiz_{ts}.mp4"))

    frames_input = os.path.join(frames_dir, "frame_%04d.png")
    cmd = ["ffmpeg", "-y", "-framerate", str(FPS), "-i", frames_input]

    music = pick_music()
    if music:
        cmd += ["-i", abs_path(music), "-shortest", "-af", "volume=0.18"]

    cmd += [
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        out,
    ]

    log("Encoding…")
    log("FFmpeg cmd:", " ".join(cmd))

    try:
        subprocess.run(cmd, check=True)
    finally:
        shutil.rmtree(frames_dir, ignore_errors=True)

    log("Video created:", out)
    return out
