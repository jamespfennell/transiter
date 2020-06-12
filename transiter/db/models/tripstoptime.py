from sqlalchemy import (
    Column,
    TIMESTAMP,
    DateTime,
    Index,
    Integer,
    String,
    Boolean,
    UniqueConstraint,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from .base import Base


class TripStopTime(Base):
    __tablename__ = "trip_stop_time"

    pk = Column(Integer, primary_key=True)
    stop_pk = Column(Integer, ForeignKey("stop.pk"), nullable=False)
    trip_pk = Column(Integer, ForeignKey("trip.pk"), nullable=False)

    arrival_time = Column(TIMESTAMP(timezone=True))
    arrival_delay = Column(Integer)
    arrival_uncertainty = Column(Integer)
    departure_time = Column(DateTime(timezone=True))
    departure_delay = Column(Integer)
    departure_uncertainty = Column(Integer)
    stop_sequence = Column(Integer, nullable=False)
    track = Column(String)

    stop = relationship("Stop", back_populates="trip_times", cascade="none")
    trip = relationship(
        "Trip", back_populates="stop_times", cascade="none", cascade_backrefs=False
    )

    __table_args__ = (
        UniqueConstraint(trip_pk, stop_sequence),
        Index("trip_stop_time_stop_pk_arrival_time_idx", stop_pk, arrival_time),
    )

    def get_time(self):
        return self.arrival_time or self.departure_time

    @property
    def future(self):
        # NOTE: negative trip stop sequences are interpreted as indicating that
        # all stops are passed.
        return 0 <= self.trip.current_stop_sequence <= self.stop_sequence
