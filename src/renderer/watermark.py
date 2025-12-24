import math
from PIL import Image, ImageEnhance
from typing import Tuple

W, H = 1080, 1920


def apply_watermark(
    base: Image.Image,
    logo: Image.Image,
    frame: int,
    corner: str = "top-right",
    opacity: float = 0.7,
) -> Image.Image:
    """
    Adds a subtle animated watermark logo to a frame.
    """

    # --- animation ---
    drift = int(6 * math.sin(frame / 18))
    scale = 0.97 + 0.03 * math.sin(frame / 24)

    size = int(120 * scale)
    wm = logo.resize((size, size), Image.BICUBIC)

    # opacity control
    alpha = wm.getchannel("A")
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    wm.putalpha(alpha)

    pad = 36

    if corner == "top-left":
        x = pad + drift
        y = pad
    elif corner == "bottom-left":
        x = pad + drift
        y = H - size - pad
    elif corner == "bottom-right":
        x = W - size - pad + drift
        y = H - size - pad
    else:  # top-right
        x = W - size - pad + drift
        y = pad

    base.paste(wm, (x, y), wm)
    return base
