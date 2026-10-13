"""Word-Level Subtitle Engine using Faster-Whisper.
Produces clean, dynamic highlighted ASS subtitles for 9:16 vertical video.
"""

import os
import subprocess
import logging
from typing import Optional, List
from faster_whisper import WhisperModel

logger = logging.getLogger("subtitle_engine")

def format_ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"

class SubtitleEngine:
    """Generates broadcast-grade animated word-level ASS subtitles."""
    def __init__(
        self,
        model_size_or_path: str = "large-v3-turbo",
        device: str = "cpu",
        compute_type: str = "int8"
    ):
        self.model_size_or_path = model_size_or_path
        self.device = device
        self.compute_type = compute_type

    def generate_subtitles(
        self,
        audio_path: str,
        ass_path: str,
        language: str = "id"
    ) -> str:
        """Transcribes audio with word timestamps and builds ASS script."""
        os.makedirs(os.path.dirname(os.path.abspath(ass_path)), exist_ok=True)
        logger.info(f"Extracting speech word timestamps from {os.path.basename(audio_path)}...")

        model = WhisperModel(self.model_size_or_path, device=self.device, compute_type=self.compute_type)
        segments, _ = model.transcribe(audio_path, language=language, word_timestamps=True)

        all_words = []
        hallucinations = {"TERIMA KASIH", "TERIMA KASIH.", "SUBSCRIBE", "LIKE", "COMMENT"}

        for segment in segments:
            for w in segment.words:
                all_words.append(w)

        # Strip trailing hallucinated phrases from silence
        while len(all_words) >= 2:
            last = all_words[-1].word.strip().upper()
            if last in hallucinations:
                all_words.pop()
            else:
                break

        chunks = []
        i = 0
        while i < len(all_words):
            chunk = [all_words[i]]
            i += 1
            while i < len(all_words):
                next_w = all_words[i]
                pause = next_w.start - chunk[-1].end
                if pause >= 0.35 and len(chunk) >= 2:
                    break
                if len(chunk) >= 4 and next_w.word.strip().endswith((".", ",", "?", "!")):
                    chunk.append(next_w)
                    i += 1
                    break
                if len(chunk) >= 5:
                    break
                chunk.append(next_w)
                i += 1
            chunks.append(chunk)

        header = [
            "[Script Info]",
            "Title: Autonomous Video Pipeline Dynamic Subtitles",
            "ScriptType: v4.00+",
            "PlayResX: 1080",
            "PlayResY: 1920",
            "ScaledBorderAndShadow: yes",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            "Style: Default,Bebas Neue,24,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3.5,2,2,40,40,240,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
        ]

        events = []
        for chunk in chunks:
            chunk_start = chunk[0].start
            chunk_end = chunk[-1].end + 0.15

            words_str_list = []
            for w in chunk:
                dur_cs = max(1, int((w.end - w.start) * 100))
                clean_word = w.word.strip().upper()
                words_str_list.append(f"{{\\k{dur_cs}}}{clean_word}")

            line_text = " ".join(words_str_list)
            events.append(f"Dialogue: 0,{format_ass_time(chunk_start)},{format_ass_time(chunk_end)},Default,,0,0,0,,{line_text}")

        with open(ass_path, "w", encoding="utf-8") as f:
            f.write("\n".join(header + events) + "\n")

        logger.info(f"Generated dynamic ASS subtitles: {ass_path}")
        return ass_path
