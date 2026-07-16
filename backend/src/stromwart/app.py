from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from stromwart.api.router import router
from stromwart.application.container import Container
from stromwart.application.errors import (
    request_validation_handler,
    stromwart_error_handler,
)
from stromwart.application.middleware import CorrelationIdMiddleware
from stromwart.core import get_settings
from stromwart.database import Database
from stromwart.errors import StromwartError


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    database = Database(settings.database_url)
    http_client = httpx.AsyncClient(timeout=settings.llm_timeout_seconds)
    app.state.container = Container(settings, database, http_client)

    try:
        yield
    finally:
        await http_client.aclose()
        await database.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Stromwart API",
        version="0.1.0",
        description=(
            "Predictive Quality of Experience (QoE) engine for live streaming events. "
            "Ingests telemetry, estimates QoE with uncertainty quantification, "
            "forecasts degradation risk, detects incidents, and recommends "
            "guardrail-checked mitigations via an agentic SRE workflow."
        ),
        openapi_tags=[
            {
                "name": "telemetry",
                "description": "Ingest events, sessions, and per-chunk telemetry observations.",
            },
            {
                "name": "qoe",
                "description": "QoE scoring and risk forecasting with ML models.",
            },
            {
                "name": "modeling",
                "description": "Event-scoped forecast time series for live dashboards.",
            },
            {
                "name": "control",
                "description": "Incident detection, investigation, proposals, and simulation.",
            },
            {
                "name": "agents",
                "description": (
                    "LLM analyst workflow — evidence gathering, analysis, human feedback."
                ),
            },
            {
                "name": "live",
                "description": "Real-time SSE streams and session queries for live dashboards.",
            },
            {
                "name": "audit",
                "description": "Append-only audit trail queries.",
            },
            {
                "name": "health",
                "description": "Liveness and readiness probes.",
            },
        ],
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-Correlation-ID"],
    )
    app.add_middleware(CorrelationIdMiddleware)

    app.add_exception_handler(StromwartError, stromwart_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, request_validation_handler)  # type: ignore[arg-type]
    app.include_router(router)

    @app.get(
        "/health",
        tags=["health"],
        summary="Liveness probe",
        description="Returns ok when the API process is running.",
    )
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get(
        "/ready",
        tags=["health"],
        summary="Readiness probe",
        description="Returns ready when the database connection is healthy.",
    )
    async def ready(request: Request) -> dict[str, str]:
        database = request.app.state.container.database
        async with database.transaction() as uow:
            await uow.session.execute(text("SELECT 1"))
        return {"status": "ready"}

    return app


app = create_app()
