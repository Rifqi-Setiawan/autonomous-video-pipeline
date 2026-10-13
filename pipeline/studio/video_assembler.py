"""Synchronized Video Assembler.
Concatenates scenes, burns word-level subtitles, bakes Frame-0 thumbnails, and mixes master audio.
"""

import os
import subprocess
import logging
from typing import List, Optional

logger = logging.getLogger("video_assembler")

class VideoAssembler:
    """Assembles final vertical video (1080x1920 30fps CFR) using FFmpeg."""
    def __init__(self, target_fps: int = 30):
        self.target_fps = target_fps

    def stitch_scenes(
        self,
        scene_paths: List[str],
        audio_path: str,
        subtitle_ass_path: Optional[str],
        thumbnail_img_path: Optional[str],
        output_path: str,
        thumbnail_duration: float = 0.35
    ) -> str:
        """Stitches clips together with mastered audio and burned subtitles."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        temp_dir = os.path.join(os.path.dirname(output_path), "temp_assembly")
        os.makedirs(temp_dir, exist_ok=True)

        concat_list = os.path.join(temp_dir, "concat.txt")
        with open(concat_list, "w", encoding="utf-8") as f:
            for s in scene_paths:
                f.write(f"file '{os.path.abspath(s)}'\n")

        # 1. Base concatenation and scaling
        raw_concat = os.path.join(temp_dir, "raw_concatenated.mp4")
        scale_vf = (
            f"scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps={self.target_fps}"
        )

        cmd_concat = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_list,
            "-vf", scale_vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-an", "-pix_fmt", "yuv420p",
            raw_concat
        ]
        logger.info("Concatenating video scenes...")
        subprocess.run(cmd_concat, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        # 2. Add Frame 0 thumbnail bake-in (if provided) and burn subtitles + audio
        vf_chain = []
        inputs = ["-i", raw_concat, "-i", audio_path]

        if thumbnail_img_path and os.path.exists(thumbnail_img_path):
            inputs.extend(["-loop", "1", "-t", str(thumbnail_duration), "-i", thumbnail_img_path])
            # Overlay thumbnail on the first 0.35s
            filter_complex = (
                f"[0:v]fps={self.target_fps}[main];"
                f"[2:v]scale=1080:1920,fps={self.target_fps}[thumb];"
                f"[thumb][main]concat=n=2:v=1:a=0[v_baked]"
            )
            if subtitle_ass_path and os.path.exists(subtitle_ass_path):
                # Escape path for FFmpeg subtitles filter
                esc_ass = subtitle_ass_path.replace("\\", "/").replace(":", "\\:")
                filter_complex += f";[v_baked]subtitles='{esc_ass}'[v_final]"
                map_video = "[v_final]"
            else:
                map_video = "[v_baked]"
            
            cmd_final = [
                "ffmpeg", "-y",
                *inputs,
                "-filter_complex", filter_complex,
                "-map", map_video,
                "-map", "1:a",
                "-c:v", "libx264", "-preset", "slow", "-crf", "19",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                "-movflags", "+faststart",
                output_path
            ]
        else:
            if subtitle_ass_path and os.path.exists(subtitle_ass_path):
                esc_ass = subtitle_ass_path.replace("\\", "/").replace(":", "\\:")
                vf_chain.append(f"subtitles='{esc_ass}'")

            cmd_final = [
                "ffmpeg", "-y",
                *inputs,
            ]
            if vf_chain:
                cmd_final.extend(["-vf", ",".join(vf_chain)])
            cmd_final.extend([
                "-map", "0:v",
                "-map", "1:a",
                "-c:v", "libx264", "-preset", "slow", "-crf", "19",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                "-movflags", "+faststart",
                output_path
            ])

        logger.info(f"Rendering final master video: {output_path}...")
        subprocess.run(cmd_final, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        # Cleanup intermediate artifacts
        if os.path.exists(raw_concat):
            os.remove(raw_concat)

        return output_path
