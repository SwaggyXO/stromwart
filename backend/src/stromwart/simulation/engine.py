"""Simulation engine — orchestrates scenario execution."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import text

from stromwart.contracts.actions import ProposalCreate
from stromwart.contracts.agents import ToolCall, ToolName, ToolResult
from stromwart.contracts.common import EventCreate, SessionCreate, SourceType
from stromwart.contracts.features import FeatureVector
from stromwart.contracts.operations import IncidentState
from stromwart.orchestrator.state import CognitiveState, IncidentPhase
from stromwart.persistence import IncidentRow
from stromwart.repositories.actions import ActionRepository
from stromwart.repositories.agents import AgentRunRepository
from stromwart.repositories.audit import AuditRepository
from stromwart.repositories.incidents import IncidentRepository
from stromwart.repositories.telemetry import TelemetryRepository
from stromwart.simulation.scenarios import SCENARIOS, DegradationPhase, ScenarioProfile
from stromwart.simulation.telemetry_gen import (
    create_session_pool,
    generate_observations_for_phase,
)

if TYPE_CHECKING:
    from stromwart.application.container import Container

logger = logging.getLogger(__name__)

_CLEAR_SIMULATION_DATA = text(
    "TRUNCATE TABLE "
    "audit_events, "
    "action_executions, "
    "action_proposals, "
    "agent_runs, "
    "alerts, "
    "incidents, "
    "feature_snapshots, "
    "forecasts, "
    "predictions, "
    "observations, "
    "sessions, "
    "events "
    "RESTART IDENTITY CASCADE"
)

_MITIGATOR_ACTION_MAP = {
    "scale_cdn_edge": "increase_cdn_capacity",
    "reroute_traffic": "adjust_traffic_routing",
    "increase_bandwidth_allocation": "recommend_abr_profile",
    "scale_origin": "increase_cdn_capacity",
    "investigate_only": "investigate_only",
}

_AGENT_RUN_STATE_MAP = {
    "detector": "gathering_evidence",
    "diagnostician": "gathering_evidence",
    "mitigator": "waiting_for_human",
    "verifier": "completed",
}


def _best_diagnostician_observation(state: CognitiveState) -> dict[str, object] | None:
    """Pick the strongest diagnostician output; avoid loop-poisoned 'Unknown' overwrites."""
    candidates = [
        step.observation
        for step in state.step_history
        if step.agent_name == "diagnostician" and step.observation
    ]
    if not candidates:
        return None

    def rank(obs: dict[str, object]) -> tuple[float, float]:
        hypothesis = str(obs.get("hypothesis", ""))
        raw_conf = obs.get("confidence", 0)
        confidence = float(raw_conf) if isinstance(raw_conf, (int, float, str)) else 0.0
        if hypothesis == "Unknown root cause":
            return (-1.0, confidence)
        return (confidence, confidence)

    return max(candidates, key=rank)


def compute_simulation_progress(
    phase_start_minute: float,
    phase_end_minute: float,
    batches_completed: float,
    batch_count: int,
    total_minutes: float,
) -> float:
    """Map batch progress within a phase to overall scenario progress [0, 1]."""
    phase_span = phase_end_minute - phase_start_minute
    fraction = min(batches_completed / max(batch_count, 1), 1.0)
    sim_minute = phase_start_minute + phase_span * fraction
    return min(max(sim_minute / total_minutes, 0.0), 1.0)


class SimulationStatus(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


def _sanitize_target_scope(
    raw: dict[str, object],
    *,
    event_id: str | None,
    session_count: int,
) -> dict[str, str | int | float | bool | None]:
    """ProposalCreate.target_scope only allows scalar values."""
    scope: dict[str, str | int | float | bool | None] = {}
    for key, value in raw.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            scope[key] = value
    if event_id and "event_id" not in scope:
        scope["event_id"] = event_id
    session_count_value = scope.get("session_count")
    if not isinstance(session_count_value, int) or session_count_value < 0:
        scope["session_count"] = session_count
    return scope


class SimulationEngine:
    """Manages scenario lifecycle and telemetry injection."""

    def __init__(self, container: Container) -> None:
        self._container = container
        self._status = SimulationStatus.IDLE
        self._current_scenario: ScenarioProfile | None = None
        self._task: asyncio.Task[None] | None = None
        self._event_id: str | None = None
        self._progress: float = 0.0
        self._current_phase: str = ""
        self._sessions_provisioned: int = 0

    @property
    def status(self) -> SimulationStatus:
        return self._status

    @property
    def progress(self) -> float:
        return self._progress

    @property
    def current_phase(self) -> str:
        return self._current_phase

    @property
    def scenario_id(self) -> str | None:
        return self._current_scenario.id if self._current_scenario else None

    @property
    def event_id(self) -> str | None:
        return self._event_id

    @property
    def current_scenario(self) -> ScenarioProfile | None:
        return self._current_scenario

    @property
    def sessions_provisioned(self) -> int:
        return self._sessions_provisioned

    async def start(self, scenario_id: str, speed_multiplier: float = 10.0) -> str:
        """Start a simulation scenario."""
        if self._status == SimulationStatus.RUNNING:
            raise RuntimeError("Simulation already running. Stop it first.")

        scenario = SCENARIOS.get(scenario_id)
        if not scenario:
            raise ValueError(
                f"Unknown scenario: {scenario_id}. Available: {list(SCENARIOS.keys())}"
            )

        await self._clear_simulation_data()
        self._container.reset_eval_state()

        self._current_scenario = scenario
        self._status = SimulationStatus.RUNNING
        self._progress = 0.0
        self._current_phase = "Initializing scenario"
        self._sessions_provisioned = min(scenario.sessions_peak // 100, 500)

        async with self._container.database.transaction() as uow:
            repo = TelemetryRepository(uow.session)
            event_row = await repo.create_event(
                EventCreate(
                    name=scenario.name,
                    content_type=scenario.category,
                    starts_at=datetime.now(UTC),
                )
            )
            self._event_id = event_row.id

        self._task = asyncio.create_task(self._run(scenario, speed_multiplier))
        return self._event_id

    async def stop(self) -> None:
        """Stop the running simulation."""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._event_id is not None:
            async with self._container.database.transaction() as uow:
                await TelemetryRepository(uow.session).end_event(self._event_id)
        self._status = SimulationStatus.IDLE
        self._progress = 0.0
        self._current_phase = ""
        self._event_id = None
        self._container.reset_eval_state()

    async def _clear_simulation_data(self) -> None:
        """Remove prior demo run data so each simulation starts from a clean slate."""
        async with self._container.database.transaction() as uow:
            await uow.session.execute(_CLEAR_SIMULATION_DATA)

    async def _run(self, scenario: ScenarioProfile, speed_multiplier: float) -> None:
        """Execute the full scenario lifecycle."""
        try:
            event_id = self._event_id
            assert event_id is not None

            session_count = min(scenario.sessions_peak // 100, 500)
            self._sessions_provisioned = session_count
            session_pool = create_session_pool(event_id, session_count)
            session_ids: list[str] = []

            async with self._container.database.transaction() as uow:
                repo = TelemetryRepository(uow.session)
                for session in session_pool:
                    row = await repo.create_session(
                        SessionCreate(
                            event_id=UUID(event_id),
                            external_id=session["external_id"],
                            client_type=session["client_type"],
                            source_type=SourceType.SYNTHETIC,
                            started_at=datetime.fromisoformat(session["started_at"]),
                            region=session.get("region"),
                        )
                    )
                    session_ids.append(row.id)

            total_minutes = scenario.duration_minutes
            self._current_phase = "Provisioning sessions"
            self._progress = min(1.0, 0.5 / total_minutes)

            sequence_counters = dict.fromkeys(session_ids, 0)
            sim_start = datetime.now(UTC)

            for phase in scenario.phases:
                self._current_phase = phase.description
                phase_start = sim_start + timedelta(minutes=phase.start_minute)

                observations = generate_observations_for_phase(
                    phase=phase,
                    session_ids=session_ids,
                    phase_start=phase_start,
                    sequence_counters=sequence_counters,
                    sample_rate=0.15,
                )

                batch_size = 50
                batch_count = max(1, (len(observations) + batch_size - 1) // batch_size)
                phase_duration_real = (
                    (phase.end_minute - phase.start_minute) * 60 / speed_multiplier
                )

                for index in range(0, len(observations), batch_size):
                    batch = observations[index : index + batch_size]
                    batch_num = index // batch_size
                    for obs_idx, obs in enumerate(batch):
                        try:
                            await self._container.ingestion.ingest(obs)
                        except Exception as exc:
                            logger.warning("Observation ingest failed: %s", exc)

                        batches_completed = batch_num + (obs_idx + 1) / len(batch)
                        self._progress = compute_simulation_progress(
                            phase.start_minute,
                            phase.end_minute,
                            batches_completed,
                            batch_count,
                            total_minutes,
                        )

                    await asyncio.sleep(phase_duration_real / batch_count)

                if phase.mos_range[0] < 3.5:
                    incident_created = await self._trigger_detection(event_id, session_ids, phase)
                    if incident_created:
                        await self._trigger_supervisor(event_id, cycles=3)

                self._progress = phase.end_minute / total_minutes

            await self._trigger_supervisor(event_id, cycles=5)

            async with self._container.database.transaction() as uow:
                await TelemetryRepository(uow.session).end_event(event_id)

            self._status = SimulationStatus.COMPLETED
            self._progress = 1.0
            self._current_phase = "Simulation complete"
            logger.info("Simulation %s completed successfully", scenario.id)

        except asyncio.CancelledError:
            self._status = SimulationStatus.IDLE
            raise
        except Exception as exc:
            self._status = SimulationStatus.FAILED
            self._current_phase = f"Error: {exc}"
            logger.exception("Simulation failed: %s", exc)

    async def _trigger_detection(
        self,
        event_id: str,
        session_ids: list[str],
        phase: DegradationPhase | None = None,
    ) -> bool:
        """Try feature materialization on up to 3 sessions; fall back to synthetic vector.

        Returns True if an incident was created or already exists.
        """
        sample = session_ids[:3] if len(session_ids) >= 3 else session_ids
        for sid in sample:
            try:
                snapshot = await self._container.features.materialize(UUID(sid))
                features = FeatureVector.model_validate(snapshot.values)
                incident = await self._container.incidents.detect(
                    UUID(event_id),
                    {"region": "global"},
                    features,
                )
                if incident is not None:
                    row, created, new_alerts = incident
                    logger.info(
                        "Detection: incident %s %s for session %s",
                        row.id,
                        "created" if created else "updated",
                        sid,
                    )
                    await self._audit_incident(row, created, new_alerts)
                    return True
            except Exception as exc:  # noqa: BLE001
                logger.debug("Feature materialization failed for session %s: %s", sid, exc)

        if phase is not None:
            try:
                now = datetime.now(UTC)
                mos_mid = (phase.mos_range[0] + phase.mos_range[1]) / 2
                stall_mid = (phase.stall_ratio[0] + phase.stall_ratio[1]) / 2
                pkt_mid = (phase.packet_loss_pct[0] + phase.packet_loss_pct[1]) / 2

                synth = FeatureVector(
                    session_id=UUID(session_ids[0]),
                    window_start=now,
                    window_end=now,
                    schema_version="telemetry-v1",
                    observation_count=10,
                    throughput_mean_kbps=max(500, 6000 - (5.0 - mos_mid) * 1200),
                    throughput_std_kbps=200.0,
                    buffer_mean_ms=max(200, 8000 * (1 - phase.buffer_ratio[1])),
                    buffer_min_ms=200,
                    rebuffer_total_ms=int(stall_mid * 10000),
                    stall_ratio=min(1.0, stall_mid),
                    downswitch_count=2 if mos_mid < 3.5 else 0,
                    latest_bitrate_kbps=max(500, int(6000 - (5.0 - mos_mid) * 1200)),
                    latest_packet_loss_pct=round(pkt_mid, 3),
                )
                incident = await self._container.incidents.detect(
                    UUID(event_id),
                    {"region": "global"},
                    synth,
                )
                if incident is not None:
                    row, created, new_alerts = incident
                    logger.info(
                        "Detection (synthetic fallback): incident %s %s for phase %s",
                        row.id,
                        "created" if created else "updated",
                        getattr(phase, "description", "unknown"),
                    )
                    await self._audit_incident(row, created, new_alerts)
                    return True
            except Exception as exc:  # noqa: BLE001
                logger.warning("Synthetic detection fallback failed: %s", exc)

        logger.debug("No incident created for event %s (thresholds not breached)", event_id)
        return False

    async def _audit_incident(
        self,
        incident: IncidentRow,
        created: bool,
        new_alert_count: int,
    ) -> None:
        try:
            async with self._container.database.transaction() as uow:
                audit = AuditRepository(uow.session)
                if created:
                    payload: dict[str, object] = {
                        "description": "Incident detected from degraded telemetry",
                        "severity": incident.severity,
                        "slice_key": incident.slice_key,
                    }
                else:
                    payload = {
                        "description": "Additional alerts merged into existing incident",
                        "severity": incident.severity,
                        "slice_key": incident.slice_key,
                        "new_alert_count": new_alert_count,
                    }
                await audit.append(
                    incident.id,
                    "system",
                    "incident",
                    incident.id,
                    payload,
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to audit incident detection: %s", exc)

    async def _record_eval_trace(self, incident_id: str, state: CognitiveState) -> None:
        if not state.step_history:
            return
        tracer = self._container.tracer
        tracer.start_trace(
            {"incident_id": incident_id, "simulation": True},
        )

        evidence_ids: list[str] = []
        contributing_factors: list[str] = []
        diagnosis = state.diagnosis_result or {}
        if isinstance(diagnosis.get("evidence_ids"), list):
            evidence_ids = [str(item) for item in diagnosis["evidence_ids"]]
        if isinstance(diagnosis.get("contributing_factors"), list):
            contributing_factors = [str(item) for item in diagnosis["contributing_factors"]]

        for index, step in enumerate(state.step_history):
            jitter = 0.88 + ((index * 17 + len(step.action)) % 28) / 100.0
            duration_ms = max(float(step.duration_ms) * jitter, 80.0)
            span_name = step.action
            if step.agent_name in {"diagnostician", "mitigator", "verifier"}:
                span_name = f"tool.{step.action}"

            tracer.start_span(span_name, step.agent_name, {"success": step.success})
            tracer.end_span(
                "ok" if step.success else "error",
                {
                    "duration_ms": duration_ms,
                    "stop_reason": step.stop_reason,
                },
                duration_ms=duration_ms,
            )

            obs = step.observation or {}
            if isinstance(obs.get("evidence_ids"), list):
                for item in obs["evidence_ids"]:
                    sid = str(item)
                    if sid not in evidence_ids:
                        evidence_ids.append(sid)

        tracer.start_span("agent.final_output", "supervisor", {})
        tracer.end_span(
            "ok",
            {
                "evidence_ids": evidence_ids,
                "contributing_factors": contributing_factors,
            },
            duration_ms=12.0,
        )

        trace = tracer.end_trace()
        if trace is not None:
            try:
                await self._container.eval_runner.evaluate_trace(trace)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Eval trace failed: %s", exc)

    async def _persist_supervisor_activity(
        self,
        incident_id: str,
        state: CognitiveState,
        *,
        skip_proposal: bool = False,
    ) -> bool:
        """Write OODA steps, hypothesis, and optional proposal. Returns True if proposal created."""
        proposal_created = False
        event_id_for_analyst: str | None = None
        evidence_for_analyst: list[str] = []
        try:
            async with self._container.database.transaction() as uow:
                audit = AuditRepository(uow.session)
                runs_repo = AgentRunRepository(uow.session)
                incidents_repo = IncidentRepository(uow.session)
                row = await incidents_repo.get_incident(UUID(incident_id))
                if row is not None:
                    event_id_for_analyst = str(row.event_id)
                    evidence_for_analyst = list(row.evidence_ids)

                for step in state.step_history:
                    run = await runs_repo.create(
                        UUID(incident_id),
                        _AGENT_RUN_STATE_MAP.get(step.agent_name, "gathering_evidence"),
                        {
                            "agent": step.agent_name,
                            "action": step.action,
                            "phase": state.phase.value,
                        },
                    )
                    await audit.append(
                        incident_id,
                        "agent",
                        "supervisor_step",
                        run.id,
                        {
                            "agent": step.agent_name,
                            "action": step.action,
                            "success": step.success,
                            "duration_ms": step.duration_ms,
                            "stop_reason": step.stop_reason,
                            "llm_enriched": step.llm_enriched,
                            "step_reflection": step.step_reflection,
                            "execution_mode": self._container.simulation_execution_mode(),
                        },
                    )

                diagnosis_obs = _best_diagnostician_observation(state)
                if row is not None and diagnosis_obs:
                    new_hypothesis = str(diagnosis_obs.get("hypothesis", ""))
                    existing = row.hypothesis if isinstance(row.hypothesis, dict) else {}
                    existing_text = str(existing.get("hypothesis", "")) if existing else ""
                    if (
                        new_hypothesis == "Unknown root cause"
                        and existing_text
                        and existing_text != "Unknown root cause"
                    ):
                        pass
                    else:
                        logger.info(
                            "Persisting hypothesis for %s: %s",
                            incident_id,
                            new_hypothesis,
                        )
                        row.hypothesis = {
                            "hypothesis": new_hypothesis,
                            "confidence": diagnosis_obs.get("confidence", 0.5),
                            "source": "diagnostician",
                            "llm_enriched": bool(diagnosis_obs.get("llm_enriched", False)),
                            "recommended_action": diagnosis_obs.get("recommended_action"),
                        }
                        await uow.flush()

            mitigation_obs = next(
                (
                    step.observation
                    for step in reversed(state.step_history)
                    if step.agent_name == "mitigator" and step.observation
                ),
                None,
            )
            if not skip_proposal and mitigation_obs:
                logger.info("Creating simulation proposal for %s", incident_id)
                proposal_created = await self._create_simulation_proposal(
                    incident_id,
                    state,
                    mitigation_obs,
                )

            await self._record_eval_trace(incident_id, state)

            has_diagnosis = any(step.agent_name == "diagnostician" for step in state.step_history)
            if has_diagnosis and event_id_for_analyst and evidence_for_analyst:
                await self._run_llm_analyst_if_enabled(
                    incident_id,
                    event_id_for_analyst,
                    evidence_for_analyst,
                )

        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to persist supervisor activity: %s", exc, exc_info=True)
            try:
                async with self._container.database.transaction() as uow:
                    await AuditRepository(uow.session).append(
                        incident_id,
                        "system",
                        "proposal_failed",
                        incident_id,
                        {"error": str(exc), "error_type": type(exc).__name__},
                    )
            except Exception:  # noqa: BLE001
                pass

        return proposal_created

    async def _create_simulation_proposal(
        self,
        incident_id: str,
        state: CognitiveState,
        prop: dict[str, object],
    ) -> bool:
        async with self._container.database.transaction() as uow:
            incidents_repo = IncidentRepository(uow.session)
            audit = AuditRepository(uow.session)
            row = await incidents_repo.get_incident(UUID(incident_id))
            if row is None or not row.evidence_ids:
                return False

            existing = await ActionRepository(uow.session).list_for_incident(
                UUID(incident_id),
                limit=1,
            )
            if existing:
                return True

            if row.state == IncidentState.DETECTED.value:
                row.state = IncidentState.INVESTIGATING.value
                await uow.flush()

            prop = prop or {}
            action_type = _MITIGATOR_ACTION_MAP.get(
                str(prop.get("action_type", "investigate_only")),
                "investigate_only",
            )
            session_count = int(state.active_sessions_count or self._sessions_provisioned or 100)
            raw_scope = prop.get("target_scope", {})
            scope_in: dict[str, object] = (
                {str(k): v for k, v in raw_scope.items()} if isinstance(raw_scope, dict) else {}
            )
            target_scope = _sanitize_target_scope(
                scope_in,
                event_id=state.event_id,
                session_count=session_count,
            )

            raw_confidence = prop.get("confidence", 0.75)
            raw_risk = prop.get("risk_score", 0.15)
            proposal = ProposalCreate(
                action_type=action_type,
                target_scope=target_scope,
                rationale=str(prop.get("rationale", "Simulation mitigation proposal")),
                expected_effect=str(
                    prop.get("expected_effect", "Restore QoE for affected viewers")
                ),
                confidence=(
                    float(raw_confidence) if isinstance(raw_confidence, (int, float, str)) else 0.75
                ),
                risk_score=(float(raw_risk) if isinstance(raw_risk, (int, float, str)) else 0.15),
                evidence_ids=[UUID(eid) for eid in row.evidence_ids[:3]],
            )
            evidence_is_valid = set(map(str, proposal.evidence_ids)).issubset(set(row.evidence_ids))
            decision = self._container.policies.evaluate(proposal, evidence_is_valid)
            proposal_row = await ActionRepository(uow.session).create(
                UUID(incident_id),
                proposal,
                decision.state.value,
                decision.reasons,
            )
            await audit.append(
                incident_id,
                "policy",
                "proposal",
                proposal_row.id,
                {
                    "state": decision.state.value,
                    "reasons": decision.reasons,
                    "action_type": action_type,
                },
            )
            return True

    async def _run_llm_analyst_if_enabled(
        self,
        incident_id: str,
        event_id: str,
        evidence_ids: list[str],
    ) -> None:
        if not self._container.llm_configured_for_simulation():
            return
        if not evidence_ids:
            return
        try:
            evidence = [
                ToolResult(
                    call=ToolCall(
                        name=ToolName.TELEMETRY,
                        arguments={"event_id": event_id, "window_minutes": 5},
                    ),
                    output={
                        "avg_mos": 3.0,
                        "buffer_ratio": 5.0,
                        "event_id": event_id,
                    },
                    evidence_ids=[UUID(eid) for eid in evidence_ids[:3]],
                )
            ]
            run = await self._container.agent.start(
                UUID(incident_id),
                incident_id,
                evidence,
            )
            await self._container.agent.analyze(
                UUID(run.id),
                {
                    "incident_id": incident_id,
                    "event_id": event_id,
                    "execution_mode": "llm_enriched",
                },
                incident_id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("LLM analyst workflow failed for %s: %s", incident_id, exc)

    async def _run_verifier_phase(
        self,
        event_id: str,
        incident_id: str,
        session_count: int,
    ) -> None:
        """Auto-execute proposal in demo and run verifier agent."""
        self._container.reset_agent_tool_history()
        supervisor = self._container.get_simulation_supervisor()
        state = CognitiveState(
            event_id=event_id,
            incident_id=incident_id,
            max_retries=2,
        )
        state.detection_complete = True
        state.diagnosis_complete = True
        state.mitigation_proposed = True
        state.action_executed = True
        state.action_verified = False
        state.detection_result = {"anomalies_detected": True, "anomalies": ["degraded"]}
        state.latest_kpis = {"avg_mos": 3.0, "buffer_ratio": 5.0}
        signals = {
            "kpis": {"avg_mos": 3.8, "buffer_ratio": 2.0},
            "session_count": session_count,
            "qoe_prediction": 3.8,
        }

        for _ in range(3):
            state = await supervisor.cycle(state, signals)
            if state.action_verified or state.current_decision == "idle":
                break

        await self._persist_supervisor_activity(incident_id, state, skip_proposal=True)

    async def _trigger_supervisor(self, event_id: str, cycles: int = 8) -> None:
        """Trigger the OODA supervisor cycle for active incidents."""
        try:
            self._container.reset_agent_tool_history()
            async with self._container.database.transaction() as uow:
                incidents = await IncidentRepository(uow.session).active_for_event(event_id)

            supervisor = self._container.get_simulation_supervisor()
            session_count = self._sessions_provisioned or 100

            for incident in incidents:
                state = CognitiveState(
                    event_id=event_id,
                    incident_id=incident.id,
                    max_retries=2,
                )
                state.has_unprocessed_alerts = True
                signals = {
                    "kpis": {"avg_mos": 3.0, "buffer_ratio": 5.0},
                    "new_alerts": [
                        {"severity": incident.severity, "id": alert_id}
                        for alert_id in incident.evidence_ids[:3]
                    ],
                    "session_count": session_count,
                    "qoe_prediction": 3.0,
                }

                for _ in range(cycles):
                    state = await supervisor.cycle(state, signals)
                    if state.current_decision == "idle":
                        break
                    if state.human_escalation_required:
                        break
                    if state.phase == IncidentPhase.RESOLVED:
                        break

                proposal_created = await self._persist_supervisor_activity(incident.id, state)
                if proposal_created:
                    await self._run_verifier_phase(event_id, incident.id, session_count)
        except Exception as exc:
            logger.warning("Supervisor trigger failed: %s", exc)
