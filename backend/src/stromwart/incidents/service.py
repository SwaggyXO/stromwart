from uuid import UUID

from sqlalchemy.exc import IntegrityError

from stromwart.contracts.features import FeatureVector
from stromwart.contracts.operations import Severity
from stromwart.database import Database
from stromwart.incidents.rules import AlertRules, RuleMatch
from stromwart.persistence import IncidentRow
from stromwart.repositories.incidents import IncidentRepository


class IncidentService:
    def __init__(self, database: Database, rules: AlertRules) -> None:
        self._database = database
        self._rules = rules

    async def detect(
        self,
        event_id: UUID,
        affected_slice: dict[str, str | None],
        features: FeatureVector,
    ) -> tuple[IncidentRow, bool, int] | None:
        """Return (incident, created, new_alert_count). created is True only on first create."""
        matches = self._rules.evaluate(features)
        if not matches:
            return None

        slice_key = self._slice_key(affected_slice)
        active_key = f"{event_id}:{slice_key}"

        async with self._database.transaction() as uow:
            repository = IncidentRepository(uow.session)
            alert_ids: list[str] = []

            for match in matches:
                alert = await repository.create_alert(
                    event_id,
                    slice_key,
                    match.rule_id,
                    match.severity,
                    match.observed_value,
                    match.threshold,
                )
                alert_ids.append(alert.id)

            existing = await repository.active_incident(active_key)
            if existing is not None:
                existing.evidence_ids = list(
                    dict.fromkeys(existing.evidence_ids + alert_ids)
                )
                await uow.flush()
                return existing, False, len(alert_ids)

            try:
                async with uow.savepoint():
                    incident = await repository.create_incident(
                        event_id,
                        slice_key,
                        affected_slice,
                        self._highest(matches),
                        alert_ids,
                    )
                    return incident, True, len(alert_ids)
            except IntegrityError:
                existing = await repository.active_incident(active_key)
                if existing is None:
                    raise
                existing.evidence_ids = list(
                    dict.fromkeys(existing.evidence_ids + alert_ids)
                )
                await uow.flush()
                return existing, False, len(alert_ids)

    @staticmethod
    def _slice_key(affected_slice: dict[str, str | None]) -> str:
        return "|".join(
            f"{key}={value or '_'}"
            for key, value in sorted(affected_slice.items())
        )

    @staticmethod
    def _highest(matches: list[RuleMatch]) -> Severity:
        ranking = {
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4,
        }
        return max(matches, key=lambda item: ranking[item.severity]).severity
