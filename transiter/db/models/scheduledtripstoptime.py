from sqlalchemy import (
    Column,
    String,
    UniqueConstraint,
    Index,
    Time,
    Integer,
    ForeignKey,
    Enum,
    Float,
    Boolean,
)
from sqlalchemy.orm import relationship

from .base import Base
from transiter import parse


class ScheduledTripStopTime(Base):
    __tablename__ = "scheduled_trip_stop_time"

    pk = Column(Integer, primary_key=True)
    trip_pk = Column(Integer, ForeignKey("scheduled_trip.pk"), nullable=False)
    stop_pk = Column(Integer, ForeignKey("stop.pk"), nullable=False)

    BoardingPolicy = parse.BoardingPolicy

    arrival_time = Column(Time(timezone=False))
    departure_time = Column(Time(timezone=False))
    stop_sequence = Column(Integer, nullable=False)
    headsign = Column(String)
    pickup_type = Column(
        Enum(BoardingPolicy, native_enum=False),
        nullable=False,
        default=BoardingPolicy.ALLOWED,
    )
    drop_off_type = Column(
        Enum(BoardingPolicy, native_enum=False),
        nullable=False,
        default=BoardingPolicy.ALLOWED,
    )
    continuous_pickup = Column(
        Enum(BoardingPolicy, native_enum=False),
        nullable=False,
        default=BoardingPolicy.NOT_ALLOWED,
    )
    continuous_drop_off = Column(
        Enum(BoardingPolicy, native_enum=False),
        nullable=False,
        default=BoardingPolicy.NOT_ALLOWED,
    )
    shape_distance_traveled = Column(Float)
    exact_times = Column(Boolean, nullable=False, default=False)

    stop = relationship("Stop", back_populates="scheduled_trip_times", cascade="")
    trip = relationship("ScheduledTrip", back_populates="stop_times", cascade="")

    __table_args__ = (
        UniqueConstraint("trip_pk", "stop_sequence"),
        Index(
            "scheduled_trip_stop_time_trip_pk_departure_time_idx",
            "trip_pk",
            "departure_time",
        ),
    )
