from __future__ import annotations

import base64
import json
import logging
import time

from openai import APIError, APIStatusError, OpenAI
from pydantic import ValidationError

from app.config import get_settings
from app.constants import BASE_PROMPT, RETRY_PROMPT
from app.services.base import AIExtractionError, AIProviderError, BaseExtractionService
from app.schemas import GeminiPlayersResponse


logger = logging.getLogger(__name__)


class QwenService(BaseExtractionService):
    provider_name = "qwen"

    def __init__(self, model_name: str | None = None) -> None:
        settings = get_settings()
        if not settings.qwen_api_key:
            raise AIProviderError("QWEN_API_KEY is not configured.")
        self.model_name = model_name or settings.qwen_model
        self.client = OpenAI(
            api_key=settings.qwen_api_key,
            base_url=settings.qwen_base_url,
        )

    def extract_players(self, image_bytes: bytes, mime_type: str, server_name: str) -> GeminiPlayersResponse:
        prompts = [BASE_PROMPT, f"{BASE_PROMPT}\n\n{RETRY_PROMPT}"]
        retryable_statuses = {429, 503}
        retry_delays = [2, 5, 10]
        image_base64 = base64.b64encode(image_bytes).decode("ascii")
        image_url = f"data:{mime_type};base64,{image_base64}"

        last_error: Exception | None = None
        for prompt in prompts:
            try:
                for attempt in range(len(retry_delays) + 1):
                    try:
                        response = self.client.chat.completions.create(
                            model=self.model_name,
                            temperature=0,
                            response_format={"type": "json_object"},
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": prompt},
                                        {"type": "image_url", "image_url": {"url": image_url}},
                                    ],
                                }
                            ],
                        )
                        content = response.choices[0].message.content or ""
                        return GeminiPlayersResponse.model_validate(json.loads(content))
                    except APIStatusError as exc:
                        if exc.status_code in retryable_statuses and attempt < len(retry_delays):
                            delay = retry_delays[attempt]
                            logger.warning(
                                "Qwen retry for server=%s model=%s status=%s attempt=%s delay=%ss reason=%s",
                                server_name,
                                self.model_name,
                                exc.status_code,
                                attempt + 1,
                                delay,
                                exc,
                            )
                            time.sleep(delay)
                            continue

                        logger.error(
                            "Qwen request failed for server=%s model=%s status=%s reason=%s",
                            server_name,
                            self.model_name,
                            exc.status_code,
                            exc,
                        )
                        raise AIExtractionError(f"Qwen API request failed: {exc}") from exc
                    except APIError as exc:
                        logger.error(
                            "Qwen request failed for server=%s model=%s reason=%s",
                            server_name,
                            self.model_name,
                            exc,
                        )
                        raise AIExtractionError(f"Qwen API request failed: {exc}") from exc
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                logger.warning(
                    "Qwen returned invalid structured data for server=%s model=%s reason=%s",
                    server_name,
                    self.model_name,
                    exc,
                )
                last_error = exc

        raise AIExtractionError(
            f"Qwen returned invalid structured data after retry: {last_error}"
        )
