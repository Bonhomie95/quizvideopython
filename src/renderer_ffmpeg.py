import os
import random
import shutil
import subprocess
from datetime import datetime
from typing import Any, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageEnhance

from .config import OUTPUT_DIR, FONTS_DIR, MUSIC_DIR
from .utils.text import wrap_lines

W, H, FPS = 1080, 1920, 30
DURATION = 13


def log(*args):
    print("[renderer]", *args)


def abs_path(p: str) -> str:
    return os.path.abspath(p)


# ✅ Pillow resample compatibility + fixes Pylance "LANCZOS not known"
try:
    _Resampling = getattr(Image, "Resampling")  # Pillow ≥ 9
    RESAMPLE: Any = _Resampling.LANCZOS
except Exception:
    RESAMPLE = getattr(Image, "LANCZOS", Image.BICUBIC)  # fallback


def pick_music() -> Optional[str]:
    if not os.path.isdir(MUSIC_DIR):
        return None
    tracks = [
        os.path.join(MUSIC_DIR, f)
        for f in os.listdir(MUSIC_DIR)
        if f.lower().endswith((".mp3", ".wav", ".m4a"))
    ]
    return random.choice(tracks) if tracks else None


def load_font(filename: str, size: int) -> ImageFont.FreeTypeFont:
    path = os.path.join(FONTS_DIR, filename)
    return ImageFont.truetype(path, size)


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def draw_gradient(
    draw: ImageDraw.ImageDraw, top: Tuple[int, int, int], bottom: Tuple[int, int, int]
):
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
        log("Missing asset:", path)
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
    frames_dir = abs_path(os.path.join("output", "frames"))
    renders_dir = abs_path(OUTPUT_DIR)
    os.makedirs(frames_dir, exist_ok=True)
    os.makedirs(renders_dir, exist_ok=True)

    music = pick_music()
    log("Music:", music or "None")

    gradients = [
        ((5, 5, 7), (20, 20, 40)),
        ((10, 10, 20), (5, 5, 7)),
        ((15, 5, 30), (5, 5, 15)),
        ((6, 12, 25), (2, 2, 8)),
        ((18, 10, 30), (3, 3, 10)),
    ]
    top_color, bottom_color = random.choice(gradients)

    category = (q.get("category") or "quiz").replace("_", " ").title()
    difficulty = (q.get("difficulty") or "easy").title()
    question = wrap_lines(q["question"], 40)
    A, B, C, D = q["options"]

    font_small = load_font("Inter-Regular.ttf", 38)
    font_big = load_font("Inter-Bold.ttf", 54)
    font_opt = load_font("Inter-Regular.ttf", 44)
    font_cta = load_font("Inter-Bold.ttf", 46)

    total_frames = FPS * DURATION

    def slide_y(base: int, frame: int, start: int, dist: int = 60) -> int:
        if frame < start:
            return base + dist
        t = min(1.0, (frame - start) / FPS)
        eased = 1.0 - (1.0 - t) ** 3
        return int(base + (1.0 - eased) * dist)

    def slide_x(base: int, frame: int, start: int, offset: int) -> int:
        if frame < start:
            return base + offset
        t = min(1.0, (frame - start) / FPS)
        eased = 1.0 - (1.0 - t) ** 3
        return int(base + (1.0 - eased) * offset)

    # assets
    logo = safe_load_rgba("assets/logo.png", size=(120, 120), opacity=0.75)

    yt_like = safe_load_rgba("assets/icons/yt_like.png", size=(96, 96), opacity=0.95)
    yt_comment = safe_load_rgba(
        "assets/icons/yt_comment.png", size=(96, 96), opacity=0.95
    )
    yt_sub = safe_load_rgba(
        "assets/icons/yt_subscribe.png", size=(96, 96), opacity=0.95
    )

    fb_like = safe_load_rgba("assets/icons/fb_like.png", size=(96, 96), opacity=0.95)
    fb_comment = safe_load_rgba(
        "assets/icons/fb_comment.png", size=(96, 96), opacity=0.95
    )
    fb_follow = safe_load_rgba(
        "assets/icons/fb_follow.png", size=(96, 96), opacity=0.95
    )

    yt_icons = [x for x in [yt_like, yt_comment, yt_sub] if x is not None]
    fb_icons = [x for x in [fb_like, fb_comment, fb_follow] if x is not None]
    cta_start_frame = (DURATION - 2) * FPS

    # render frames
    for frame in range(total_frames):
        img = Image.new("RGB", (W, H))
        draw = ImageDraw.Draw(img)

        draw_gradient(draw, top_color, bottom_color)

        if logo:
            img.paste(logo, (W - 140, 40), logo)

        header_start = int(0.8 * FPS)
        if frame >= header_start:
            y = slide_y(260, frame, header_start, dist=60)
            text = f"{category} - {difficulty}"
            tw = float(draw.textlength(text, font=font_small))
            x0 = int((W - tw) / 2)  # ✅ int fixes float->int type error
            draw.text((x0, y), text, font=font_small, fill="white")

        question_start = int(1.8 * FPS)
        if frame >= question_start:
            y = slide_y(520, frame, question_start, dist=60)
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
                y = slide_y(y0 + i * 110, frame, start, dist=60)
                tw = float(draw.textlength(text, font=font_opt))
                x_base = int((W - tw) / 2)  # ✅ int base
                x = slide_x(x_base, frame, start, offset)
                draw.text((x, y), text, font=font_opt, fill="white")

        # CTA end-screen
        if frame >= cta_start_frame:
            overlay = Image.new("RGBA", (W, H), (0, 0, 0, 120))
            base = img.convert("RGBA")
            base = Image.alpha_composite(base, overlay)

            d2 = ImageDraw.Draw(base)
            d2.text(
                (W // 2, 1350),
                "YouTube: Like • Comment • Subscribe",
                font=font_cta,
                fill="white",
                anchor="mm",
            )
            d2.text(
                (W // 2, 1425),
                "Facebook: Like • Comment • Follow",
                font=font_cta,
                fill="white",
                anchor="mm",
            )

            icons = yt_icons + fb_icons
            if icons:
                gap = 36
                icon_w = 96
                total_w = len(icons) * icon_w + (len(icons) - 1) * gap
                start_x = (W - total_w) // 2
                y_icons = 1500
                for idx, ic in enumerate(icons):
                    x = start_x + idx * (icon_w + gap)
                    base.paste(ic, (x, y_icons), ic)

            img = base.convert("RGB")

        img.save(os.path.join(frames_dir, f"frame_{frame:04d}.png"))

    # encode
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out = abs_path(os.path.join(renders_dir, f"quiz_{ts}.mp4"))

    frames_input = os.path.join(frames_dir, "frame_%04d.png")

    cmd = ["ffmpeg", "-y", "-framerate", str(FPS), "-i", frames_input]

    if music:
        cmd += ["-i", abs_path(music), "-shortest", "-af", "volume=0.18"]

    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]

    log("Encoding video…")
    log("FFmpeg cmd:", " ".join(cmd))

    try:
        subprocess.run(cmd, check=True)
    finally:
        # ✅ delete frames always
        shutil.rmtree(frames_dir, ignore_errors=True)
        log("Frames cleaned")

    log("Video created:", out)
    return out
