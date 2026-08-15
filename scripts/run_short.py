import argparse
import sys
import os

# Fix python path if run from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from core.logger import logger
from core.orchestrator import Orchestrator

from services.topic_generator import GroqTopicGenerator
from services.script_generator import GroqScriptGenerator
from services.tts_service import EdgeTTSService
from services.visual_provider import PexelsUnsplashProvider
from services.caption_service import SRTGenerator
from services.video_renderer import FFmpegRenderer
from services.youtube_uploader import YouTubeUploader
from services.history import SQLiteHistory

def parse_args():
    parser = argparse.ArgumentParser(description="AutoShorts AI - Zero-Cost YouTube Shorts Generator")
    parser.add_argument("--channel", type=str, default="technology", help="The channel niche/context")
    parser.add_argument("--no-upload", action="store_true", help="Skip YouTube upload and save video locally")
    parser.add_argument("--dry-run", action="store_true", help="Run without calling external APIs (skips after history check)")
    parser.add_argument("--topic", type=str, help="Override topic generation with a specific topic")
    return parser.parse_args()

def main():
    args = parse_args()
    
    logger.info("Initializing AutoShorts AI", channel=args.channel, db_path=settings.db_path)
    
    # Initialize Dependencies
    history = SQLiteHistory()
    topic_gen = GroqTopicGenerator(channel_context=args.channel)
    script_gen = GroqScriptGenerator()
    tts = EdgeTTSService()
    caption = SRTGenerator()
    visual = PexelsUnsplashProvider()
    renderer = FFmpegRenderer()
    uploader = YouTubeUploader()
    
    # Wire Orchestrator
    orchestrator = Orchestrator(
        topic_generator=topic_gen,
        script_generator=script_gen,
        tts_service=tts,
        visual_provider=visual,
        caption_service=caption,
        video_renderer=renderer,
        youtube_uploader=uploader,
        history_backend=history
    )
    
    # Run Pipeline
    privacy = "private" if args.no_upload or args.dry_run else "private" # Defaulting to private for dev safety
    upload = not args.no_upload
    
    try:
        orchestrator.run(
            topic_override=args.topic,
            upload=upload,
            dry_run=args.dry_run,
            privacy=privacy
        )
    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user.")
        sys.exit(130)

if __name__ == "__main__":
    main()
