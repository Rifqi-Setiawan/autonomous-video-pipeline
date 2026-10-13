#!/usr/bin/env python3
"""
Autonomous Video Pipeline CLI
End-to-end orchestration: Scene Generation -> Audio/Subtitle Mastering -> FFmpeg Assembly -> Multi-Platform Publishing
"""

import os
import sys
import json
import argparse
import logging

from pipeline.config import PipelineConfig
from pipeline.generator.account_pool import AccountPool
from pipeline.generator.batch_generator import BatchSceneGenerator
from pipeline.studio.audio_mixer import AudioMixer
from pipeline.studio.auto_subtitle import SubtitleEngine
from pipeline.studio.thumbnail_engine import ThumbnailEngine
from pipeline.studio.video_assembler import VideoAssembler
from pipeline.publisher.publisher import MultiPlatformPublisher

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("pipeline_runner")

def run(args):
    config = PipelineConfig.load(args.config)
    os.makedirs(config.output_dir, exist_ok=True)
    os.makedirs(config.clips_dir, exist_ok=True)

    if not os.path.exists(args.storyboard):
        logger.error(f"Storyboard JSON file not found: {args.storyboard}")
        sys.exit(1)

    with open(args.storyboard, "r", encoding="utf-8") as f:
        story = json.load(f)

    ep_id = story.get("episode_id", "ep_01")
    title = story.get("title", "Untitled Episode")
    scenes = story.get("scenes", [])

    logger.info("=" * 80)
    logger.info(f"STARTING AUTONOMOUS VIDEO PIPELINE: {title} ({ep_id})")
    logger.info("=" * 80)

    # Stage 1: Generate AI Video Clips
    if args.stage in ("all", "generate"):
        logger.info("\n--- [STAGE 1] AI Video Generation ---")
        pool = AccountPool(config_path="./config/accounts.json", profiles_dir="./browser_profiles")
        generator = BatchSceneGenerator(pool=pool, output_dir=os.path.join(config.clips_dir, ep_id))
        gen_results = generator.generate_scenes(scenes)
        logger.info(f"Clip generation finished: {len(gen_results)} scenes processed.")

    # Stage 2: Post-Production & Assembly
    final_video = os.path.join(config.output_dir, f"{ep_id}_master.mp4")
    if args.stage in ("all", "assemble"):
        logger.info("\n--- [STAGE 2] Post-Production & Studio Assembly ---")
        clips = [os.path.join(config.clips_dir, ep_id, f"scene_{s.get('scene_id', idx+1):02d}.mp4") for idx, s in enumerate(scenes)]

        # 1. Thumbnail Bake-In Card
        thumb_engine = ThumbnailEngine(font_path=os.path.join(config.fonts_dir, "Anton.ttf"))
        thumb_card = os.path.join(config.output_dir, f"{ep_id}_thumb_card.jpg")
        hook_text = story.get("thumbnail", {}).get("hook_text", title)
        thumb_engine.generate(base_image_path=clips[0] if clips else "", hook_text=hook_text, output_path=thumb_card)

        # 2. Audio & Subtitles
        voice_path = os.path.join(config.audio_dir, f"{ep_id}_voiceover.wav")
        bgm_path = os.path.join(config.audio_dir, "ambient_bgm.mp3")
        mastered_audio = os.path.join(config.output_dir, f"{ep_id}_mixed_audio.mp3")
        ass_subtitles = os.path.join(config.output_dir, f"{ep_id}_subtitles.ass")

        if os.path.exists(voice_path) and os.path.exists(bgm_path):
            mixer = AudioMixer(
                bgm_volume=config.audio.bgm_volume,
                ducking_ratio=config.audio.ducking_ratio,
                target_loudness_lufs=config.audio.target_loudness_lufs
            )
            mixer.mix(voice_track=voice_path, bgm_track=bgm_path, output_path=mastered_audio)

            sub_engine = SubtitleEngine()
            sub_engine.generate_subtitles(audio_path=mastered_audio, ass_path=ass_subtitles)

        # 3. Stitch Scenes
        assembler = VideoAssembler()
        assembler.stitch_scenes(
            scene_paths=clips,
            audio_path=mastered_audio if os.path.exists(mastered_audio) else voice_path,
            subtitle_ass_path=ass_subtitles if os.path.exists(ass_subtitles) else None,
            thumbnail_img_path=thumb_card if os.path.exists(thumb_card) else None,
            output_path=final_video
        )
        logger.info(f"Assembly completed successfully: {final_video}")

    # Stage 3: Multi-Platform Publishing & Storage Lifecycle Archival
    if args.stage in ("all", "publish"):
        logger.info("\n--- [STAGE 3] Multi-Platform Publishing & Cold Archival ---")
        publisher = MultiPlatformPublisher(archive_dir=config.archive_dir)
        pub_results = publisher.publish(
            video_path=final_video,
            title=title,
            description=story.get("description", ""),
            tags=story.get("tags", []),
            target=args.target
        )
        logger.info(f"Publishing results: {pub_results}")

    logger.info("=" * 80)
    logger.info("AUTONOMOUS PIPELINE EXECUTION COMPLETE.")
    logger.info("=" * 80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autonomous Video Pipeline Orchestrator")
    parser.add_argument("--storyboard", type=str, default="./examples/sample_storyboard.json", help="Path to storyboard JSON")
    parser.add_argument("--config", type=str, default="./config/config.example.yaml", help="Path to pipeline YAML config")
    parser.add_argument("--stage", choices=["all", "generate", "assemble", "publish"], default="all", help="Pipeline execution stage")
    parser.add_argument("--target", choices=["all", "youtube", "tiktok"], default="youtube", help="Publishing target")
    args = parser.parse_args()
    run(args)
