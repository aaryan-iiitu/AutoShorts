import asyncio
import subprocess
import edge_tts
from core.logger import logger
from core.exceptions import GenerationError
from services.interfaces import ITTSService
from utils.retry import api_retry

class EdgeTTSService(ITTSService):
    def __init__(self, voice: str = "en-US-ChristopherNeural"):
        self.voice = voice

    @api_retry()
    async def _generate_async(self, text: str, output_path: str):
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(output_path)

    def generate_audio(self, text: str, output_path: str) -> float:
        """
        Generates TTS and returns the duration of the audio in seconds using ffprobe.
        """
        logger.info("Generating audio via Edge TTS", text_length=len(text), output=output_path)
        try:
            asyncio.run(self._generate_async(text, output_path))
            duration = self._get_audio_duration(output_path)
            logger.debug("Audio generated successfully", duration=duration)
            return duration
        except Exception as e:
            logger.error("TTS generation failed", error=str(e))
            raise GenerationError(f"TTS Error: {str(e)}")

    def _get_audio_duration(self, file_path: str) -> float:
        """Helper to extract audio duration using ffprobe."""
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return float(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            raise GenerationError(f"FFprobe failed to get duration: {e.stderr}")
        except ValueError:
            raise GenerationError("FFprobe returned invalid duration format.")
