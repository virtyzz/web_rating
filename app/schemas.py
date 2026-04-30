from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class PlayerExtraction(BaseModel):
    name: str = Field(min_length=1)
    rank: int
    points: int
    kills: int

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = " ".join(value.split()).strip()
        if not cleaned:
            raise ValueError("Player name cannot be empty.")
        return cleaned

    @field_validator("rank", "points", "kills", mode="before")
    @classmethod
    def parse_ints(cls, value):
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            normalized = (
                value.replace(" ", "")
                .replace(",", "")
                .replace("_", "")
                .replace("O", "0")
                .replace("o", "0")
            )
            if normalized.lstrip("-").isdigit():
                return int(normalized)
        raise ValueError("Numeric field must be an integer.")


class GeminiPlayersResponse(BaseModel):
    players: list[PlayerExtraction]


class PlayerOut(BaseModel):
    name: str
    rank: int
    points: int
    kills: int
    updated_at: datetime


class ServerTableResponse(BaseModel):
    server_name: str
    players: list[PlayerOut]
    updated_at: datetime | None = None


class ClusterServersResponse(BaseModel):
    cluster_id: int
    is_complete: bool
    required_servers: list[str]
    servers: list[ServerTableResponse]


class SummaryPlayerOut(BaseModel):
    name: str
    total_points: int
    total_kills: int
    best_rank: int


class ClusterSummaryResponse(BaseModel):
    cluster_id: int
    generated_at: datetime
    players: list[SummaryPlayerOut]


class UploadResponse(BaseModel):
    cluster_id: int
    provider: str
    model: str
    processed_servers: list[str]
    players_saved: int
    message: str


class ProviderOption(BaseModel):
    provider: str
    models: list[str]
    enabled: bool
    default_model: str


class ProvidersResponse(BaseModel):
    default_provider: str
    providers: list[ProviderOption]
