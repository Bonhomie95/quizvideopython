import json
import os
import random
from .config import DATA_PATH

STATE_PATH = os.path.join(os.path.dirname(DATA_PATH), ".used.json")


def _load_used():
    if not os.path.exists(STATE_PATH):
        return set()
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return set(json.load(f))


def _save_used(used_set):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(list(used_set)), f)


def pick_question():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)

    used = _load_used()
    candidates = [q for q in items if q["question"] not in used]
    if not candidates:
        used = set()
        candidates = items[:]  # reset cycle

    q = random.choice(candidates)
    used.add(q["question"])
    _save_used(used)
    return q
