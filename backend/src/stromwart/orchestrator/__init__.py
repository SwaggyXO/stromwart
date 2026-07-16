from stromwart.orchestrator.state import CognitiveState

__all__ = ["Supervisor", "CognitiveState"]


def __getattr__(name: str) -> object:
    if name == "Supervisor":
        from stromwart.orchestrator.supervisor import Supervisor

        return Supervisor
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
