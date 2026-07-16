import asyncio
import time

from fastapi import APIRouter
from pydantic import BaseModel

from stromwart.application.dependencies import ContainerDep
from stromwart.settings.connectivity import probe_provider
from stromwart.settings.schema import AVAILABLE_PROVIDERS, ProviderInfo, SystemSettings

router = APIRouter(prefix="/settings", tags=["settings"])

TEST_TIMEOUT_SECONDS = 10.0


class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    latency_ms: int = 0


@router.get(
    "",
    response_model=SystemSettings,
    summary="Get system settings",
    description="Retrieve current LLM provider configuration and application settings.",
)
async def get_settings(container: ContainerDep) -> SystemSettings:
    return container.settings_store.get()


@router.put(
    "",
    response_model=SystemSettings,
    summary="Update system settings",
    description="Apply partial settings changes (provider, model, API key, endpoint).",
)
async def update_settings(changes: dict[str, object], container: ContainerDep) -> SystemSettings:
    return container.settings_store.update(changes)


@router.get(
    "/providers",
    response_model=list[ProviderInfo],
    summary="List LLM providers",
    description="Return available LLM provider options for the settings UI.",
)
async def list_providers() -> list[ProviderInfo]:
    return AVAILABLE_PROVIDERS


@router.post("/providers/test", response_model=TestConnectionResponse)
async def test_provider(
    provider_id: str,
    model: str,
    api_key: str | None = None,
    endpoint: str | None = None,
) -> TestConnectionResponse:
    """Fast connectivity probe — no full LLM inference."""
    started = time.perf_counter()

    async def _run() -> TestConnectionResponse:
        outcome = await probe_provider(provider_id, model, api_key, endpoint)
        latency_ms = int((time.perf_counter() - started) * 1000)
        return TestConnectionResponse(
            success=outcome.success,
            message=outcome.message,
            latency_ms=latency_ms,
        )

    try:
        return await asyncio.wait_for(_run(), timeout=TEST_TIMEOUT_SECONDS)
    except TimeoutError:
        return TestConnectionResponse(
            success=False,
            message=f"Connection timed out ({int(TEST_TIMEOUT_SECONDS)}s)",
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
