# Autonomous Video Pipeline 🎬🤖

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-Chromium-green.svg)](https://playwright.dev/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-Mastering-red.svg)](https://ffmpeg.org/)
[![Whisper](https://img.shields.io/badge/Faster--Whisper-Word--Level-orange.svg)](https://github.com/SYSTRAN/faster-whisper)
[![YouTube API](https://img.shields.io/badge/YouTube_API-v3-red.svg)](https://developers.google.com/youtube/v3)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Autonomous Video Pipeline** is a production-grade, end-to-end automated vertical video (9:16) creation and distribution engine. It orchestrates autonomous AI footage generation via headless browser automation, broadcast-compliant audio mastering, micro-timestamped kinetic subtitles, high-CTR thumbnail insertion, and multi-platform publishing (YouTube Shorts & TikTok) with automated cold-storage lifecycle archival.

---

## 🏗️ System Architecture

```text
 ┌────────────────────────────────────────────────────────┐
 │               Storyboard / Episode JSON                │
 │    (Story outline, AI prompts, voiceover, hook text)   │
 └───────────────────────────┬────────────────────────────┘
                             │
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │  STAGE 1: GENERATION POOL (Playwright Chromium)        │
 │  • Rotating Multi-Account Pool (Round-Robin)           │
 │  • Quota tracking, rate-limit cooldown & failovers     │
 │  • 9:16 Vertical Video Prompt Execution (Google Veo)   │
 │  • Output: Clean raw MP4 video scene clips             │
 └───────────────────────────┬────────────────────────────┘
                             │
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │  STAGE 2: POST-PRODUCTION & STUDIO MASTERING           │
 │  ├─ Audio Engine: EBU R128 (-14 LUFS) & Sidechain Duck │
 │  ├─ Subtitle Engine: Faster-Whisper word timestamps    │
 │  ├─ Thumbnail Engine: Frame-0 Bake-In hook card (0.35s)│
 │  └─ Video Assembler: FFmpeg 1080x1920 30fps CFR Stitch │
 └───────────────────────────┬────────────────────────────┘
                             │
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │  STAGE 3: PUBLISHING & STORAGE LIFECYCLE               │
 │  • YouTube Data API v3 Shorts Auto-Uploader            │
 │  • TikTok Creator Studio Session Automator             │
 │  • Hot-to-Cold Storage Migration (Zero-Downtime Links) │
 └────────────────────────────────────────────────────────┘
```

---

## ⚡ Key Capabilities

### 1. Multi-Account Browser Automation & Quota Balancing
* **Session Pooling:** Rotates through persistent browser profile slots to bypass single-account daily generation ceilings.
* **Auto-Failover:** Detects safety filter refusals and daily quota depletion in real-time, automatically switching tasks to standby account slots without stalling the pipeline.
* **Aspect Ratio Enforcement:** Programmatically guarantees true **Portrait (9:16)** frame generation.

### 2. Broadcast-Grade Audio Engineering (EBU R128 & Sidechain Ducking)
* **Standard Loudness:** Mixes narrative voice and background music (BGM) to exact international streaming standards (**-14 LUFS**, True Peak -1.0 dBTP).
* **Smooth Sidechain Ducking:** Compresses background music cleanly whenever voiceover is active (fast 15ms attack, smooth 240ms release), swelling naturally during speech pauses.
* **Constant Narration Integrity:** Ensures audio fade-outs apply exclusively to background music while narrative speech remains 100% constant and authoritative until the final millisecond.

### 3. Dynamic Word-Level Kinetic Subtitles (Faster-Whisper)
* **Millisecond Precision:** Transcribes speech audio using `faster-whisper-large-v3-turbo` with word-level boundaries.
* **Poetic Line Chunking:** Groups words into natural speech units (3–5 words per line) based on acoustic pauses (>0.35s) rather than naive character limits.
* **2-Tone Visual ASS Styling:** Generates custom ASS subtitle events featuring crisp white base dialogue with vibrant yellow word highlights and black outer borders.

### 4. Frame-0 High-CTR Hook Card Generator
* **Bake-In Thumbnail Technology:** Embeds a high-impact, centered 2-tone hook card directly into the first 0.35 seconds (Frame 0) of the master video.
* **Maximum CTR:** Ensures that platforms without manual thumbnail support automatically display a clear, compelling graphic hook on user feeds.

### 5. Automated Multi-Platform Distribution & Cold Storage Archival
* **API Integration:** Automatically distributes finalized videos to **YouTube Shorts** via YouTube Data API v3 and **TikTok**.
* **Zero-Downtime Archiving:** Upon confirmed publication, moves multi-gigabyte master videos and render caches from primary root storage to cold data volumes while preserving lightweight symlinks, keeping production hosts lean.

---

## 📁 Repository Structure

```text
autonomous-video-pipeline/
├── config/
│   ├── config.example.yaml          # Pipeline thresholds & visual styles
│   ├── accounts.example.json        # Google account slot pool definitions
│   └── client_secrets.example.json  # OAuth2 YouTube Data API template
├── examples/
│   └── sample_storyboard.json       # Sample 3-scene episode storyboard
├── pipeline/
│   ├── __init__.py
│   ├── config.py                    # Dataclass configuration loader
│   ├── generator/
│   │   ├── __init__.py
│   │   ├── account_pool.py          # Account slot rotation & quota manager
│   │   ├── batch_generator.py       # Sequential scene prompt dispatcher
│   │   └── gemini_worker.py         # Playwright Chromium browser worker
│   ├── studio/
│   │   ├── __init__.py
│   │   ├── audio_mixer.py           # EBU R128 mastering & auto-ducking
│   │   ├── auto_subtitle.py         # Faster-Whisper word-level ASS generator
│   │   ├── thumbnail_engine.py      # Pillow Frame-0 hook card renderer
│   │   └── video_assembler.py       # FFmpeg video stitcher & subtitle burner
│   └── publisher/
│       ├── __init__.py
│       ├── publisher.py             # Multi-platform distributor & archiver
│       ├── youtube_uploader.py      # YouTube Data API v3 publisher
│       └── tiktok_uploader.py       # TikTok session publisher
├── run_pipeline.py                  # Unified CLI orchestrator
├── requirements.txt                 # Python dependencies
└── README.md
```

---

## 🚀 Quick Start Guide

### Prerequisites
* Python 3.10+
* FFmpeg (with libx264, libmp3lame, and libass support)
* Google Chrome / Chromium

### 1. Installation
```bash
git clone https://github.com/Rifqi-Setiawan/autonomous-video-pipeline.git
cd autonomous-video-pipeline

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium
```

### 2. Configuration Setup
```bash
cp config/config.example.yaml config/config.yaml
cp config/accounts.example.json config/accounts.json
cp config/client_secrets.example.json config/client_secrets.json
```

### 3. Execution via CLI

Run the full end-to-end pipeline:
```bash
python run_pipeline.py --storyboard examples/sample_storyboard.json --stage all
```

Or execute discrete stages independently:
```bash
# 1. Generate video footage only
python run_pipeline.py --storyboard examples/sample_storyboard.json --stage generate

# 2. Assemble audio, subtitles, and final MP4
python run_pipeline.py --storyboard examples/sample_storyboard.json --stage assemble

# 3. Publish to YouTube Shorts and archive to cold storage
python run_pipeline.py --storyboard examples/sample_storyboard.json --stage publish --target youtube
```

---

## 🔒 Security & Privacy

* **Strict Isolation:** Authentication tokens, browser session cookies, and private credentials are kept strictly local via `.gitignore`.
* **Zero Secret Leakage:** Example configuration templates are provided for safe deployment across developer environments.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 👨‍💻 Author

**Muhammad Rifqi Setiawan**  
* GitHub: [@Rifqi-Setiawan](https://github.com/Rifqi-Setiawan)  
* Email: `149862767+Rifqi-Setiawan@users.noreply.github.com`
