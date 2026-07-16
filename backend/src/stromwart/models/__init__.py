from stromwart.models.registry import ModelRegistry

__all__ = ["ModelRegistry"]

# Concrete implementations (available after `uv sync` with ML deps)
try:
    from stromwart.models.qoe_gbm import QoEGBMModel
    from stromwart.models.quantile_forecaster import QuantileForecasterModel

    __all__ += ["QoEGBMModel", "QuantileForecasterModel"]
except ImportError:
    pass
