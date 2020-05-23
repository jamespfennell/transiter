from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base


class ServiceMap(Base):
    __tablename__ = "service_map"

    pk = Column(Integer, primary_key=True)
    route_pk = Column(Integer, ForeignKey("route.pk"), index=True, nullable=False)
    group_pk = Column(Integer, ForeignKey("service_map_group.pk"), nullable=False)

    group = relationship("ServiceMapGroup", back_populates="maps")
    route = relationship(
        "Route", foreign_keys=[route_pk], back_populates="service_maps"
    )
    vertices = relationship(
        "ServiceMapVertex",
        back_populates="map",
        order_by="ServiceMapVertex.position",
        cascade="all, delete-orphan",
    )

    __table_args__ = (UniqueConstraint(route_pk, group_pk),)
