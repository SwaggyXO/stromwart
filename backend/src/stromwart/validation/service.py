from fastapi import HTTPException, status

from stromwart.contracts.telemetry import ObservationCreate
from stromwart.repositories import TelemetryRepository


class TelemetryValidator:
    async def validate(
        self,
        value: ObservationCreate,
        repo: TelemetryRepository,
    ) -> None:
        try:
            await repo.get_session(value.session_id)
        except Exception as exc:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "session does not exist",
            ) from exc

        previous = await repo.prior_timestamp(value.session_id, value.sequence)
        if previous and value.observed_at <= previous:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "observation timestamp is not monotonic",
            )
