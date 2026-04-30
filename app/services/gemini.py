from __future__ import annotations

import json

from google import genai
from google.genai import errors
from google.genai import types
from pydantic import ValidationError

from app.config import get_settings
from app.constants import BASE_PROMPT, RETRY_PROMPT
from app.schemas import GeminiPlayersResponse


class GeminiExtractionError(Exception):
    pass


class GeminiService:
    def __init__(self) -> None:
        settings = get_settings()
        self.model_name = settings.gemini_model
        self.client = genai.Client(api_key=settings.gemini_api_key)

    def extract_players(self, image_bytes: bytes, mime_type: str) -> GeminiPlayersResponse:
        prompts = [BASE_PROMPT, f"{BASE_PROMPT}\n\n{RETRY_PROMPT}"]

        last_error: Exception | None = None
        for prompt in prompts:
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
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                last_error = exc
            except errors.APIError as exc:
                raise GeminiExtractionError(f"Gemini API request failed: {exc}") from exc

        raise GeminiExtractionError(
            f"Gemini returned invalid structured data after retry: {last_error}"
        )
