import math
from models.domain import Script
from services.interfaces import ICaptionService
from core.logger import logger

class SRTGenerator(ICaptionService):
    def generate_captions(self, script: Script, output_path: str) -> str:
        """
        Generates an SRT file based on the durations of the script segments.
        No paid transcription APIs are used.
        """
        logger.info("Generating SRT captions", output_path=output_path, segment_count=len(script.segments))
        
        srt_content = []
        current_time_sec = 0.0
        
        for i, segment in enumerate(script.segments, start=1):
            start_time = current_time_sec
            end_time = current_time_sec + segment.duration
            
            start_srt = self._format_time(start_time)
            end_srt = self._format_time(end_time)
            
            srt_content.append(str(i))
            srt_content.append(f"{start_srt} --> {end_srt}")
            srt_content.append(segment.text)
            srt_content.append("")  # Empty line between SRT blocks
            
            current_time_sec = end_time
            
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_content))
            
        return output_path
        
    def _format_time(self, seconds: float) -> str:
        """Format seconds to SRT time format: HH:MM:SS,mmm"""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"
