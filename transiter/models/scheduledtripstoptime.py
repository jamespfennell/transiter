from sqlalchemy import Column, UniqueConstraint, Index, Time, Integer, ForeignKey
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

    __table_args__ = (
        UniqueConstraint("trip_pk", "stop_sequence"),
        Index(
            "scheduled_trip_stop_time_trip_pk_departure_time_idx",
            "trip_pk",
            "departure_time",
        ),
    )


class ScheduledTripStopTimeLight:
    arrival_time = None
    departure_time = None
    stop_sequence = None
    stop_id = None

    def __eq__(self, other):
        return (
            str(self.arrival_time) == str(other.arrival_time)
            and str(self.departure_time) == str(other.departure_time)
            and self.stop_sequence == other.stop_sequence
            and self.stop_id == other.stop_id
        )

    def __repr__(self):
        props = []
        for key, value in self.__dict__.items():
            if key[0] == "_":
                continue
            props.append("{}={}".format(key, value))
        return "ScheduledTripStopTimeLight({})".format(", ".join(sorted(props)))
