from dataclasses import dataclass

from stromwart.contracts.common import SessionCreate


@dataclass(frozen=True)
class Slice:
    event_id: str
    region: str | None
    asn: str | None
    device_class: str | None
    network_type: str | None
    cdn_edge_id: str | None
    abr_profile: str | None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "event_id": self.event_id,
            "region": self.region,
            "asn": self.asn,
            "device_class": self.device_class,
            "network_type": self.network_type,
            "cdn_edge_id": self.cdn_edge_id,
            "abr_profile": self.abr_profile,
        }

    def key(self) -> str:
        return "|".join(f"{key}={value or '_'}" for key, value in self.as_dict().items())


class TopologyService:
    def session_slice(self, session: SessionCreate) -> Slice:
        return Slice(
            event_id=str(session.event_id),
            region=session.region,
            asn=session.asn,
            device_class=session.device_class,
            network_type=session.network_type,
            cdn_edge_id=session.cdn_edge_id,
            abr_profile=session.abr_profile,
        )

    def validate_scope(
        self,
        incident_slice: dict[str, str | None],
        target_scope: dict[str, str | int | float | bool | None],
    ) -> bool:
        for key, value in target_scope.items():
            if key in incident_slice and value not in (None, incident_slice[key]):
                return False
        return True
