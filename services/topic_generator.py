import json
from typing import List
from groq import Groq
from groq import APIError, RateLimitError
from config.settings import settings
from core.cost_guard import cost_guard
from core.exceptions import QuotaExceededError, GenerationError
from core.logger import logger
from services.interfaces import ITopicGenerator
from utils.retry import api_retry
from utils.retry import api_retry

class GroqTopicGenerator(ITopicGenerator):
    def __init__(self, channel_context: str = "technology"):
        if not settings.groq_api_key:
            raise GenerationError("GROQ_API_KEY is not set.")
        self.client = Groq(api_key=settings.groq_api_key, timeout=settings.network_timeout_seconds)
        self.channel_context = channel_context

    @api_retry()
    def generate_topic(self, recent_topics: List[str]) -> str:
        cost_guard.increment_groq_requests()
        logger.info("Generating new topic via Groq", context=self.channel_context)

        system_prompt = f"You are an expert YouTube Shorts creator in the '{self.channel_context}' niche."
        user_prompt = (
            "Generate ONE highly engaging, viral topic for a YouTube Short.\n"
            "Respond ONLY with the topic text itself. Do not use quotes or introductory text.\n"
        )
        if recent_topics:
            user_prompt += f"DO NOT use any of these recent topics: {', '.join(recent_topics)}\n"

        try:
            response = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=50
            )
            topic = response.choices[0].message.content.strip().strip('"').strip("'")
            if not topic:
                raise GenerationError("Received empty topic from Groq.")
            return topic

        except RateLimitError as e:
            logger.error("Groq rate limit exceeded", error=str(e))
            raise QuotaExceededError(f"Groq Rate Limit: {str(e)}")
        except APIError as e:
            logger.error("Groq API error", error=str(e))
            raise GenerationError(f"Groq API Error: {str(e)}")
        except Exception as e:
            logger.error("Unexpected error in topic generation", error=str(e))
            raise GenerationError(f"Unexpected: {str(e)}")
