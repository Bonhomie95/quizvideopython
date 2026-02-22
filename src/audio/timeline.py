from pydub import AudioSegment
from pathlib import Path

QUESTION_TOTAL = 8000      # 8 seconds gameplay
ANSWER_DURATION = 2500     # reveal time
HOOK_DURATION = 2500
OUTRO_DURATION = 5000


def load(p):
    return AudioSegment.from_file(p)


def pad_to_duration(audio, target_ms):
    if len(audio) >= target_ms:
        return audio[:target_ms]
    silence = AudioSegment.silent(duration=target_ms - len(audio))
    return audio + silence


def build_timeline(audio_files, out_path="output/cache/master.wav"):
    timeline = AudioSegment.silent(duration=200)
    timestamps = []

    def add_block(name, segment):
        nonlocal timeline
        start = len(timeline)
        timeline += segment
        end = len(timeline)
        timestamps.append({"type": name, "start": start, "end": end})

    for name, path in audio_files:
        audio = load(path)

        if name == "hook":
            audio = pad_to_duration(audio, HOOK_DURATION)
            add_block(name, audio)
            continue

        if name.startswith("q"):
            audio = pad_to_duration(audio, QUESTION_TOTAL)
            add_block(name, audio)
            continue

        if name.startswith("a"):
            audio = pad_to_duration(audio, ANSWER_DURATION)
            add_block(name, audio)
            continue

        if name == "outro":
            audio = pad_to_duration(audio, OUTRO_DURATION)
            add_block(name, audio)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    timeline.export(out_path, format="wav")

    return out_path, timestamps
