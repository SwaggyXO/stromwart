from __future__ import annotations

from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx

from stromwart.agents.base import Budget
from stromwart.agents.critic import EvidenceCritic
from stromwart.agents.detector import DetectorAgent
from stromwart.agents.diagnostician import DiagnosticianAgent
from stromwart.agents.guardrails import AgentGuardrails, GuardrailPolicy
from stromwart.agents.mitigator import MitigatorAgent
from stromwart.agents.tools import ToolGateway, ToolSpec
from stromwart.agents.verifier import VerifierAgent
from stromwart.agents.workflow import AgentWorkflow
from stromwart.core import Settings
from stromwart.database import Database
from stromwart.evals import AgentTracer, LLMJudge
from stromwart.evals.runner import EvalRunner
from stromwart.features.service import FeatureService
from stromwart.incidents.rules import AlertRules
from stromwart.incidents.service import IncidentService
from stromwart.ingestion.service import IngestionService
from stromwart.mcp.server import StromwartMCPServer
from stromwart.models.registry import ModelRegistry
from stromwart.orchestrator.supervisor import Supervisor
from stromwart.policies.proposals import ProposalService
from stromwart.policies.service import PolicyService
from stromwart.providers import AnalystProvider, DisabledAnalystProvider
from stromwart.providers.router import create_provider
from stromwart.settings import SettingsStore
from stromwart.simulation.service import SimulationService

if TYPE_CHECKING:
    from stromwart.simulation.engine import SimulationEngine


class Container:
    def __init__(
        self,
        settings: Settings,
        database: Database,
        http_client: httpx.AsyncClient,
    ) -> None:
        self.settings = settings
        self.database = database
        self.http_client = http_client
        self.models = ModelRegistry()

        root = Path(__file__).parents[3]
        self.policies = PolicyService(
            root / "configs/policies/action_allowlist.yaml",
            root / "configs/policies/live_event_guardrails.yaml",
        )

        self.ingestion = IngestionService(database)
        self.features = FeatureService(database)
        self.incidents = IncidentService(database, AlertRules())
        self.proposals = ProposalService(database, self.policies)
        self.simulation = SimulationService()
        self._load_models()

        self.settings_store = SettingsStore(root / "settings.yaml")
        system_settings = self.settings_store.get()

        tool_specs = [
            ToolSpec(
                name="telemetry",
                description="Query recent telemetry",
                handler=self._telemetry_handler,
            ),
            ToolSpec(
                name="features",
                description="Get feature vectors",
                handler=self._features_handler,
            ),
            ToolSpec(
                name="predictions",
                description="Get QoE predictions",
                handler=self._predictions_handler,
            ),
            ToolSpec(
                name="forecasts",
                description="Get forecasts",
                handler=self._forecasts_handler,
            ),
            ToolSpec(
                name="topology",
                description="Get network topology",
                handler=self._topology_handler,
            ),
            ToolSpec(
                name="runbook",
                description="Query runbook",
                handler=self._runbook_handler,
            ),
        ]
        gateway = ToolGateway(tool_specs)
        guardrails = AgentGuardrails(
            policies={
                "mitigator": GuardrailPolicy(
                    allowed_action_types=[
                        "scale_cdn_edge",
                        "reroute_traffic",
                        "increase_bandwidth_allocation",
                        "scale_origin",
                        "investigate_only",
                    ],
                ),
            }
        )
        budget = Budget(
            max_steps=system_settings.agent_step_budget,
            max_seconds=system_settings.agent_time_budget_seconds,
        )

        llm = create_provider(
            system_settings.llm_provider,
            system_settings.llm_model,
            system_settings.llm_api_key,
            system_settings.llm_endpoint,
            http_client=self.http_client,
        )

        agents = {
            "detector": DetectorAgent(tools=gateway, guardrails=guardrails, budget=budget),
            "diagnostician": DiagnosticianAgent(
                tools=gateway,
                guardrails=guardrails,
                budget=budget,
                llm_provider=llm if system_settings.llm_provider != "disabled" else None,
            ),
            "mitigator": MitigatorAgent(tools=gateway, guardrails=guardrails, budget=budget),
            "verifier": VerifierAgent(tools=gateway, guardrails=guardrails, budget=budget),
        }

        self.supervisor = Supervisor(
            agents,
            enabled_agents={
                "detector": system_settings.detector_enabled,
                "diagnostician": system_settings.diagnostician_enabled,
                "mitigator": system_settings.mitigator_enabled,
                "verifier": system_settings.verifier_enabled,
            },
        )
        self._production_agents = agents

        self.tracer = AgentTracer(sample_rate=system_settings.eval_trace_sample_rate)
        judge = LLMJudge(llm if system_settings.eval_llm_judge_enabled else None)
        self.eval_runner = EvalRunner(self.tracer, judge)

        self.mcp_server = StromwartMCPServer(self)

        self.agent = AgentWorkflow(
            database=database,
            provider=self._provider(),
            critic=EvidenceCritic(),
        )

    @cached_property
    def simulation_engine(self) -> "SimulationEngine":
        from stromwart.simulation.engine import SimulationEngine

        return SimulationEngine(self)

    @cached_property
    def _deterministic_simulation_supervisor(self) -> Supervisor:
        """Fast deterministic supervisor when LLM is disabled."""
        demo_budget = Budget(max_steps=10, max_seconds=5)
        gateway = self._production_agents["detector"].tools
        guardrails = self._production_agents["detector"].guardrails
        demo_agents = {
            "detector": DetectorAgent(tools=gateway, guardrails=guardrails, budget=demo_budget),
            "diagnostician": DiagnosticianAgent(
                tools=gateway,
                guardrails=guardrails,
                budget=demo_budget,
                llm_provider=None,
            ),
            "mitigator": MitigatorAgent(tools=gateway, guardrails=guardrails, budget=demo_budget),
            "verifier": VerifierAgent(tools=gateway, guardrails=guardrails, budget=demo_budget),
        }
        return Supervisor(demo_agents, enabled_agents=dict(self.supervisor._enabled))

    def get_simulation_supervisor(self) -> Supervisor:
        """Use production supervisor (with LLM) when configured; else deterministic demo."""
        if self.llm_configured_for_simulation():
            return self.supervisor
        return self._deterministic_simulation_supervisor

    def reset_agent_tool_history(self) -> None:
        """Clear tool loop-detection history between OODA cycles."""
        self._production_agents["detector"].tools.reset_history()

    def reset_eval_state(self) -> None:
        """Clear in-memory eval traces/scores between demo runs."""
        self.eval_runner.clear()

    def llm_configured_for_simulation(self) -> bool:
        settings = self.settings_store.get()
        if settings.llm_provider == "disabled" or not settings.llm_model:
            return False
        if settings.llm_provider == "ollama":
            return True
        return bool(settings.llm_api_key)

    def simulation_execution_mode(self) -> str:
        return "llm_enriched" if self.llm_configured_for_simulation() else "deterministic"

    @cached_property
    def simulation_supervisor(self) -> Supervisor:
        """Backward-compatible alias for deterministic supervisor."""
        return self._deterministic_simulation_supervisor

    async def _telemetry_handler(self, args: dict[str, Any]) -> dict[str, Any]:
        return {
            "avg_mos": 3.2,
            "buffer_ratio": 4.5,
            "event_id": args.get("event_id"),
            "window_minutes": args.get("window_minutes", 5),
        }

    async def _features_handler(self, args: dict[str, Any]) -> dict[str, Any]:
        return {
            "avg_bitrate_kbps": 1800,
            "stall_ratio": 4.0,
            "packet_loss_pct": 1.5,
            "slices": args.get("slices", ["global"]),
            "event_id": args.get("event_id"),
        }

    async def _predictions_handler(self, args: dict[str, Any]) -> dict[str, Any]:
        result = self.models.predict("qoe_gbm", args)
        return {"predicted_mos": result.get("predicted_mos", 4.2), "event_id": args.get("event_id")}

    async def _forecasts_handler(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.models.predict("quantile_forecaster", args)

    async def _topology_handler(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"cdn_edge_cpu_pct": 90, "event_id": args.get("event_id")}

    async def _runbook_handler(self, args: dict[str, Any]) -> dict[str, Any]:
        action_type = args.get("action_type", "investigate_only")
        return {
            "action_type": action_type,
            "steps": ["Verify scope", "Execute action", "Monitor effect"],
        }

    def _provider(self) -> AnalystProvider:
        settings = self.settings_store.get()
        if settings.llm_provider == "disabled" or not settings.llm_model:
            return DisabledAnalystProvider()

        if settings.llm_provider != "ollama" and not settings.llm_api_key:
            return DisabledAnalystProvider()

        return create_provider(
            settings.llm_provider,
            settings.llm_model,
            settings.llm_api_key,
            settings.llm_endpoint,
            http_client=self.http_client,
        )

    def _load_models(self) -> None:
        """Load serialized model artifacts if available."""
        from stromwart.contracts.modeling import ModelIdentity

        artifacts_dir = Path(__file__).parents[3] / "artifacts"
        if not artifacts_dir.exists():
            return

        qoe_path = artifacts_dir / "qoe_gbm_v1.joblib"
        if qoe_path.exists():
            from stromwart.models.qoe_gbm import QoEGBMModel

            model = QoEGBMModel.load(qoe_path)
            identity = ModelIdentity(
                name="qoe_gbm",
                version="v1",
                feature_schema_version="telemetry-v1",
            )
            self.models.register_qoe(identity, model)

        forecast_path = artifacts_dir / "quantile_forecaster_v1.joblib"
        if forecast_path.exists():
            from stromwart.models.quantile_forecaster import QuantileForecasterModel

            forecast_model = QuantileForecasterModel.load(forecast_path)
            forecast_identity = ModelIdentity(
                name="quantile_forecaster",
                version="v1",
                feature_schema_version="telemetry-v1",
            )
            self.models.register_forecast(forecast_identity, forecast_model)
