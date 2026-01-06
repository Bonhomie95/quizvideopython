import os
import random
import shutil
import subprocess
from datetime import datetime
from typing import Any, Optional, Dict, Tuple, Union

from PIL import Image, ImageDraw, ImageFont

from .watermark import apply_watermark
from ..config import OUTPUT_DIR, FONTS_DIR, MUSIC_DIR
from ..utils.text import wrap_lines
from ..utils.wiki_images import get_cached_image, fetch_and_cache_image


# =========================================================
# VIDEO CONSTANTS
# =========================================================
W, H, FPS = 1080, 1920, 30
QUIZ_DURATION = 13


# =========================================================
# ASSETS
# =========================================================
LOGO_PATH = "assets/logo.png"
BG_DIR = "assets/backgrounds"

CATEGORY_BG_MAP = {
    "football": "football.png",
    "basketball": "basketball.png",
    "tennis": "tennis.png",
    "general": "general.png",
}


# =========================================================
# HOOK TEXT
# =========================================================
HOOK_VARIANTS = [
    "🔥 95% FAIL THIS",
    "❌ MOST PEOPLE GET THIS WRONG",
    "⚠️ DON’T BLINK",
    "🤯 ONLY GENIUSES GET THIS",
    "😅 NO GOOGLE",
    "✅ BE HONEST",
]

HOOK_EMOJI_COLORS: Dict[str, Tuple[int, int, int]] = {
    "🔥": (255, 140, 0),
    "❌": (255, 60, 60),
    "⚠️": (255, 215, 0),
}


def get_hook_color(text: str) -> Tuple[int, int, int]:
    for emoji, color in HOOK_EMOJI_COLORS.items():
        if emoji in text:
            return color
    return (255, 255, 255)


# =========================================================
# TITLE
# =========================================================
CATEGORY_EMOJIS = {
    "football": "⚽",
    "basketball": "🏀",
    "tennis": "🎾",
    "general": "🧠",
}


def generate_title(hook: str, category: str) -> str:
    emoji = CATEGORY_EMOJIS.get((category or "general").lower(), "🧠")
    return f"{emoji} {hook}"


# =========================================================
# COMMENT CTA
# =========================================================
COMMENT_CTA_VARIANTS = [
    "👇 Comment your answer",
    "👇 Don’t Google it 😅",
    "👇 Be honest",
    "👇 Only one is correct",
]


# =========================================================
# PIL RESAMPLING
# =========================================================
try:
    RESAMPLE: Any = Image.Resampling.LANCZOS
except Exception:
    RESAMPLE = Image.BICUBIC


# =========================================================
# TIMING – VERTICAL CASCADE
# =========================================================
STEP = int(0.25 * FPS)

CAT_DIFF_START = 0
HOOK_START = CAT_DIFF_START + STEP
QUESTION_START = HOOK_START + int(0.15 * FPS)
OPTIONS_START = QUESTION_START + STEP

QUESTION_SLIDE_FRAMES = int(0.5 * FPS)
OPTION_STAGGER = int(0.5 * FPS)


# =========================================================
# EASING
# =========================================================
def ease_out(t: float) -> float:
    return 1 - (1 - t) ** 3


# =========================================================
# HELPERS
# =========================================================
def abs_path(p: str) -> str:
    return os.path.abspath(p)


def load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(os.path.join(FONTS_DIR, name), size)


def load_logo() -> Optional[Image.Image]:
    if not os.path.isfile(LOGO_PATH):
        return None
    return Image.open(LOGO_PATH).convert("RGBA")


def pick_music() -> Optional[str]:
    if not os.path.isdir(MUSIC_DIR):
        return None
    tracks = [
        os.path.join(MUSIC_DIR, f)
        for f in os.listdir(MUSIC_DIR)
        if f.lower().endswith((".mp3", ".wav", ".m4a"))
    ]
    return random.choice(tracks) if tracks else None


# =========================================================
# BACKGROUND
# =========================================================
def get_background(category: Optional[str]) -> Image.Image:
    key = (category or "general").lower()
    path = os.path.join(BG_DIR, CATEGORY_BG_MAP.get(key, "general.png"))
    if not os.path.isfile(path):
        path = os.path.join(BG_DIR, "general.png")
    bg = Image.open(path).convert("RGB")
    return bg.resize((W, H), RESAMPLE)


def apply_dark_overlay(img: Image.Image) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 140))
    return Image.alpha_composite(img.convert("RGBA"), overlay)


Color = Union[str, Tuple[int, int, int]]


def draw_text_shadow(
    draw: ImageDraw.ImageDraw,
    pos: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: Color = "white",
):
    x, y = pos
    draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=fill)


# =========================================================
# QUESTION BOX
# =========================================================
def draw_question_box(img, draw, text, font, center_y: int):
    padding = 44
    lines = text.split("\n")
    box_h = len(lines) * (font.size + 10) + padding * 2
    box_w = int(W * 0.85)

    x0 = (W - box_w) // 2
    y0 = center_y - box_h // 2

    layer = Image.new("RGBA", img.size)
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle(
        (x0, y0, x0 + box_w, y0 + box_h),
        radius=26,
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


# =========================================================
# OPTIONS
# =========================================================
def fit_text(draw, text, font_path, max_size, min_size, max_width):
    for size in range(max_size, min_size - 1, -2):
        font = ImageFont.truetype(font_path, size)
        if draw.textlength(text, font=font) <= max_width:
            return font
    return ImageFont.truetype(font_path, min_size)


def preload_option_images(options):
    return {v: get_cached_image(v) or fetch_and_cache_image(v) for v in options}


# =========================================================
# MAIN RENDERER
# =========================================================
def render_quiz_frames(q: dict, frames_dir: str) -> Dict[str, Any]:
    os.makedirs(frames_dir, exist_ok=True)

    font_header = load_font("Inter-Bold.ttf", 52)
    font_hook = load_font("Inter-Bold.ttf", 60)
    font_question = load_font("Inter-Bold.ttf", 56)
    font_comment = load_font("Inter-Regular.ttf", 46)

    hook_text = random.choice(HOOK_VARIANTS)
    hook_color = get_hook_color(hook_text)
    comment_text = random.choice(COMMENT_CTA_VARIANTS)

    title = generate_title(hook_text, q.get("category", "general"))

    category_text = (q.get("category") or "general").upper()
    difficulty_text = (q.get("difficulty") or "easy").upper()

    cat_color = (180, 220, 255)
    diff_color = (255, 200, 80)

    question = wrap_lines(q["question"], 40)
    question = "\n".join(question) if isinstance(question, list) else question
    question_img_path = get_cached_image(q["question"]) or fetch_and_cache_image(
        q["question"]
    )

    options = q.get("options", [])
    option_rows = [(chr(65 + i), opt, i) for i, opt in enumerate(options)]
    option_images = preload_option_images(options)

    logo = load_logo()
    total_frames = FPS * QUIZ_DURATION
    opt_font_path = os.path.join(FONTS_DIR, "Inter-Regular.ttf")

    for frame in range(total_frames):
        img = apply_dark_overlay(get_background(q.get("category")))
        draw = ImageDraw.Draw(img)

        # HEADER
        if frame >= CAT_DIFF_START:
            t = min(1.0, (frame - CAT_DIFF_START) / STEP)
            y = int(-80 + ease_out(t) * 140)

            cat_x = W // 2 - 260
            diff_x = cat_x + int(
                draw.textlength(category_text + " • ", font=font_header)
            )

            draw_text_shadow(
                draw, (cat_x, y), category_text + " • ", font_header, fill=cat_color
            )
            draw_text_shadow(
                draw, (diff_x, y), difficulty_text, font_header, fill=diff_color
            )

        # HOOK
        if frame >= HOOK_START:
            t = min(1.0, (frame - HOOK_START) / STEP)
            x = int(-400 + ease_out(t) * (W // 2 + 400))
            draw_text_shadow(
                draw,
                (W // 2 - int(draw.textlength(hook_text, font=font_hook)) // 2, 180),
                hook_text,
                font_hook,
                fill=hook_color,
            )

        # QUESTION
        if frame >= QUESTION_START:
            t = min(1.0, (frame - QUESTION_START) / QUESTION_SLIDE_FRAMES)
            yq = int(-200 + ease_out(t) * 620)

            if question_img_path and os.path.isfile(question_img_path):
                try:
                    qi = Image.open(question_img_path).convert("RGBA")
                    qi = qi.resize((220, 220), RESAMPLE)
                    img.paste(qi, (W // 2 - 110, yq - 240), qi)
                except Exception:
                    pass

            draw_question_box(img, draw, question, font_question, yq)

        # OPTIONS
        for letter, value, idx in option_rows:
            start = OPTIONS_START + idx * OPTION_STAGGER
            if frame < start:
                continue

            t = min(1.0, (frame - start) / STEP)
            base_y = 980 + idx * 110
            y = int(-100 + ease_out(t) * base_y)

            label = f"{letter}. {value}"
            font_opt = fit_text(draw, label, opt_font_path, 44, 30, 520)

            img_path = option_images.get(value)
            if img_path and os.path.isfile(img_path):
                icon = Image.open(img_path).convert("RGBA").resize((72, 72), RESAMPLE)
                img.paste(icon, (W // 2 - 320, y), icon)

            draw_text_shadow(draw, (W // 2 - 220, y + 10), label, font_opt)

        # COMMENT CTA
        if frame >= int(6.5 * FPS):
            draw.text(
                (W // 2, 1450),
                comment_text,
                font=font_comment,
                fill="white",
                anchor="mm",
            )

        # WATERMARK
        if logo:
            img = apply_watermark(img, logo, frame, corner="top-right", opacity=0.7)

        img.convert("RGB").save(os.path.join(frames_dir, f"frame_{frame:04d}.png"))

    return {"frames": total_frames - 1, "hook": hook_text, "title": title}


# =========================================================
# VIDEO ENCODER
# =========================================================
def render_video(q: dict) -> str:
    frames_dir = abs_path("output/frames")
    os.makedirs(frames_dir, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    render_quiz_frames(q, frames_dir)

    out = abs_path(
        os.path.join(
            OUTPUT_DIR, f"quiz_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.mp4"
        )
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        os.path.join(frames_dir, "frame_%04d.png"),
    ]

    music = pick_music()
    if music:
        cmd += ["-i", abs_path(music), "-shortest", "-af", "volume=0.18"]

    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]

    subprocess.run(cmd, check=True)
    shutil.rmtree(frames_dir, ignore_errors=True)

    return out
