import os
import requests
import hashlib
from io import BytesIO
from PIL import Image

CACHE_DIR = "assets/option_images"
os.makedirs(CACHE_DIR, exist_ok=True)

WIKI_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "QuizVideoBot/1.0 (contact: you@yourdomain.com)"}

TARGET_SIZE = (128, 128)  # final avatar size saved to cache


def _key(text: str) -> str:
    # collision-safe filename
    return hashlib.sha1(text.strip().lower().encode("utf-8")).hexdigest()


def get_cached_image(option_text: str) -> str | None:
    path = os.path.join(CACHE_DIR, f"{_key(option_text)}.png")
    return path if os.path.isfile(path) else None


def _normalize_to_png(img_bytes: bytes, out_path: str) -> bool:
    """
    Make consistent cached assets:
    - open
    - RGBA
    - center-crop square
    - resize
    - save PNG
    """
    try:
        img = Image.open(BytesIO(img_bytes)).convert("RGBA")
        w, h = img.size
        if w < 80 or h < 80:  # too small / junk
            return False

        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        img = img.crop((left, top, left + side, top + side))
        img = img.resize(TARGET_SIZE, Image.LANCZOS)

        img.save(out_path, format="PNG", optimize=True)
        return True
    except Exception:
        return False


def fetch_and_cache_image(option_text: str) -> str | None:
    """
    Fetch once, then always use cache afterwards.
    """
    cached = get_cached_image(option_text)
    if cached:
        return cached

    params = {
        "action": "query",
        "titles": option_text,
        "prop": "pageimages",
        "pithumbsize": 400,
        "format": "json",
    }

    try:
        res = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=6)
        data = res.json()
        pages = data.get("query", {}).get("pages", {})

        for page in pages.values():
            thumb = page.get("thumbnail", {}).get("source")
            if not thumb:
                return None

            img_res = requests.get(thumb, headers=HEADERS, timeout=6)
            if img_res.status_code != 200:
                return None

            out_path = os.path.join(CACHE_DIR, f"{_key(option_text)}.png")
            ok = _normalize_to_png(img_res.content, out_path)
            return out_path if ok else None

    except Exception:
        return None

    return None
