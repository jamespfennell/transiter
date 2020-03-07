from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class ScheduledTrip(Base):
    __tablename__ = "scheduled_trip"

    pk = Column(Integer, primary_key=True)
    id = Column(String, nullable=False)
    route_pk = Column(Integer, ForeignKey("route.pk"), nullable=False)
    service_pk = Column(Integer, ForeignKey("scheduled_service.pk"), nullable=False)

    direction_id = Column(Boolean)

    route_id = None

    route = relationship("Route", back_populates="scheduled_trips", cascade="none")
    service = relationship("ScheduledService", back_populates="trips", cascade="none")
    stop_times = relationship(
        "ScheduledTripStopTime", back_populates="trip", cascade="all, delete-orphan"
    )
    stop_times_light = None
