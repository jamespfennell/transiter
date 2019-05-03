from sqlalchemy import Column, UniqueConstraint, Time, Integer, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class ScheduledTripStopTime(Base):
    __tablename__ = "scheduled_trip_stop_time"

    pk = Column(Integer, primary_key=True)
    trip_pk = Column(Integer, ForeignKey("scheduled_trip.pk"), nullable=False)
    stop_pk = Column(Integer, ForeignKey("stop.pk"), nullable=False)

    arrival_time = Column(Time(timezone=False))
    departure_time = Column(Time(timezone=False))
    stop_sequence = Column(Integer, nullable=False)

    stop = relationship("Stop", back_populates="scheduled_trip_times", cascade="")
    trip = relationship("ScheduledTrip", back_populates="stop_times", cascade="")

    __table_args__ = (UniqueConstraint("trip_pk", "stop_sequence"),)
