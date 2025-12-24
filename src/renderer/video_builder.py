import os
import subprocess
from datetime import datetime


def build_video(
    frames_dir: str,
    output_dir: str,
    fps: int,
    music: str | None,
    prefix: str,
) -> str:
    os.makedirs(output_dir, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out = os.path.join(output_dir, f"{prefix}_{ts}.mp4")

    frames_input = os.path.join(frames_dir, "frame_%04d.png")

    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(fps),
        "-i",
        frames_input,
    ]

    if music:
        cmd += ["-i", music, "-shortest", "-af", "volume=0.18"]

    cmd += [
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        out,
    ]

    print("[BUILD] FFmpeg cmd:", " ".join(cmd))
    subprocess.run(cmd, check=True)

    return out
