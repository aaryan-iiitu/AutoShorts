import os
import shutil
import subprocess
from config.settings import settings
from core.cost_guard import cost_guard
from core.exceptions import AutoShortsError, CostGuardError, UploadError
from core.logger import logger
from models.domain import VideoState, VideoAsset
from services.interfaces import (
    ITopicGenerator, IScriptGenerator, ITTSService,
    IVisualProvider, ICaptionService, IVideoRenderer,
    IYouTubeUploader, IHistoryBackend
)
from utils.fs import temporary_directory

class Orchestrator:
    def __init__(
        self,
        topic_generator: ITopicGenerator,
        script_generator: IScriptGenerator,
        tts_service: ITTSService,
        visual_provider: IVisualProvider,
        caption_service: ICaptionService,
        video_renderer: IVideoRenderer,
        youtube_uploader: IYouTubeUploader,
        history_backend: IHistoryBackend
    ):
        self.topic_gen = topic_generator
        self.script_gen = script_generator
        self.tts = tts_service
        self.visual = visual_provider
        self.caption = caption_service
        self.renderer = video_renderer
        self.uploader = youtube_uploader
        self.history = history_backend

    def run(self, topic_override: str = None, upload: bool = True, dry_run: bool = False, privacy: str = "private"):
        """
        Executes the fully automated zero-cost pipeline.
        Every stage has explicit failure handling, gracefully exiting on quota issues.
        """
        logger.info("Starting AutoShorts pipeline run", dry_run=dry_run, upload=upload)
        
        # 1. CostGuard Initial Check
        # In a real daemon, we might check if runs today >= MAX_RUNS_PER_DAY here.
        # But this script is invoked by a daily cron, so the cron enforces 1 run/day.
        # We ensure other limits start at 0.
        with cost_guard.lock:
            cost_guard.groq_requests = 0
            cost_guard.visual_searches = 0
            cost_guard.visual_downloads = 0

        state = VideoState(topic="")
        
        try:
            with temporary_directory() as temp_dir:
                # 2. History Check & Topic Generation
                if topic_override:
                    state.topic = topic_override
                    logger.info("Using provided topic override", topic=state.topic)
                else:
                    recent_topics = self.history.get_recent_topics()
                    if dry_run:
                        logger.info("DRY RUN: Skipping topic generation.")
                        state.topic = "Dry Run Topic"
                    else:
                        state.topic = self.topic_gen.generate_topic(recent_topics)
                        logger.info("Topic generated", topic=state.topic)

                if dry_run:
                    logger.info("DRY RUN completed successfully.")
                    return

                # 3. Script Generation
                state.script = self.script_gen.generate_script(state.topic)
                logger.info("Script generated", segment_count=len(state.script.segments))

                # 4. TTS (Per Segment)
                combined_audio_path = os.path.join(temp_dir, "narration.mp3")
                
                # In this phase we loop through segments and concatenate them.
                # Since edge-tts doesn't append easily, we generate separate files and concat them,
                # OR we just feed the full text to edge-tts and let the caption service deal with it.
                # Wait, the prompt explicitly said: "Edge TTS generates audio per segment. Measure each generated audio segment duration. Generate SRT timestamps from those durations."
                # Let's generate audio per segment, measure, and then concat.
                concat_list_path = os.path.join(temp_dir, "concat.txt")
                with open(concat_list_path, "w") as f:
                    for i, segment in enumerate(state.script.segments):
                        seg_path = os.path.join(temp_dir, f"seg_{i}.mp3")
                        duration = self.tts.generate_audio(segment.text, seg_path)
                        segment.audio_path = seg_path
                        segment.duration = duration
                        # Escape single quotes for ffmpeg concat demuxer
                        f.write(f"file '{seg_path.replace(chr(39), chr(39)+chr(92)+chr(39)+chr(39))}'\n")

                # Concat segments into one audio file using ffmpeg
                subprocess.run([
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0", 
                    "-i", concat_list_path, "-c", "copy", combined_audio_path
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                
                state.audio_path = combined_audio_path
                logger.info("TTS completed and concatenated")

                # 5. Caption Generation
                captions_path = os.path.join(temp_dir, "captions.srt")
                self.caption.generate_captions(state.script, captions_path)
                
                # 6. Visual Retrieval
                # Calculate total needed assets (roughly 1 asset per 15 seconds, or just max limit)
                # We'll just ask for the max allowed.
                asset_paths = self.visual.fetch_assets(state.script, max_assets=settings.max_visual_downloads_per_run, output_dir=temp_dir)
                state.assets = [VideoAsset(filepath=p, description="asset") for p in asset_paths]

                # 7. FFmpeg Rendering
                final_video_path = os.path.join(temp_dir, "final_short.mp4")
                self.renderer.render_video(state, final_video_path)
                state.final_video_path = final_video_path

                # 8. Validation
                if not os.path.exists(final_video_path) or os.path.getsize(final_video_path) < 1000:
                    raise AutoShortsError("Final video validation failed (file missing or too small).")

                # 9. YouTube Upload
                if upload:
                    raw_title = f"{state.topic}"
                    if len(raw_title) > 85:
                        raw_title = raw_title[:82] + "..."
                    title = f"{raw_title} | #shorts"
                    description = f"{state.script.segments[0].text}\n\nGenerated by AutoShorts AI."
                    youtube_url = self.uploader.upload_video(final_video_path, title, description, privacy_status=privacy)
                    state.youtube_url = youtube_url
                    
                    # 10. History Update
                    self.history.record_success(state.topic, youtube_url)
                else:
                    logger.info("Upload skipped via --no-upload flag")
                    # We can move the final file to the current directory for inspection since temp_dir will be wiped
                    shutil.copy2(final_video_path, "local_output.mp4")
                    logger.info("Video saved locally as local_output.mp4")

        except CostGuardError as e:
            logger.error("Pipeline stopped due to CostGuard limit", error=str(e))
            self._record_failure(state, str(e))
        except AutoShortsError as e:
            logger.error("Pipeline stopped due to domain error", error=str(e))
            self._record_failure(state, str(e))
        except Exception as e:
            logger.critical("Pipeline stopped due to unexpected error", error=str(e), exc_info=True)
            self._record_failure(state, f"Unexpected: {str(e)}")

    def _record_failure(self, state: VideoState, error_msg: str):
        if state.topic:
            try:
                self.history.record_failure(state.topic, error_msg)
            except Exception as e:
                logger.error("Failed to record failure in history", error=str(e))
