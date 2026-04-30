from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.constants import CLUSTERS
from app.models import ServerData
from app.schemas import (
    ClusterServersResponse,
    ClusterSummaryResponse,
    PlayerExtraction,
    PlayerOut,
    ServerTableResponse,
    SummaryPlayerOut,
)


def validate_cluster(cluster_id: int) -> list[str]:
    servers = CLUSTERS.get(cluster_id)
    if not servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cluster not found. Use 1 or 2.",
        )
    return servers


def replace_cluster_data(
    db: Session,
    cluster_id: int,
    payload: dict[str, list[PlayerExtraction]],
) -> int:
    validate_cluster(cluster_id)
    now = datetime.now(timezone.utc)

    db.execute(delete(ServerData).where(ServerData.cluster_id == cluster_id))

    rows: list[ServerData] = []
    for server_name, players in payload.items():
        for player in players:
            rows.append(
                ServerData(
                    server_name=server_name,
                    cluster_id=cluster_id,
                    player_name=player.name,
                    rank=player.rank,
                    points=player.points,
                    kills=player.kills,
                    updated_at=now,
                )
            )

    db.add_all(rows)
    db.commit()
    return len(rows)


def cluster_is_complete(db: Session, cluster_id: int) -> bool:
    required_servers = validate_cluster(cluster_id)
    stmt = (
        select(ServerData.server_name)
        .where(ServerData.cluster_id == cluster_id)
        .group_by(ServerData.server_name)
    )
    present_servers = {row[0] for row in db.execute(stmt).all()}
    return set(required_servers) == present_servers


def get_cluster_servers(db: Session, cluster_id: int) -> ClusterServersResponse:
    required_servers = validate_cluster(cluster_id)
    stmt = (
        select(ServerData)
        .where(ServerData.cluster_id == cluster_id)
        .order_by(ServerData.server_name, ServerData.rank.asc(), ServerData.player_name.asc())
    )
    rows = db.execute(stmt).scalars().all()

    grouped: dict[str, list[PlayerOut]] = defaultdict(list)
    updated_map: dict[str, datetime] = {}

    for row in rows:
        grouped[row.server_name].append(
            PlayerOut(
                name=row.player_name,
                rank=row.rank,
                points=row.points,
                kills=row.kills,
                updated_at=row.updated_at,
            )
        )
        updated_map[row.server_name] = row.updated_at

    servers = [
        ServerTableResponse(
            server_name=server_name,
            players=grouped.get(server_name, []),
            updated_at=updated_map.get(server_name),
        )
        for server_name in required_servers
    ]

    return ClusterServersResponse(
        cluster_id=cluster_id,
        is_complete=set(required_servers) == set(grouped.keys()),
        required_servers=required_servers,
        servers=servers,
    )


def get_cluster_summary(db: Session, cluster_id: int) -> ClusterSummaryResponse:
    required_servers = validate_cluster(cluster_id)
    if not cluster_is_complete(db, cluster_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Summary is unavailable until all 4 servers are loaded for cluster {cluster_id}: "
                f"{', '.join(required_servers)}"
            ),
        )

    stmt = (
        select(
            ServerData.player_name,
            func.sum(ServerData.points),
            func.sum(ServerData.kills),
            func.min(ServerData.rank),
            func.max(ServerData.updated_at),
        )
        .where(ServerData.cluster_id == cluster_id)
        .group_by(ServerData.player_name)
        .order_by(func.sum(ServerData.points).desc(), func.sum(ServerData.kills).desc())
    )
    rows = db.execute(stmt).all()

    generated_at = max((row[4] for row in rows), default=datetime.now(timezone.utc))
    players = [
        SummaryPlayerOut(
            name=row[0],
            total_points=row[1],
            total_kills=row[2],
            best_rank=row[3],
        )
        for row in rows
    ]

    return ClusterSummaryResponse(
        cluster_id=cluster_id,
        generated_at=generated_at,
        players=players,
    )

