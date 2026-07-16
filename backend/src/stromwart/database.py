from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class UnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def flush(self) -> None:
        await self.session.flush()

    @asynccontextmanager
    async def savepoint(self) -> AsyncIterator[None]:
        async with self.session.begin_nested():
            yield


class Database:
    def __init__(self, url: str) -> None:
        self.engine = create_async_engine(url, pool_pre_ping=True)
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[UnitOfWork]:
        async with self.session_factory() as session:
            async with session.begin():
                yield UnitOfWork(session)

    async def dispose(self) -> None:
        await self.engine.dispose()
