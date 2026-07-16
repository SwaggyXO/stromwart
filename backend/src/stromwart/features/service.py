from statistics import fmean, pstdev
from uuid import UUID

from stromwart.contracts.features import FeatureVector
from stromwart.database import Database
from stromwart.errors import ValidationError
from stromwart.persistence import FeatureSnapshotRow, ObservationRow
from stromwart.repositories.telemetry import TelemetryRepository


class FeatureService:
    schema_version = "telemetry-v1"

    def __init__(self, database: Database) -> None:
        self._database = database

    async def materialize(self, session_id: UUID, limit: int = 60) -> FeatureSnapshotRow:
        async with self._database.transaction() as uow:
            telemetry = TelemetryRepository(uow.session)
            await telemetry.get_session(session_id)
            observations = await telemetry.observations(session_id, limit)

            values = self.from_observations(session_id, observations)
            snapshot = FeatureSnapshotRow(
                session_id=str(session_id),
                schema_version=values.schema_version,
                values=values.model_dump(mode="json"),
            )
            uow.session.add(snapshot)
            await uow.flush()
            return snapshot

    def from_observations(
        self,
        session_id: UUID,
        observations: list[ObservationRow],
    ) -> FeatureVector:
        if not observations:
            raise ValidationError("cannot materialize features without observations")

        throughputs = [item.throughput_kbps for item in observations]
        buffers = [item.buffer_level_ms for item in observations]
        rebuffer_total = sum(item.rebuffer_duration_ms for item in observations)
        duration_total = sum(item.duration_ms for item in observations)

        return FeatureVector(
            session_id=session_id,
            window_start=observations[0].observed_at,
            window_end=observations[-1].observed_at,
            observation_count=len(observations),
            throughput_mean_kbps=fmean(throughputs),
            throughput_std_kbps=(
                pstdev(throughputs) if len(throughputs) > 1 else 0.0
            ),
            buffer_mean_ms=fmean(buffers),
            buffer_min_ms=min(buffers),
            rebuffer_total_ms=rebuffer_total,
            stall_ratio=rebuffer_total / duration_total,
            downswitch_count=sum(
                current.bitrate_kbps < previous.bitrate_kbps
                for previous, current in zip(observations, observations[1:])
            ),
            latest_bitrate_kbps=observations[-1].bitrate_kbps,
            latest_packet_loss_pct=observations[-1].packet_loss_pct,
        )
