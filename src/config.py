import os
from dotenv import load_dotenv

load_dotenv()

UPLOAD_EVERY_HOURS = int(os.getenv("UPLOAD_EVERY_HOURS", "12"))
COMMENT_DELAY_HOURS = int(os.getenv("COMMENT_DELAY_HOURS", "24"))

MONGO_URI = os.getenv("MONGO_URI", "")

YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
YOUTUBE_REDIRECT_URI = os.getenv("YOUTUBE_REDIRECT_URI", "")
YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN", "")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID", "")
META_PAGE_ID = os.getenv("META_PAGE_ID", "")
META_PAGE_ACCESS_TOKEN = os.getenv("META_PAGE_ACCESS_TOKEN", "")

# BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


DATA_PATH = os.path.join(PROJECT_DIR, "data", "questions.json")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output", "renders")
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
MUSIC_DIR = os.path.join(ASSETS_DIR, "music")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() in ("1", "true", "yes", "on")
CACHE_DIR = os.getenv("CACHE_DIR", "output/cache")
LOG_DIR = os.getenv("LOG_DIR", "output/logs")

AUTO_SKIP_UPLOAD_LIMIT = os.getenv(
    "AUTO_SKIP_UPLOAD_LIMIT", "true"
).lower() in ("1", "true", "yes", "on")
