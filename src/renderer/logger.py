import os
from datetime import datetime

def log(section: str, *args):
    ts = datetime.utcnow().strftime("%H:%M:%S")
    print(f"[{ts}] [{section}]", *args)


def log_dir(dir_path: str):
    if not os.path.isdir(dir_path):
        log("FS", "Directory missing:", dir_path)
        return

    files = sorted(os.listdir(dir_path))
    log("FS", f"{dir_path} → {len(files)} files")

    if files:
        log("FS", "First:", files[0])
        log("FS", "Last :", files[-1])
