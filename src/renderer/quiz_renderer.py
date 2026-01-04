import os
import random
import shutil
import subprocess
from datetime import datetime
from typing import Any, Optional, Dict, Tuple

from PIL import Image, ImageDraw, ImageFont

from .watermark import apply_watermark
from ..config import OUTPUT_DIR, FONTS_DIR, MUSIC_DIR
from ..utils.text import wrap_lines
from ..utils.wiki_images import get_cached_image, fetch_and_cache_image


# =========================================================
# VIDEO CONSTANTS
# =========================================================
W, H, FPS = 1080, 1920, 30
QUIZ_DURATION = 13  # seconds


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
# HOOK TEXT (SCROLL STOPPER)
# =========================================================
HOOK_VARIANTS = [
    "🔥 95% FAIL THIS, ARE YOU PART OF THE 5%?",
    "❌ MOST PEOPLE GET THIS WRONG",
    "⚠️ DON’T BLINK OR YOU WILL MISS IT",
    "🤯 ONLY GENIUSES GET THIS",
    "😅 NO GOOGLE HERE ANSWER CANDIDLY",
    "✅ BE HONEST, CAN YOU ANSWER THIS",
]


# =========================================================
# HOOK EMOJI COLOR MAP
# (Color-map emoji types: ❌ red, ⚠️ yellow, 🔥 orange)
# =========================================================
HOOK_EMOJI_COLORS: Dict[str, Tuple[int, int, int]] = {
    "🔥": (255, 140, 0),  # orange
    "❌": (255, 60, 60),  # red
    "⚠️": (255, 215, 0),  # yellow
}


def get_hook_color(text: str) -> Tuple[int, int, int]:
    """Detect the hook emoji and return its color; fallback is white."""
    for emoji, color in HOOK_EMOJI_COLORS.items():
        if emoji in text:
            return color
    return (255, 255, 255)


# =========================================================
# TITLE GENERATION
# =========================================================
TITLE_TEMPLATES = [
    "{hook} 🔥",
    "{hook} ❌ Most people fail",
    "{hook} ✅ Can you?",
    "{hook} 🤯 Be honest",
    "{hook} ⚠️ Don’t guess",
]

CATEGORY_EMOJIS = {
    "football": "⚽",
    "basketball": "🏀",
    "tennis": "🎾",
    "general": "🧠",
}


def generate_title(hook: str, category: str) -> str:
    """Generate a short viral title from hook + category emoji."""
    emoji = CATEGORY_EMOJIS.get((category or "general").lower(), "🧠")
    template = random.choice(TITLE_TEMPLATES)
    return f"{emoji} {template.format(hook=hook)}"


# =========================================================
# COMMENT CTA ROTATION
# =========================================================
COMMENT_CTA_VARIANTS = [
    "👇 Comment your answer",
    "👇 Be honest — what’s your answer?",
    "👇 Don’t Google it 😅",
    "👇 Only one is correct",
    "👇 Answer fast ⏳",
    "👇 Prove you know this",
]


# =========================================================
# PIL RESAMPLING (compat across Pillow versions)
# =========================================================
try:
    RESAMPLE: Any = Image.Resampling.LANCZOS
except Exception:
    RESAMPLE = getattr(Image, "LANCZOS", Image.BICUBIC)


# =========================================================
# ANIMATION TIMING
# =========================================================
IMPACT_FRAMES = int(0.38 * FPS)
SETTLE_FRAMES = int(0.26 * FPS)
TOTAL_ANIM = IMPACT_FRAMES + SETTLE_FRAMES

FONT_BIG = 96
FONT_FINAL_MAX = 44
FONT_FINAL_MIN = 30

CENTER_X = W // 2
LEFT_START_X = -140
RIGHT_START_X = W + 140

QUESTION_SLIDE_FRAMES = int(0.55 * FPS)


# =========================================================
# EASING
# =========================================================
def ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3


def ease_in_out(t: float) -> float:
    return t * t * (3 - 2 * t)


def micro_bounce(t: float) -> float:
    return t if t <= 0.85 else t + 0.06 * (1 - t)


# =========================================================
# HELPERS
# =========================================================
def abs_path(p: str) -> str:
    return os.path.abspath(p)


def load_logo() -> Optional[Image.Image]:
    if not os.path.isfile(LOGO_PATH):
        return None
    return Image.open(LOGO_PATH).convert("RGBA")


def load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(os.path.join(FONTS_DIR, name), size)


def pick_music() -> Optional[str]:
    """Pick a random music track (or None if folder empty/missing)."""
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
    filename = CATEGORY_BG_MAP.get(key, "general.png")
    path = os.path.join(BG_DIR, filename)
    if not os.path.isfile(path):
        path = os.path.join(BG_DIR, "general.png")

    bg = Image.open(path).convert("RGB")
    if bg.size != (W, H):
        bg = bg.resize((W, H), RESAMPLE)
    return bg


def apply_dark_overlay(img: Image.Image, opacity: float = 0.45) -> Image.Image:
    """Darken background to improve text readability."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, int(255 * opacity)))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def draw_text_shadow(draw: ImageDraw.ImageDraw, pos, text: str, font, fill="white"):
    """Readable text: soft shadow + main text."""
    x, y = pos
    draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=fill)


# =========================================================
# QUESTION BOX (EDIT BACKGROUND HERE)
# =========================================================
def draw_question_box(
    img: Image.Image, draw: ImageDraw.ImageDraw, text: str, font, center_y: int
):
    """
    QUESTION BACKGROUND AREA ✅
    - box_w controls width
    - fill alpha controls transparency
    """
    padding = 44
    radius = 26

    lines = text.split("\n")
    box_h = len(lines) * (font.size + 10) + padding * 2

    box_w = int(W * 0.85)  # 👈 EDIT QUESTION BOX WIDTH HERE (0.80–0.90)

    x0 = (W - box_w) // 2
    y0 = center_y - box_h // 2
    x1 = x0 + box_w
    y1 = y0 + box_h

    layer = Image.new("RGBA", img.size)
    d = ImageDraw.Draw(layer)

    # 👇 EDIT QUESTION BOX BACKGROUND COLOR/ALPHA HERE
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


# =========================================================
# OPTION BACKGROUND (EDIT HERE)
# =========================================================
def draw_option_strip(img: Image.Image, y: int):
    """
    OPTIONS BACKGROUND AREA ✅
    - height = 90
    - alpha controls transparency
    """
    # 👇 EDIT OPTION STRIP BACKGROUND HERE
    strip = Image.new("RGBA", (W, 90), (0, 0, 0, 130))
    img.alpha_composite(strip, (0, y))


def fit_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: str,
    max_size: int,
    min_size: int,
    max_width: int,
):
    """Shrink font until text fits max_width."""
    for size in range(max_size, min_size - 1, -2):
        font = ImageFont.truetype(font_path, size)
        if draw.textlength(text, font=font) <= max_width:
            return font
    return ImageFont.truetype(font_path, min_size)


def preload_option_images(options):
    """Preload/cache option images; may return None values."""
    images = {}
    for v in options:
        images[v] = get_cached_image(v) or fetch_and_cache_image(v)
    return images


# =========================================================
# MAIN RENDERER
# =========================================================
def render_quiz_frames(q: dict, frames_dir: str) -> Dict[str, Any]:
    """
    Returns:
      {
        "frames": <last_frame_index>,
        "hook": <hook_text>,
        "title": <generated_title>
      }
    """
    os.makedirs(frames_dir, exist_ok=True)

    # ---------- Fonts ----------
    font_small = load_font("Inter-Regular.ttf", 38)
    font_question = load_font("Inter-Bold.ttf", 56)
    font_comment = load_font("Inter-Regular.ttf", 48)

    # ---------- Rotations ----------
    hook_text = random.choice(HOOK_VARIANTS)
    hook_color = get_hook_color(hook_text)
    comment_text = random.choice(COMMENT_CTA_VARIANTS)

    # Title for uploader usage/logging
    title = generate_title(hook_text, q.get("category") or "general")

    # ---------- Labels ----------
    category_label = (q.get("category") or "general").title()
    difficulty_label = (q.get("difficulty") or "easy").title()

    # ---------- Question formatting ----------
    question = wrap_lines(q["question"], 40)
    question = "\n".join(question) if isinstance(question, list) else question

    # ---------- Options ----------
    options = q["options"]
    option_rows = [(chr(65 + i), opt, i) for i, opt in enumerate(options)]
    option_images = preload_option_images(options)

    # ---------- Layout ----------
    y_header = 260
    y_question_final = 520
    y_options_start = 980
    y_comment = 1450

    img_size = 72
    final_img_x = W // 2 - 320
    final_text_x = final_img_x + img_size + 22
    meet_img_x = CENTER_X - img_size - 12
    meet_text_x = CENTER_X + 12

    opt_font_path = os.path.join(FONTS_DIR, "Inter-Regular.ttf")
    max_text_width = 520

    logo = load_logo()

    total_frames = FPS * QUIZ_DURATION

    for frame in range(total_frames):
        # ---------- Base frame background ----------
        img = apply_dark_overlay(get_background(q.get("category"))).convert("RGBA")
        draw = ImageDraw.Draw(img)

        # =================================================
        # 1) HOOK (FIRST 0.8s)
        # =================================================
        if frame < int(2.0 * FPS):
            t = frame / (2.0 * FPS)
            scale = 1.25 - 0.25 * t
            alpha = int(255 * (0.6 + 0.4 * t))

            hook_font = load_font("Inter-Bold.ttf", max(10, int(50 * scale)))
            tw = int(draw.textlength(hook_text, font=hook_font))

            overlay = Image.new("RGBA", img.size)
            d = ImageDraw.Draw(overlay)
            d.text(
                ((W - tw) // 2, H // 2 - 40),
                hook_text,
                font=hook_font,
                fill=(hook_color[0], hook_color[1], hook_color[2], alpha),
            )
            img = Image.alpha_composite(img, overlay)

        # =================================================
        # 2) HEADER (after 0.9s)
        # =================================================
        if frame >= int(2.1 * FPS):
            header = f"{category_label} • {difficulty_label}"
            tw = int(draw.textlength(header, font=font_small))
            draw_text_shadow(
                draw, ((W - tw) // 2, y_header), header, font_small, fill="white"
            )

        # =================================================
        # 3) QUESTION DROP (after 1.6s)
        # =================================================
        if frame >= int(1.6 * FPS):
            qf = frame - int(1.6 * FPS)
            t = min(1.0, qf / max(1, QUESTION_SLIDE_FRAMES))
            yq = int((y_question_final - 160) * (1 - t) + y_question_final * t)
            draw_question_box(img, draw, question, font_question, yq)

        # =================================================
        # 4) OPTIONS (staggered entrance)
        # =================================================
        for letter, value, idx in option_rows:
            start = int((3.6 + idx * 0.9) * FPS)
            if frame < start:
                continue

            anim_f = frame - start
            base_y = y_options_start + idx * 110

            # option strip background behind each option
            draw_option_strip(img, base_y - 8)

            label = f"{letter}. {value}"

            # ---- animated entrance then settle ----
            if anim_f < TOTAL_ANIM:
                if anim_f < IMPACT_FRAMES:
                    tt = micro_bounce(ease_out_cubic(anim_f / max(1, IMPACT_FRAMES)))
                    img_x = int(LEFT_START_X + tt * (meet_img_x - LEFT_START_X))
                    text_x = int(RIGHT_START_X - tt * (RIGHT_START_X - meet_text_x))
                    font_size = FONT_BIG
                    yy = base_y - 38
                else:
                    tt = ease_in_out((anim_f - IMPACT_FRAMES) / max(1, SETTLE_FRAMES))
                    img_x = int(meet_img_x * (1 - tt) + final_img_x * tt)
                    text_x = int(meet_text_x * (1 - tt) + final_text_x * tt)
                    font_size = int(FONT_BIG * (1 - tt) + FONT_FINAL_MAX * tt)
                    yy = int((base_y - 38) * (1 - tt) + base_y * tt)

                font_opt = ImageFont.truetype(opt_font_path, max(10, font_size))
            else:
                img_x = final_img_x
                text_x = final_text_x
                yy = base_y
                font_opt = fit_text(
                    draw,
                    label,
                    opt_font_path,
                    FONT_FINAL_MAX,
                    FONT_FINAL_MIN,
                    max_text_width,
                )

            # ---- Option icon (SAFE: img_path can be None) ----
            img_path = option_images.get(value)  # ✅ ALWAYS DEFINE BEFORE USING
            if isinstance(img_path, str) and os.path.isfile(img_path):
                try:
                    opt_img = Image.open(img_path).convert("RGBA")
                    opt_img = opt_img.resize((img_size, img_size), RESAMPLE)
                    img.paste(opt_img, (img_x, yy), opt_img)
                except Exception:
                    pass

            # ---- Option label text ----
            draw_text_shadow(draw, (text_x, yy + 10), label, font_opt, fill="white")

        # =================================================
        # 5) COMMENT CTA (after 6.2s)
        # =================================================
        if frame >= int(6.2 * FPS):
            alpha = min(255, int((frame - int(6.2 * FPS)) * 18))
            overlay = Image.new("RGBA", img.size)
            d2 = ImageDraw.Draw(overlay)
            d2.text(
                (W // 2, y_comment),
                comment_text,
                font=font_comment,
                fill=(255, 255, 255, alpha),
                anchor="mm",
            )
            img = Image.alpha_composite(img, overlay)

        # =================================================
        # 6) WATERMARK (always on top)
        # =================================================
        if logo:
            img = apply_watermark(img, logo, frame, corner="top-right", opacity=0.7)

        # ---------- Save frame ----------
        img.convert("RGB").save(os.path.join(frames_dir, f"frame_{frame:04d}.png"))

    return {"frames": total_frames - 1, "hook": hook_text, "title": title}


# =========================================================
# VIDEO ENCODER
# =========================================================
def render_video(q: dict) -> str:
    """
    Local render helper (if you run renderer directly).
    Your main pipeline uses build_video() — this is optional.
    """
    frames_dir = abs_path("output/frames")
    os.makedirs(frames_dir, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    result = render_quiz_frames(q, frames_dir)
    hook_text = result["hook"]

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

    print("🎬 AUTO TITLE:", generate_title(hook_text, q.get("category", "general")))

    subprocess.run(cmd, check=True)
    shutil.rmtree(frames_dir, ignore_errors=True)

    return out
