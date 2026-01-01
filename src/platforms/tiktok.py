# TikTok CTA Themes (high contrast, punchy)
CTA_THEMES = [
    ((0, 0, 0), (30, 30, 30)),  # dark premium
    ((10, 10, 10), (60, 20, 20)),  # red punch
    ((10, 10, 10), (20, 40, 60)),  # blue tech
    ((15, 15, 15), (40, 30, 20)),  # warm dark
]

TIKTOK_PLATFORM = {
    "name": "tiktok",
    # CTA
    "cta_duration": 3,  # seconds
    "cta_text": [
        "Follow for daily quizzes 🔥",
        "Answer in comments 👇",
    ],
    "icons": [
        "assets/icons/tt_like.png",
        "assets/icons/tt_comment.png",
        "assets/icons/tt_follow.png",
    ],
    "themes": CTA_THEMES,
    # Metadata (for future upload)
    "title": lambda q: (f"{q['category'].replace('_',' ').title()} Quiz 🤯"),
    "description": lambda q: (
        f"{q['question']}\n\n"
        "Think fast ⏱️ Answer below 👇\n\n"
        "#quiz #trivia #fyp #learnontiktok"
    ),
}
