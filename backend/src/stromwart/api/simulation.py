"""Simulation API routes."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from stromwart.application.dependencies import ContainerDep
from stromwart.simulation.scenarios import SCENARIOS

router = APIRouter(prefix="/simulation", tags=["simulation"])


class StartSimulationRequest(BaseModel):
    scenario_id: str
    speed_multiplier: float = 10.0


class SimulationStatusResponse(BaseModel):
    status: str
    scenario_id: str | None = None
    progress: float = 0.0
    current_phase: str = ""
    event_id: str | None = None
    sessions_provisioned: int | None = None
    sessions_peak_narrative: int | None = None
    execution_mode: str | None = None


def _status_payload(engine: object, container: object | None = None) -> dict[str, Any]:
    from stromwart.application.container import Container
    from stromwart.simulation.engine import SimulationEngine

    assert isinstance(engine, SimulationEngine)
    scenario = engine.current_scenario
    payload: dict[str, Any] = {
        "status": engine.status.value,
        "scenario_id": engine.scenario_id,
        "progress": engine.progress,
        "current_phase": engine.current_phase,
        "event_id": engine.event_id,
        "sessions_provisioned": engine.sessions_provisioned,
        "sessions_peak_narrative": scenario.sessions_peak if scenario else None,
    }
    if isinstance(container, Container):
        payload["execution_mode"] = container.simulation_execution_mode()
    return payload


class ScenarioResponse(BaseModel):
    id: str
    name: str
    description: str
    duration_minutes: int
    category: str
    sessions_peak: int
    phase_count: int


@router.get("/scenarios", response_model=list[ScenarioResponse])
async def list_scenarios() -> list[dict[str, Any]]:
    """List available simulation scenarios."""
    return [
        {
            "id": scenario.id,
            "name": scenario.name,
            "description": scenario.description,
            "duration_minutes": scenario.duration_minutes,
            "category": scenario.category,
            "sessions_peak": scenario.sessions_peak,
            "phase_count": len(scenario.phases),
        }
        for scenario in SCENARIOS.values()
    ]


@router.post("/start", response_model=SimulationStatusResponse, status_code=201)
async def start_simulation(
    body: StartSimulationRequest,
    container: ContainerDep,
) -> dict[str, Any]:
    """Start a simulation scenario."""
    engine = container.simulation_engine
    try:
        await engine.start(body.scenario_id, body.speed_multiplier)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return _status_payload(engine, container)


@router.post("/stop")
async def stop_simulation(container: ContainerDep) -> dict[str, str]:
    """Stop the running simulation."""
    engine = container.simulation_engine
    await engine.stop()
    return {"status": "stopped"}


@router.get("/status", response_model=SimulationStatusResponse)
async def get_simulation_status(container: ContainerDep) -> dict[str, Any]:
    """Get current simulation status."""
    return _status_payload(container.simulation_engine, container)
