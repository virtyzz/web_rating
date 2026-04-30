from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas import GeminiPlayersResponse


class AIExtractionError(Exception):
    pass


class AIProviderError(Exception):
    pass


class BaseExtractionService(ABC):
    provider_name: str
    model_name: str

    @abstractmethod
    def extract_players(self, image_bytes: bytes, mime_type: str, server_name: str) -> GeminiPlayersResponse:
        raise NotImplementedError
