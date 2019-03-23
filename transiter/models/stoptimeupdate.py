from sqlalchemy import Column, TIMESTAMP, DateTime, Index, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from .base import Base


#TODO(!) rename TripStopTime
class StopTimeUpdate(Base):
    __tablename__ = 'stop_time_update'

    pk = Column(Integer, primary_key=True)
    stop_pk = Column(Integer, ForeignKey('stop.pk'), nullable=False)
    trip_pk = Column(Integer, ForeignKey('trip.pk'), nullable=False)

    future = Column(Boolean, server_default=text('true'))
    arrival_time = Column(TIMESTAMP(timezone=True))
    departure_time = Column(DateTime(timezone=True))
    #departure_time = Column(TIMESTAMP(timezone=True))
    last_update_time = Column(TIMESTAMP(timezone=True))
    # TODO add a unique constraint on stop_sequence, trip_pk
    stop_sequence = Column(Integer, nullable=False)
    track = Column(String)

    stop_id = None

    stop = relationship(
        'Stop',
        back_populates='stop_events',
        cascade='')
    trip = relationship(
        'Trip',
        back_populates='stop_events',
        cascade='',
        cascade_backrefs=False
    )

    _short_repr_list = ['arrival_time', 'departure_time', 'track', 'future']


Index('stop_time_update_trip_idx', StopTimeUpdate.trip_pk, StopTimeUpdate.stop_sequence)
Index('stop_time_update_stop_idx', StopTimeUpdate.stop_pk, StopTimeUpdate.arrival_time)

