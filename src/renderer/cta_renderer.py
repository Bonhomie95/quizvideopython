import os
import random
from typing import Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont

from .watermark import apply_watermark
from .logger import log

# =========================================================
# CONSTANTS
# =========================================================

W, H, FPS = 1080, 1920, 30
FONT_PATH = "assets/fonts/Inter-Bold.ttf"
LOGO_PATH = "assets/logo.png"


# =========================================================
# LOADERS
# =========================================================


def load_logo():
    if os.path.isfile(LOGO_PATH):
        return Image.open(LOGO_PATH).convert("RGBA")
    return None


# =========================================================
# HELPERS
# =========================================================


def ease_out(t: float) -> float:
    return 1 - (1 - t) ** 3


def slide_y(base: int, frame: int, start: int, dist: int = 80) -> int:
    if frame < start:
        return base + dist
    t = min(1.0, (frame - start) / 20)
    return int(base + (1 - ease_out(t)) * dist)


def fade_alpha(frame: int, start: int, duration: int = 20) -> int:
    if frame < start:
        return 0
    return min(255, int((frame - start) / duration * 255))


def draw_gradient(
    img: Image.Image, top: Tuple[int, int, int], bottom: Tuple[int, int, int]
):
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))


def safe_icon(path: str, size: int):
    if not os.path.isfile(path):
        log("CTA", f"⚠️ Missing icon skipped: {path}")
        return None
    return Image.open(path).convert("RGBA").resize((size, size))


# =========================================================
# MAIN
# =========================================================


def render_cta_frames(frames_dir: str, start_index: int, platform: Dict):
    duration = platform["cta_duration"]
    total_frames = duration * FPS

    theme_top, theme_bottom = random.choice(platform["themes"])
    icons: List[str] = platform["icons"]
    texts: List[str] = platform["cta_text"]

    font = ImageFont.truetype(FONT_PATH, 48)
    logo = load_logo()

    log("CTA", f"Frames: {total_frames} ({platform['name']})")

    for i in range(total_frames):
        frame_no = start_index + i

        # -----------------------------
        # Background
        # -----------------------------
        img = Image.new("RGB", (W, H))
        draw_gradient(img, theme_top, theme_bottom)

        # -----------------------------
        # Glass card
        # -----------------------------
        card = Image.new("RGBA", (900, 520), (255, 255, 255, 40))
        img = img.convert("RGBA")
        img.paste(card, (90, 620), card)

        # -----------------------------
        # CTA text
        # -----------------------------
        alpha = fade_alpha(i, 0)
        text_layer = Image.new("RGBA", (W, H))
        td = ImageDraw.Draw(text_layer)

        y = slide_y(720, i, 0)
        for line in texts:
            td.text(
                (W // 2, y),
                line,
                font=font,
                fill=(255, 255, 255, alpha),
                anchor="mm",
            )
            y += 80

        img = Image.alpha_composite(img, text_layer)

        # -----------------------------
        # Icons (staggered)
        # -----------------------------
        icon_size = 96
        gap = 40
        valid_icons = [p for p in icons if os.path.isfile(p)]

        if valid_icons:
            total_w = len(valid_icons) * icon_size + (len(valid_icons) - 1) * gap
            start_x = (W - total_w) // 2
            base_y = 1150

            x = start_x
            for idx, path in enumerate(valid_icons):
                appear_at = 10 + idx * 6
                if i < appear_at:
                    continue

                ic = safe_icon(path, icon_size)
                if not ic:
                    continue

                y_icon = slide_y(base_y, i, appear_at)
                img.paste(ic, (x, y_icon), ic)
                x += icon_size + gap

        # -----------------------------
        # Animated watermark (ALWAYS LAST)
        # -----------------------------
        if logo:
            img = apply_watermark(
                base=img,
                logo=logo,
                frame=i,
                corner="top-left",
                opacity=0.75,
            )

        # -----------------------------
        # Save
        # -----------------------------
        img.convert("RGB").save(os.path.join(frames_dir, f"frame_{frame_no:04d}.png"))

    log("CTA", "CTA frames done")
    return total_frames