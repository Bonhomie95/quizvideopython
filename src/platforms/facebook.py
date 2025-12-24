CTA_THEMES = [
    ((30, 20, 60), (10, 10, 30)),
    ((20, 60, 50), (5, 20, 25)),
    ((60, 30, 20), (30, 10, 5)),
    ((25, 15, 50), (5, 5, 20)),
]

FACEBOOK_PLATFORM = {
    "name": "facebook",
    "cta_duration": 3,
    "cta_text": [
        "Like • Comment • Follow",
        "Share with a friend ⚽",
    ],
    "icons": [
        "assets/icons/fb_like.png",
        "assets/icons/fb_comment.png",
        "assets/icons/fb_follow.png",
    ],
    "themes": CTA_THEMES,
    # ✅ ADD THIS
    "description": lambda q: (
        f"{q['question']}\n\n"
        "Like • Comment • Follow\n"
        "#football #quiz #reels #trivia"
    ),
}
