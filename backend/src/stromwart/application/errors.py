from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from stromwart.errors import (
    ConflictError,
    InvalidStateError,
    ModelUnavailableError,
    NotFoundError,
    ProviderUnavailableError,
    StromwartError,
    ValidationError,
)


def error_response(
    request: Request,
    status_code: int,
    code: str,
    detail: str,
) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "unavailable")
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "detail": detail,
                "correlation_id": correlation_id,
            }
        },
    )


async def stromwart_error_handler(
    request: Request,
    error: StromwartError,
) -> JSONResponse:
    mappings = {
        NotFoundError: 404,
        ConflictError: 409,
        ValidationError: 422,
        InvalidStateError: 409,
        ModelUnavailableError: 503,
        ProviderUnavailableError: 503,
    }
    return error_response(
        request,
        mappings.get(type(error), 400),
        error.code,
        error.detail,
    )


async def request_validation_handler(
    request: Request,
    error: RequestValidationError,
) -> JSONResponse:
    return error_response(
        request,
        422,
        "request_validation_error",
        str(error.errors()),
    )
