import os
import subprocess
import glob
from typing import List, Optional
from config.settings import settings
from core.exceptions import RenderingError
from core.logger import logger
from models.domain import VideoState
from services.interfaces import IVideoRenderer

class FFmpegRenderer(IVideoRenderer):
    def render_video(self, state: VideoState, output_path: str) -> str:
        """
        Compiles audio, video assets, and captions into a final MP4.
        Ensures 1080x1920, 9:16, H.264, AAC, 30 FPS.
        Gracefully handles static images by looping them for 5 seconds.
        """
        logger.info("Starting FFmpeg rendering", output=output_path)
        
        if not state.assets:
            raise RenderingError("No visual assets provided for rendering.")
        if not state.audio_path or not os.path.exists(state.audio_path):
            raise RenderingError("Narration audio is missing.")
            
        temp_dir = os.path.dirname(state.audio_path)
        captions_path = os.path.join(temp_dir, "captions.srt")
        if not os.path.exists(captions_path):
            logger.warning("Captions file missing, video will render without subtitles.")
            captions_path = None

        bg_music_path = self._get_background_music()
        
        cmd = ["ffmpeg", "-y"]
        
        # Inputs
        for asset in state.assets:
            # If the asset is an image from Unsplash, we must loop it so it behaves like a video stream
            if asset.filepath.lower().endswith(('.jpg', '.jpeg', '.png')):
                cmd.extend(["-loop", "1", "-t", "10", "-i", asset.filepath]) # 10 seconds is usually enough for a short clip
            else:
                cmd.extend(["-i", asset.filepath])
            
        cmd.extend(["-i", state.audio_path])
        audio_idx = len(state.assets)
        
        if bg_music_path:
            cmd.extend(["-i", bg_music_path])
            bg_music_idx = audio_idx + 1
            
        filter_complex = []
        w, h = settings.video_width, settings.video_height
        video_streams = []
        
        for i in range(len(state.assets)):
            # Force aspect ratio, crop, set SAR, force fps
            filter_complex.append(f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1,fps=30,format=yuv420p[v{i}]")
            video_streams.append(f"[v{i}]")
            
        # Concat all videos
        concat_str = "".join(video_streams)
        filter_complex.append(f"{concat_str}concat=n={len(state.assets)}:v=1:a=0[vconcat]")
        
        last_v_stream = "[vconcat]"
        if captions_path:
            escaped_srt = captions_path.replace("\\", "/").replace(":", "\\:")
            filter_complex.append(f"{last_v_stream}subtitles={escaped_srt}[vsub]")
            last_v_stream = "[vsub]"
            
        # Audio mixing
        if bg_music_path:
            filter_complex.append(f"[{audio_idx}:a]volume=1.0[anarr]")
            filter_complex.append(f"[{bg_music_idx}:a]volume=0.1[abgm]")
            filter_complex.append(f"[anarr][abgm]amix=inputs=2:duration=first:dropout_transition=2[aout]")
        else:
            filter_complex.append(f"[{audio_idx}:a]volume=1.0[aout]")
            
        cmd.extend(["-filter_complex", ";".join(filter_complex)])
        cmd.extend(["-map", last_v_stream, "-map", "[aout]"])
        
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",  # Stop when the shortest stream ends (which is our audio duration)
            output_path
        ])
        
        try:
            logger.debug("Running FFmpeg", command=" ".join(cmd))
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            if not os.path.exists(output_path):
                raise RenderingError("FFmpeg completed but output file not found.")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error("FFmpeg failed", stderr=e.stderr)
            raise RenderingError(f"FFmpeg Error: {e.stderr}")

    def _get_background_music(self) -> Optional[str]:
        music_dir = os.path.join("assets", "music")
        if not os.path.exists(music_dir):
            return None
            
        import random
        tracks = glob.glob(os.path.join(music_dir, "*.mp3")) + glob.glob(os.path.join(music_dir, "*.wav"))
        if not tracks:
            return None
        return random.choice(tracks)
