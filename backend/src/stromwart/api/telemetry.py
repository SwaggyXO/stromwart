from uuid import UUID

from fastapi import APIRouter, status

from stromwart.api.serializers import (
    event_read,
    feature_read,
    observation_read,
    session_read,
)
from stromwart.application.dependencies import ContainerDep, UnitOfWorkDep
from stromwart.contracts.common import EventCreate, EventRead, SessionCreate, SessionRead
from stromwart.contracts.features import FeatureRead
from stromwart.contracts.telemetry import ObservationCreate, ObservationRead
from stromwart.persistence import ObservationRow
from stromwart.repositories.telemetry import TelemetryRepository

router = APIRouter(tags=["telemetry"])


@router.post(
    "/events",
    response_model=EventRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create live event",
    description=(
        "Register a new live streaming event. "
        "All sessions and telemetry will be linked to this event."
    ),
)
async def create_event(value: EventCreate, uow: UnitOfWorkDep) -> EventRead:
    return event_read(await TelemetryRepository(uow.session).create_event(value))


@router.post(
    "/sessions",
    response_model=SessionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create session",
    description=(
        "Register a viewer session for a live event. "
        "Requires a unique (event_id, external_id) pair."
    ),
)
async def create_session(value: SessionCreate, uow: UnitOfWorkDep) -> SessionRead:
    return session_read(await TelemetryRepository(uow.session).create_session(value))


@router.post(
    "/telemetry/observations",
    response_model=ObservationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest telemetry observation",
    description=(
        "Submit a single per-chunk telemetry observation. "
        "Idempotent: duplicate (session_id, sequence) with same payload "
        "returns the existing record."
    ),
)
async def ingest_observation(
    value: ObservationCreate,
    container: ContainerDep,
) -> ObservationRead:
    observation_id, deduplicated = await container.ingestion.ingest(value)

    async with container.database.transaction() as uow:
        row = await uow.session.get(ObservationRow, observation_id)
        assert row is not None
        return observation_read(row, deduplicated)


@router.post(
    "/telemetry/replay",
    response_model=list[ObservationRead],
    summary="Replay telemetry batch",
    description=(
        "Submit a batch of observations for a single session (ordered by sequence). "
        "Used for replaying historical data or synthetic scenarios."
    ),
)
async def replay(
    values: list[ObservationCreate],
    container: ContainerDep,
) -> list[ObservationRead]:
    results = await container.ingestion.replay(values)

    async with container.database.transaction() as uow:
        observations = []

        for observation_id, deduplicated in results:
            row = await uow.session.get(ObservationRow, observation_id)
            assert row is not None
            observations.append(observation_read(row, deduplicated))

        return observations


@router.post(
    "/sessions/{session_id}/features",
    response_model=FeatureRead,
    summary="Materialize features",
    description=(
        "Compute and persist the feature vector for a session from its latest "
        "observations (up to 60 chunks)."
    ),
)
async def materialize_features(
    session_id: UUID,
    container: ContainerDep,
) -> FeatureRead:
    return feature_read(await container.features.materialize(session_id))
