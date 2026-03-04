import os
from pathlib import Path
from .tts import tts_to_file

LEVEL_NAMES = {
    "easy": "Easy",
    "medium": "Medium",
    "hard": "Hard",
    "impossible": "Impossible",
    "genius": "Genius",
}


def build_question_text(index, q):
    # Number prefix creates rhythm: "Question 1." pause before the question
    return f"Question {index}. {q['question']}"


def build_answer_text(q):
    # Short and punchy — viewers want the answer fast
    return f"The answer is... {q['answer']}"


def generate_episode_audio(episode: dict, out_dir="output/cache/audio"):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    files = []

    # Hook
    hook_path = out_dir / "hook.wav"
    tts_to_file(episode["hook"], hook_path)
    files.append(("hook", hook_path))

    # Questions
    for i, q in enumerate(episode["questions"], 1):
        q_path = out_dir / f"q{i}.wav"
        a_path = out_dir / f"a{i}.wav"

        tts_to_file(build_question_text(i, q), q_path)
        tts_to_file(build_answer_text(q), a_path)

        files.extend([(f"q{i}", q_path), (f"a{i}", a_path)])

    # Outro
    outro_path = out_dir / "outro.wav"
    tts_to_file(episode["outro"], outro_path)
    files.append(("outro", outro_path))

    return files
