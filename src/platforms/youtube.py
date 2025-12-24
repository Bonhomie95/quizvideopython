CTA_THEMES = [
    ((30, 20, 60), (10, 10, 30)),
    ((20, 60, 50), (5, 20, 25)),
    ((60, 30, 20), (30, 10, 5)),
    ((25, 15, 50), (5, 5, 20)),
]

YOUTUBE_PLATFORM = {
    "name": "youtube",
    # CTA
    "cta_duration": 3,  # seconds
    "cta_text": [
        "Like • Comment • Subscribe",
        "Answer drops in 24 hours 👇",
    ],
    "icons": [
        "assets/icons/yt_like.png",
        "assets/icons/yt_comment.png",
        "assets/icons/yt_subscribe.png",
    ],
    "themes": CTA_THEMES,
    # Metadata
    "title": lambda q: (
        f"{q['category'].replace('_',' ').title()} Quiz • "
        f"{q['difficulty'].title()} 🤔 #shorts"
    ),
    "description": lambda q: (
        f"{q['question']}\n\n"
        "Comment your guess 👇\n\n"
        "#quiz #football #trivia #shorts"
    ),
}
