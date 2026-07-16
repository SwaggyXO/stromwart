from collections.abc import AsyncIterator
from typing import Annotated, cast

from fastapi import Depends, Request

from stromwart.application.container import Container
from stromwart.database import Database, UnitOfWork


def container(request: Request) -> Container:
    return cast(Container, request.app.state.container)


def database(
    app_container: Annotated[Container, Depends(container)],
) -> Database:
    return app_container.database


async def unit_of_work(
    database_instance: Annotated[Database, Depends(database)],
) -> AsyncIterator[UnitOfWork]:
    async with database_instance.transaction() as uow:
        yield uow


ContainerDep = Annotated[Container, Depends(container)]
UnitOfWorkDep = Annotated[UnitOfWork, Depends(unit_of_work)]
