<div align="center">

<img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/FFmpeg-Video_Processing-007808?style=for-the-badge&logo=ffmpeg&logoColor=white" />
<img src="https://img.shields.io/badge/YouTube_API-Auto_Upload-FF0000?style=for-the-badge&logo=youtube&logoColor=white" />
<img src="https://img.shields.io/badge/Pillow-Image_Processing-11557C?style=for-the-badge" />

# 🎬 QuizVideoPython

**Fully automated quiz video generation and YouTube upload pipeline.**  
Feed it questions. Get a published video. Zero manual work.

</div>

---

## 🧠 Overview

QuizVideoPython is a Python automation pipeline that takes quiz content and produces a fully composed, ready-to-publish YouTube video — completely hands-free.

It handles everything: compositing question frames over custom backgrounds, synchronising audio, encoding the final video with FFmpeg, and uploading directly to YouTube via the Data API. What used to take hours of manual video editing now runs as a single script.

---

## ✨ What It Does

```
Input: Quiz questions (JSON / text)
         ↓
  Frame generation (PIL/Pillow)
         ↓
  Background compositing
         ↓
  Audio sync (question read + timer sounds)
         ↓
  Video encoding (FFmpeg)
         ↓
Output: Published YouTube video ✅
```

---

## ⚙️ Features

- **Automated frame composition** — question text, answer options, countdown timer rendered as image frames
- **Custom background support** — static images or looping video backgrounds
- **Audio synchronisation** — voice-over, background music, and sound effects timed precisely to frames
- **FFmpeg video encoding** — high-quality MP4 output with configurable resolution and bitrate
- **YouTube auto-upload** — authenticates with YouTube Data API v3 and publishes with title, description, tags, and thumbnail
- **Batch processing** — generate and upload multiple videos from a single input file
- **Template system** — swap visual themes without touching the core pipeline

---

## 🛠 Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| Image Processing | Pillow (PIL) |
| Video Encoding | FFmpeg (via subprocess) |
| Audio Handling | pydub / ffmpeg-python |
| YouTube Upload | Google YouTube Data API v3 |
| Auth | OAuth2 (google-auth) |
| Config | JSON / YAML templates |

---

## 🏗 Project Structure

```
quizvideopython/
├── pipeline/
│   ├── frame_generator.py     # Renders question frames as images
│   ├── compositor.py          # Layers frames over backgrounds
│   ├── audio_sync.py          # Matches audio timing to frames
│   ├── encoder.py             # FFmpeg video assembly
│   └── uploader.py            # YouTube Data API upload
├── templates/
│   ├── backgrounds/           # Background image/video assets
│   └── themes/                # Font, color, layout configs
├── input/
│   └── questions.json         # Your quiz content goes here
├── output/                    # Generated videos saved here
├── config.yaml                # Global pipeline config
└── main.py                    # Run the full pipeline
```

---

## 🚀 Getting Started

```bash
git clone https://github.com/Bonhomie95/quizvideopython.git
cd quizvideopython

pip install -r requirements.txt
```

**Configure your questions:**
```json
[
  {
    "question": "What is the capital of France?",
    "options": ["Berlin", "Madrid", "Paris", "Rome"],
    "answer": "Paris",
    "duration_seconds": 10
  }
]
```

**Run the full pipeline:**
```bash
python main.py --input input/questions.json --theme default --upload
```

> **Note:** YouTube upload requires OAuth2 credentials from Google Cloud Console. See `docs/youtube_setup.md`.

---

## 📋 Requirements

- Python 3.10+
- FFmpeg installed and on PATH
- Google Cloud project with YouTube Data API v3 enabled
- OAuth2 credentials (`client_secrets.json`)

---

## 🌍 Use Cases

- Automated YouTube quiz channels
- Educational content at scale
- Social media short-form quiz clips
- Trivia content for PulseQuiz promotion

---

<div align="center">
  <sub>Built by <a href="https://github.com/Bonhomie95">Adeyemi Joseph</a></sub>
</div>
