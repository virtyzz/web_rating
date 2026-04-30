from __future__ import annotations

from app.config import get_settings
from app.constants import SUPPORTED_PROVIDERS
from app.schemas import ProviderOption, ProvidersResponse
from app.services.base import AIProviderError, BaseExtractionService
from app.services.gemini import GeminiService
from app.services.qwen import QwenService


def get_extraction_service(provider: str, model: str | None = None) -> BaseExtractionService:
    normalized_provider = provider.strip().lower()
    if normalized_provider not in SUPPORTED_PROVIDERS:
        raise AIProviderError(f"Unsupported AI provider: {provider}")

    provider_models = SUPPORTED_PROVIDERS[normalized_provider]
    resolved_model = model.strip() if model else provider_models[0]
    if resolved_model not in provider_models:
        raise AIProviderError(
            f"Unsupported model '{resolved_model}' for provider '{normalized_provider}'."
        )

    if normalized_provider == "gemini":
        return GeminiService(model_name=resolved_model)
    if normalized_provider == "qwen":
        return QwenService(model_name=resolved_model)

    raise AIProviderError(f"Unsupported AI provider: {provider}")


def get_provider_options() -> ProvidersResponse:
    settings = get_settings()
    providers = [
        ProviderOption(
            provider="gemini",
            models=SUPPORTED_PROVIDERS["gemini"],
            enabled=bool(settings.gemini_api_key),
            default_model=settings.gemini_model,
        ),
        ProviderOption(
            provider="qwen",
            models=SUPPORTED_PROVIDERS["qwen"],
            enabled=bool(settings.qwen_api_key),
            default_model=settings.qwen_model,
        ),
    ]
    default_provider = settings.ai_provider if settings.ai_provider in SUPPORTED_PROVIDERS else "gemini"
    return ProvidersResponse(default_provider=default_provider, providers=providers)
