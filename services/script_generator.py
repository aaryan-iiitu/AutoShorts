import json
from groq import Groq
from groq import APIError, RateLimitError
from config.settings import settings
from core.cost_guard import cost_guard
from core.exceptions import QuotaExceededError, GenerationError
from core.logger import logger
from models.domain import Script, ScriptSegment
from services.interfaces import IScriptGenerator
from utils.retry import api_retry
from utils.network import get_session

class GroqScriptGenerator(IScriptGenerator):
    def __init__(self):
        if not settings.groq_api_key:
            raise GenerationError("GROQ_API_KEY is not set.")
        self.client = Groq(api_key=settings.groq_api_key, http_client=get_session())

    @api_retry()
    def generate_script(self, topic: str) -> Script:
        cost_guard.increment_groq_requests()
        logger.info("Generating script via Groq", topic=topic)

        system_prompt = (
            "You are a master scriptwriter for YouTube Shorts. "
            "Write a highly engaging, fast-paced script designed to retain viewer attention. "
            "You MUST output the script in strict JSON format matching exactly this schema:\n"
            "{\n"
            '  "segments": [\n'
            '    {"text": "Your hook here"},\n'
            '    {"text": "Next sentence"},\n'
            '    {"text": "Call to action"}\n'
            "  ]\n"
            "}\n"
            "Keep each segment between 1 to 3 short sentences. "
            "The total script length should be around 45 to 60 seconds when spoken (approx 120-150 words). "
            "Output ONLY valid JSON. No markdown wrappers. No introduction."
        )
        
        user_prompt = f"Topic: {topic}"

        try:
            response = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            raw_content = response.choices[0].message.content.strip()
            data = json.loads(raw_content)
            
            if "segments" not in data or not isinstance(data["segments"], list):
                raise GenerationError("Invalid JSON schema returned by Groq.")
                
            segments = [ScriptSegment(text=seg.get("text", "")) for seg in data["segments"] if seg.get("text")]
            
            if not segments:
                raise GenerationError("No valid segments generated.")
                
            return Script(topic=topic, segments=segments)

        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON from Groq", error=str(e), content=raw_content)
            raise GenerationError(f"JSON Parse Error: {str(e)}")
        except RateLimitError as e:
            logger.error("Groq rate limit exceeded", error=str(e))
            raise QuotaExceededError(f"Groq Rate Limit: {str(e)}")
        except APIError as e:
            logger.error("Groq API error", error=str(e))
            raise GenerationError(f"Groq API Error: {str(e)}")
        except Exception as e:
            logger.error("Unexpected error in script generation", error=str(e))
            raise GenerationError(f"Unexpected: {str(e)}")
