import datetime

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

from .base import Base, ToDictMixin


class TripStopTime(ToDictMixin, Base):
    __tablename__ = "trip_stop_time"

    pk = Column(Integer, primary_key=True)
    stop_pk = Column(Integer, ForeignKey("stop.pk"), nullable=False)
    trip_pk = Column(Integer, ForeignKey("trip.pk"), nullable=False)

    future = Column(Boolean, default=True, nullable=False)
    arrival_time = Column(TIMESTAMP(timezone=True))
    arrival_delay = Column(Integer)
    arrival_uncertainty = Column(Integer)
    departure_time = Column(DateTime(timezone=True))
    departure_delay = Column(Integer)
    departure_uncertainty = Column(Integer)
    stop_sequence = Column(Integer, nullable=False)
    track = Column(String)

    stop_id = None

    stop = relationship("Stop", back_populates="trip_times", cascade="none")
    trip = relationship(
        "Trip", back_populates="stop_times", cascade="none", cascade_backrefs=False
    )

    __table_args__ = (
        UniqueConstraint(trip_pk, stop_sequence),
        Index("trip_stop_time_stop_pk_arrival_time_idx", stop_pk, arrival_time),
    )

    _short_repr_list = [arrival_time, departure_time, track, future, stop_sequence]

    def to_dict(self):
        return {
            "arrival": {
                "time": self.arrival_time,
                "delay": self.arrival_delay,
                "uncertainty": self.arrival_uncertainty,
            },
            "departure": {
                "time": self.departure_time,
                "delay": self.departure_delay,
                "uncertainty": self.departure_uncertainty,
            },
            "track": self.track,
            "future": self.future,
            "stop_sequence": self.stop_sequence,
        }

    def get_time(self):
        if self.arrival_time is not None:
            return self.arrival_time
        return self.departure_time

    __mapping_columns__ = [
        pk,
        stop_pk,
        trip_pk,
        future,
        arrival_delay,
        arrival_time,
        arrival_uncertainty,
        departure_delay,
        departure_time,
        departure_uncertainty,
        stop_sequence,
        track,
    ]

    def to_mapping(self):
        return self._to_dict(self.__mapping_columns__)

    @staticmethod
    def from_feed(
        *,
        trip_id: str,
        stop_id: str,
        stop_sequence: int = None,
        future: bool = True,
        departure_time: datetime.datetime = None,
        departure_delay: int = None,
        departure_uncertainty: int = None,
        arrival_time: datetime.datetime = None,
        arrival_delay: int = None,
        arrival_uncertainty: int = None,
        track: str = None,
    ):
        return TripStopTimeLight(
            trip_id=trip_id,
            stop_id=stop_id,
            stop_sequence=stop_sequence,
            future=future,
            departure_time=departure_time,
            departure_delay=departure_delay,
            departure_uncertainty=departure_uncertainty,
            arrival_time=arrival_time,
            arrival_delay=arrival_delay,
            arrival_uncertainty=arrival_uncertainty,
            track=track,
        )


class TripStopTimeLight:

    __user_db_fields__ = {
        "future",
        "arrival_delay",
        "arrival_time",
        "arrival_uncertainty",
        "departure_delay",
        "departure_time",
        "departure_uncertainty",
        "stop_sequence",
        "track",
    }
    __user_non_db_fields = {
        "trip_id",
        "stop_id",
    }
    __other_db_fields__ = {
        "pk",
        "stop_pk",
        "trip_pk",
    }

    pk = None

    def __init__(
        self, **kwargs,
    ):
        for key, value in kwargs.items():
            if (
                key not in self.__user_db_fields__
                and key not in self.__user_non_db_fields
            ):
                raise KeyError(
                    "Unexpected argument to TripStopTime constructor: {}".format(key)
                )
            setattr(self, key, value)

    def to_mapping(self):
        d = {}
        for attr in self.__user_db_fields__:
            d[attr] = getattr(self, attr, None)
        for attr in self.__other_db_fields__:
            d[attr] = getattr(self, attr, None)
        return d

    def __repr__(self):
        return str(self.to_mapping())

    def __eq__(self, other):
        return self.to_mapping() == other.to_mapping()
