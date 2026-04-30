from __future__ import annotations

import json
import logging
import time

from google import genai
from google.genai import errors
from google.genai import types
from pydantic import ValidationError

from app.config import get_settings
from app.constants import BASE_PROMPT, RETRY_PROMPT
from app.services.base import AIExtractionError, AIProviderError, BaseExtractionService
from app.schemas import GeminiPlayersResponse


logger = logging.getLogger(__name__)


class GeminiService(BaseExtractionService):
    provider_name = "gemini"

    def __init__(self, model_name: str | None = None) -> None:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise AIProviderError("GEMINI_API_KEY is not configured.")
        self.model_name = model_name or settings.gemini_model
        self.client = genai.Client(api_key=settings.gemini_api_key)

    def extract_players(self, image_bytes: bytes, mime_type: str, server_name: str) -> GeminiPlayersResponse:
        prompts = [BASE_PROMPT, f"{BASE_PROMPT}\n\n{RETRY_PROMPT}"]
        retryable_statuses = {429, 503}
        retry_delays = [2, 5, 10]

        last_error: Exception | None = None
        for prompt in prompts:
            try:
                for attempt in range(len(retry_delays) + 1):
                    try:
                        response = self.client.models.generate_content(
                            model=self.model_name,
                            contents=[
                                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                                prompt,
                            ],
                            config={
                                "response_mime_type": "application/json",
                                "response_schema": GeminiPlayersResponse,
                                "temperature": 0,
                            },
                        )

                        if getattr(response, "parsed", None):
                            return GeminiPlayersResponse.model_validate(response.parsed)

                        return GeminiPlayersResponse.model_validate(json.loads(response.text))
                    except errors.APIError as exc:
                        if exc.code in retryable_statuses and attempt < len(retry_delays):
                            delay = retry_delays[attempt]
                            logger.warning(
                                "Gemini retry for server=%s model=%s status=%s attempt=%s delay=%ss reason=%s",
                                server_name,
                                self.model_name,
                                exc.code,
                                attempt + 1,
                                delay,
                                exc,
                            )
                            time.sleep(delay)
                            continue

                        logger.error(
                            "Gemini request failed for server=%s model=%s status=%s reason=%s",
                            server_name,
                            self.model_name,
                            exc.code,
                            exc,
                        )
                        raise AIExtractionError(f"Gemini API request failed: {exc}") from exc
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                logger.warning(
                    "Gemini returned invalid structured data for server=%s model=%s reason=%s",
                    server_name,
                    self.model_name,
                    exc,
                )
                last_error = exc

        raise AIExtractionError(
            f"Gemini returned invalid structured data after retry: {last_error}"
        )
