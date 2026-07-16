from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

from stromwart.contracts.common import ApiModel


class ModelIdentity(ApiModel):
    name: str = Field(min_length=1, max_length=100)
    version: str = Field(min_length=1, max_length=100)
    feature_schema_version: str = Field(min_length=1, max_length=100)


class ScoreRequest(ApiModel):
    """Request QoE scoring for a session."""

    session_id: UUID = Field(description="Session to score (must have observations)")
    model: ModelIdentity = Field(description="Which model to use for scoring")

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "model": {
                        "name": "qoe_gbm",
                        "version": "v1",
                        "feature_schema_version": "telemetry-v1",
                    },
                }
            ]
        },
    )


class ScoreResult(ApiModel):
    """QoE prediction with conformal prediction interval."""

    prediction_type: str = Field(
        min_length=1,
        max_length=50,
        description="Type of prediction: mos_estimate, bad_qoe_probability",
    )
    value: float = Field(description="Point estimate (MOS 1-5 or probability 0-1)")
    lower_bound: float | None = Field(
        default=None,
        description="Lower bound of conformal prediction interval",
    )
    upper_bound: float | None = Field(
        default=None,
        description="Upper bound of conformal prediction interval",
    )
    confidence: float | None = Field(
        default=None, ge=0, le=1,
        description="Model confidence (derived from interval width)",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "prediction_type": "mos_estimate",
                    "value": 3.82,
                    "lower_bound": 3.14,
                    "upper_bound": 4.51,
                    "confidence": 0.658,
                }
            ]
        },
    )

    @model_validator(mode="after")
    def validate_interval(self) -> "ScoreResult":
        if (
            self.lower_bound is not None
            and self.upper_bound is not None
            and self.lower_bound > self.upper_bound
        ):
            raise ValueError("lower_bound cannot exceed upper_bound")
        return self


class ForecastRequest(ApiModel):
    session_id: UUID
    metric_name: str = Field(min_length=1, max_length=100)
    horizon_seconds: int = Field(gt=0, le=86_400)
    model: ModelIdentity


class ForecastResult(ApiModel):
    """Quantile forecast for a session metric."""

    p10: float = Field(description="10th percentile (optimistic bound)")
    p50: float = Field(description="50th percentile (median forecast)")
    p90: float = Field(description="90th percentile (pessimistic bound)")

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {"p10": 0.12, "p50": 0.34, "p90": 0.61}
            ]
        },
    )

    @model_validator(mode="after")
    def validate_quantiles(self) -> "ForecastResult":
        if not self.p10 <= self.p50 <= self.p90:
            raise ValueError("forecast quantiles must satisfy p10 <= p50 <= p90")
        return self


class ForecastSeriesPoint(ApiModel):
    """Event-scoped forecast time-series point for charting."""

    timestamp: datetime = Field(description="Forecast horizon timestamp (UTC)")
    p10: float = Field(description="10th percentile risk at this horizon")
    p50: float = Field(description="50th percentile risk at this horizon")
    p90: float = Field(description="90th percentile risk at this horizon")

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "timestamp": "2026-07-14T20:16:00Z",
                    "p10": 0.08,
                    "p50": 0.15,
                    "p90": 0.28,
                }
            ]
        },
    )

    @model_validator(mode="after")
    def validate_quantiles(self) -> "ForecastSeriesPoint":
        if not self.p10 <= self.p50 <= self.p90:
            raise ValueError("forecast quantiles must satisfy p10 <= p50 <= p90")
        return self
