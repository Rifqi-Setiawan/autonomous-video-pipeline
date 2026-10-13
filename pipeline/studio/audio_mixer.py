"""Audio Mastering and Auto-Ducking Engine.
Calibrated for EBU R128 -14 LUFS loudness standard with clean sidechain ducking.
"""

import os
import subprocess
import logging
from typing import Optional

logger = logging.getLogger("audio_mixer")

class AudioMixer:
    """Mixes voiceover narration with background music (BGM).
    Applies high-pass cleanup on voice, dynamic sidechain ducking on BGM,
    and broadcast loudness normalization (-14 LUFS).
    """
    def __init__(
        self,
        bgm_volume: float = 1.80,
        ducking_ratio: float = 2.2,
        ducking_threshold: float = 0.08,
        attack_ms: int = 15,
        release_ms: int = 240,
        target_loudness_lufs: float = -14.0
    ):
        self.bgm_volume = bgm_volume
        self.ducking_ratio = ducking_ratio
        self.ducking_threshold = ducking_threshold
        self.attack_ms = attack_ms
        self.release_ms = release_ms
        self.target_loudness_lufs = target_loudness_lufs

    def mix(
        self,
        voice_path: str,
        bgm_path: str,
        output_path: str,
        bgm_seek_seconds: float = 15.0,
        fade_out_duration: float = 3.8
    ) -> str:
        """Processes voice and BGM into a broadcast-standard mastered audio track."""
        if not os.path.exists(voice_path):
            raise FileNotFoundError(f"Voice track not found: {voice_path}")
        if not os.path.exists(bgm_path):
            raise FileNotFoundError(f"BGM track not found: {bgm_path}")

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        probe_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            voice_path
        ]
        voice_dur = float(subprocess.check_output(probe_cmd).decode().strip())
        fade_start = max(0.0, voice_dur - fade_out_duration)

        filter_complex = (
            f"[0:a]highpass=f=70,agate=threshold=0.025:ratio=2.0:range=0.1:attack=15:release=180,"
            f"acompressor=threshold=-12dB:ratio=3:attack=10:release=100:makeup=2.5dB[v_clean];"
            f"[v_clean]asplit=2[v_lead][v_sc];"
            f"[1:a]volume={self.bgm_volume},"
            f"afade=t=out:st={fade_start:.2f}:d={fade_out_duration:.2f}[bgm_full];"
            f"[bgm_full][v_sc]sidechaincompress=threshold={self.ducking_threshold}:"
            f"ratio={self.ducking_ratio}:attack={self.attack_ms}:release={self.release_ms}[ducked_bgm];"
            f"[ducked_bgm][v_lead]amix=inputs=2:duration=first:weights=0.85 2.2,"
            f"loudnorm=I={self.target_loudness_lufs}:TP=-1.0:LRA=8[out]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", voice_path,
            "-ss", str(bgm_seek_seconds),
            "-stream_loop", "-1",
            "-i", bgm_path,
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            output_path
        ]

        logger.info(f"Mastering audio mix (-14 LUFS, Ducking: {self.ducking_ratio}:1)...")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        return output_path
