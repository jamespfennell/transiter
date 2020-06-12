from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Time, Enum
from sqlalchemy.orm import relationship

from transiter import parse
from .base import Base


class ScheduledTrip(Base):
    __tablename__ = "scheduled_trip"

    pk = Column(Integer, primary_key=True)
    id = Column(String, nullable=False)
    route_pk = Column(Integer, ForeignKey("route.pk"), nullable=False)
    service_pk = Column(Integer, ForeignKey("scheduled_service.pk"), nullable=False)

    WheelchairAccessible = parse.ScheduledTrip.WheelchairAccessible
    BikesAllowed = parse.ScheduledTrip.BikesAllowed

    headsign = Column(String)
    short_name = Column(String)
    direction_id = Column(Boolean)
    block_id = Column(String)
    wheelchair_accessible = Column(
        Enum(WheelchairAccessible, native_enum=False),
        nullable=False,
        default=WheelchairAccessible.UNKNOWN,
    )
    bikes_allowed = Column(
        Enum(BikesAllowed, native_enum=False),
        nullable=False,
        default=BikesAllowed.UNKNOWN,
    )

    route = relationship("Route", back_populates="scheduled_trips", cascade="none")
    service = relationship("ScheduledService", back_populates="trips", cascade="none")
    stop_times = relationship(
        "ScheduledTripStopTime", back_populates="trip", cascade="all, delete-orphan"
    )
    frequencies = relationship("ScheduledTripFrequency", cascade="all, delete-orphan")


class ScheduledTripFrequency(Base):
    __tablename__ = "scheduled_trip_frequency"

    pk = Column(Integer, primary_key=True)
    trip_pk = Column(Integer, ForeignKey("scheduled_trip.pk"), nullable=False)

    start_time = Column(Time(timezone=True), nullable=False)
    end_time = Column(Time(timezone=True), nullable=False)
    headway = Column(Integer, nullable=False)
    frequency_based = Column(Boolean, default=True, nullable=False)
