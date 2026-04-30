from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.constants import ALLOWED_MIME_TYPES, CLUSTERS
from app.database import Base, engine, get_db
from app.schemas import ClusterServersResponse, ClusterSummaryResponse, UploadResponse
from app.services.gemini import GeminiExtractionError, GeminiService
from app.services.storage import get_cluster_servers, get_cluster_summary, replace_cluster_data


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="YW Web Rating", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def validate_upload_payload(cluster_id: int, files: list[UploadFile], server_names: list[str]) -> list[str]:
    expected_servers = CLUSTERS.get(cluster_id)
    if not expected_servers:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found.")

    if len(files) != 4 or len(server_names) != 4:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Exactly 4 screenshots and 4 server names are required.",
        )

    normalized_names = [name.strip().lower() for name in server_names]
    if sorted(normalized_names) != sorted(expected_servers):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Upload screenshots for all servers in cluster {cluster_id}: {', '.join(expected_servers)}",
        )

    for upload in files:
        if upload.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{upload.filename} is not a supported image file.",
            )

    return normalized_names


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse("app/static/index.html")


@app.get("/health")
async def healthcheck():
    return {"status": "ok"}


@app.post("/upload/{cluster}", response_model=UploadResponse)
async def upload_cluster_screenshots(
    cluster: int,
    files: list[UploadFile] = File(...),
    server_names: list[str] = Form(...),
    db: Session = Depends(get_db),
):
    normalized_names = validate_upload_payload(cluster, files, server_names)
    gemini_service = GeminiService()

    extracted_payload = {}
    for server_name, upload in zip(normalized_names, files):
        image_bytes = await upload.read()
        if not image_bytes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{upload.filename} is empty.",
            )
        try:
            extracted = gemini_service.extract_players(
                image_bytes=image_bytes,
                mime_type=upload.content_type,
                server_name=server_name,
            )
        except GeminiExtractionError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to parse screenshot for {server_name}: {exc}",
            ) from exc
        extracted_payload[server_name] = extracted.players

    players_saved = replace_cluster_data(db=db, cluster_id=cluster, payload=extracted_payload)
    return UploadResponse(
        cluster_id=cluster,
        processed_servers=normalized_names,
        players_saved=players_saved,
        message="Cluster data uploaded, recognized, and saved successfully.",
    )


@app.get("/servers/{cluster}", response_model=ClusterServersResponse)
async def get_servers(cluster: int, db: Session = Depends(get_db)):
    return get_cluster_servers(db=db, cluster_id=cluster)


@app.get("/summary/{cluster}", response_model=ClusterSummaryResponse)
async def get_summary(cluster: int, db: Session = Depends(get_db)):
    return get_cluster_summary(db=db, cluster_id=cluster)
