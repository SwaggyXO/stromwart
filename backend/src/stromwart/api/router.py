from fastapi import APIRouter

from stromwart.api.agents import router as agents_router
from stromwart.api.audit import router as audit_router
from stromwart.api.control import router as control_router
from stromwart.api.evals import router as evals_router
from stromwart.api.live import router as live_router
from stromwart.api.modeling import router as modeling_router
from stromwart.api.modeling_forecast import router as modeling_forecast_router
from stromwart.api.providers import router as providers_router
from stromwart.api.settings import router as settings_router
from stromwart.api.simulation import router as simulation_router
from stromwart.api.telemetry import router as telemetry_router
from stromwart.mcp.routes import router as mcp_router

router = APIRouter(prefix="/v1")
router.include_router(telemetry_router)
router.include_router(control_router)
router.include_router(agents_router)
router.include_router(modeling_router)
router.include_router(modeling_forecast_router)
router.include_router(live_router)
router.include_router(audit_router)
router.include_router(settings_router)
router.include_router(providers_router)
router.include_router(simulation_router)
router.include_router(evals_router)
router.include_router(mcp_router)
