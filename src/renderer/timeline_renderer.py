from math import ceil
from pathlib import Path

FPS = 30


def ms_to_frames(ms):
    return ceil((ms / 1000) * FPS)


def group_timeline(timestamps):
    """
    Convert raw timestamps into renderable scenes
    """
    scenes = []

    for i, t in enumerate(timestamps):
        duration = t["end"] - t["start"]
        frames = ms_to_frames(duration)

        scenes.append({
            "type": t["type"],
            "frames": frames
        })

    return scenes
