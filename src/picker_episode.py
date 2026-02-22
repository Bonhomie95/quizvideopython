import json
import random
from pathlib import Path

DIFFICULTY_ORDER = ["easy", "medium", "hard", "impossible", "genius"]

HOOKS = [
    "Only smart people finish this quiz",
    "If you get 5 out of 5 your brain is elite",
    "You can not answer question five",
    "This quiz gets harder every question",
    "Level five breaks almost everyone",
]

OUTROS = [
    "Comment your score. Top 3 will be announced tomorrow.",
    "Only real geniuses get 5 out of 5. Comment below.",
    "I want to see who survives question five.",
]

DATA_PATH = Path("data/questions.json")
USED_PATH = Path("data/used.json")


def load_questions():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_used():
    if not USED_PATH.exists():
        return set()
    return set(json.loads(USED_PATH.read_text()))


def save_used(ids):
    USED_PATH.write_text(json.dumps(list(ids), indent=2))


def pick_by_difficulty(questions, difficulty, used):
    pool = [
        q
        for q in questions
        if q["difficulty"] == difficulty and q["question"] not in used
    ]

    if not pool:  # reset if exhausted
        pool = [q for q in questions if q["difficulty"] == difficulty]

    q = random.choice(pool) if pool else None
    if q:
        used.add(q["question"])
    return q


def build_episode():
    questions = load_questions()
    used = load_used()
    selected = []

    for diff in DIFFICULTY_ORDER:
        q = pick_by_difficulty(questions, diff, used)
        if q:
            selected.append(q)

    save_used(used)

    if len(selected) < 3:
        raise Exception("Not enough questions")

    return {
        "hook": random.choice(HOOKS),
        "questions": selected,
        "outro": random.choice(OUTROS),
    }
