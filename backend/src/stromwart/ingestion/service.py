
from sqlalchemy.exc import IntegrityError

from stromwart.contracts.telemetry import ObservationCreate
from stromwart.database import Database, UnitOfWork
from stromwart.errors import ConflictError, ValidationError
from stromwart.persistence import ObservationRow
from stromwart.repositories.telemetry import TelemetryRepository


class IngestionService:
    def __init__(self, database: Database) -> None:
        self._database = database

    async def ingest(self, value: ObservationCreate) -> tuple[str, bool]:
        async with self._database.transaction() as uow:
            repository = TelemetryRepository(uow.session)
            row, deduplicated = await self._insert(uow, repository, value)
            return row.id, deduplicated

    async def replay(
        self,
        observations: list[ObservationCreate],
    ) -> list[tuple[str, bool]]:
        if not observations:
            raise ValidationError("replay requires at least one observation")

        session_ids = {item.session_id for item in observations}
        if len(session_ids) != 1:
            raise ValidationError("a replay batch must contain exactly one session")

        ordered = sorted(observations, key=lambda item: item.sequence)
        if len({item.sequence for item in ordered}) != len(ordered):
            raise ValidationError("replay contains duplicate sequence values")

        async with self._database.transaction() as uow:
            repository = TelemetryRepository(uow.session)
            results: list[tuple[str, bool]] = []

            for observation in ordered:
                row, deduplicated = await self._insert(
                    uow,
                    repository,
                    observation,
                )
                results.append((row.id, deduplicated))

            return results

    async def _insert(
        self,
        uow: UnitOfWork,
        repository: TelemetryRepository,
        value: ObservationCreate,
    ) -> tuple[ObservationRow, bool]:
        await repository.get_session(value.session_id)

        prior = await repository.timestamp_before(
            value.session_id,
            value.sequence,
        )
        if prior is not None and value.observed_at <= prior:
            raise ValidationError("observed_at must increase with sequence")

        payload_hash = repository.payload_hash(value)
        existing = await repository.get_observation(
            value.session_id,
            value.sequence,
        )

        if existing is not None:
            if existing.payload_hash != payload_hash:
                raise ConflictError(
                    "sequence already exists with a different telemetry payload"
                )
            return existing, True

        try:
            async with uow.savepoint():
                return await repository.add_observation(value)
        except IntegrityError:
            existing = await repository.get_observation(
                value.session_id,
                value.sequence,
            )
            if existing is None:
                raise

            if existing.payload_hash != payload_hash:
                raise ConflictError(
                    "sequence already exists with a different telemetry payload"
                )

            return existing, True
