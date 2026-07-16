import hashlib
import json
from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from stromwart.persistence import AuditRow


class AuditService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record(
        self,
        actor_type: str,
        artifact_type: str,
        artifact_id: str,
        payload: dict[str, Any],
        correlation_id: str | None = None,
    ) -> str:
        encoded = json.dumps(
            payload,
            default=str,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()

        event = AuditRow(
            correlation_id=correlation_id or str(uuid4()),
            actor_type=actor_type,
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            payload_hash=hashlib.sha256(encoded).hexdigest(),
            payload=payload,
        )
        self.session.add(event)
        await self.session.commit()
        return event.id
