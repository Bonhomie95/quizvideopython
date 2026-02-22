import asyncio
from pathlib import Path

VOICE = "en-US-GuyNeural"


# ---------------- EDGE TTS (ONLINE) ----------------
async def _edge_generate(text: str, path: Path):
    import edge_tts
    communicate = edge_tts.Communicate(text=text, voice=VOICE)
    await communicate.save(str(path))


def _try_edge(text: str, path: Path):
    try:
        asyncio.run(_edge_generate(text, path))
        return True
    except Exception as e:
        print("⚠️ Edge TTS failed — switching to offline voice")
        return False


# ---------------- OFFLINE TTS ----------------
def _offline_generate(text: str, path: Path):
    import pyttsx3

    engine = pyttsx3.init()
    engine.setProperty("rate", 175)
    engine.save_to_file(text, str(path))
    engine.runAndWait()


# ---------------- PUBLIC API ----------------
def tts_to_file(text: str, path: str):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # try online first
    if _try_edge(text, path):
        return

    # fallback offline
    _offline_generate(text, path)
