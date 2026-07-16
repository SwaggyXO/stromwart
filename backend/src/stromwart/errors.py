class StromwartError(Exception):
    code = "stromwart_error"

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class NotFoundError(StromwartError):
    code = "not_found"


class ConflictError(StromwartError):
    code = "conflict"


class ValidationError(StromwartError):
    code = "validation_error"


class InvalidStateError(StromwartError):
    code = "invalid_state"


class ModelUnavailableError(StromwartError):
    code = "model_unavailable"


class ProviderUnavailableError(StromwartError):
    code = "provider_unavailable"
