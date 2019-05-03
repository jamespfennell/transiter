from sqlalchemy import Column, TIMESTAMP, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class Route(Base):
    __tablename__ = "route"

    pk = Column(Integer, primary_key=True)
    id = Column(String, index=True)
    system_id = Column(String, ForeignKey("system.id"), index=True)

    frequency = Column(Float, nullable=True, default=None)
    running = Column(Boolean, default=False)
    color = Column(String)
    short_name = Column(String)
    long_name = Column(String)
    description = Column(String)
    timetable_url = Column(String)
    last_update_time = Column(TIMESTAMP(timezone=True))

    system = relationship("System", back_populates="routes")
    trips = relationship("Trip", back_populates="route", cascade="all, delete-orphan")
    service_patterns = relationship(
        "ServicePattern",
        back_populates="route",
        primaryjoin="ServicePattern.route_pk==Route.pk",
        cascade="all, delete-orphan",
    )
    route_statuses = relationship(
        "RouteStatus", secondary="route_status_route", back_populates="routes"
    )

    _short_repr_list = [id]
    _long_repr_list = [id]
