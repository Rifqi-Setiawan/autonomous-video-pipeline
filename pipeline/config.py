"""Configuration loader and schema definition for the pipeline."""

import os
import yaml
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class AudioConfig:
    bgm_volume: float = 1.80
    ducking_ratio: float = 2.2
    ducking_threshold: float = 0.08
    attack_ms: int = 15
    release_ms: int = 240
    target_loudness_lufs: float = -14.0

@dataclass
class SubtitleConfig:
    font: str = "Bebas Neue"
    font_size: int = 24
    primary_color: str = "&H00FFFFFF"
    highlight_color: str = "&H0000E6FF"
    outline_color: str = "&H00000000"
    outline_width: float = 3.5
    shadow_width: float = 2.0

@dataclass
class ThumbnailConfig:
    display_duration_seconds: float = 0.35
    font: str = "Anton"
    max_text_width: int = 860

@dataclass
class PipelineConfig:
    output_dir: str = "./output"
    clips_dir: "./clips" = "./clips"
    archive_dir: str = "./archive"
    fonts_dir: str = "./assets/fonts"
    audio_dir: str = "./assets/audio"
    audio: AudioConfig = field(default_factory=AudioConfig)
    subtitles: SubtitleConfig = field(default_factory=SubtitleConfig)
    thumbnails: ThumbnailConfig = field(default_factory=ThumbnailConfig)

    @classmethod
    def load(cls, path: Optional[str] = None) -> "PipelineConfig":
        if not path or not os.path.exists(path):
            return cls()
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

        paths = raw.get("paths", {})
        studio = raw.get("studio", {})
        
        audio_dict = studio.get("audio", {})
        sub_dict = studio.get("subtitles", {})
        thumb_dict = studio.get("thumbnails", {})

        return cls(
            output_dir=paths.get("output_dir", "./output"),
            clips_dir=paths.get("clips_dir", "./clips"),
            archive_dir=paths.get("archive_dir", "./archive"),
            fonts_dir=paths.get("fonts_dir", "./assets/fonts"),
            audio_dir=paths.get("audio_dir", "./assets/audio"),
            audio=AudioConfig(**audio_dict) if audio_dict else AudioConfig(),
            subtitles=SubtitleConfig(**sub_dict) if sub_dict else SubtitleConfig(),
            thumbnails=ThumbnailConfig(**thumb_dict) if thumb_dict else ThumbnailConfig(),
        )
