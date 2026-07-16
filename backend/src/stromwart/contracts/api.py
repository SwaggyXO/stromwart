from typing import TypeVar

from stromwart.contracts.common import ApiModel

Item = TypeVar("Item")


class ErrorBody(ApiModel):
    code: str
    detail: str
    correlation_id: str


class ErrorResponse(ApiModel):
    error: ErrorBody


class Page[Item](ApiModel):
    items: list[Item]
    next_cursor: str | None = None
