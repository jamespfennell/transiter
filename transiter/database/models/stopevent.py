from sqlalchemy import Column, TIMESTAMP, Index, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from .base import Base


class StopEvent(Base):
    __tablename__ = 'stop_events'

    id = Column(Integer, primary_key=True)
    direction = Column(String)
    stop_pri_key = Column(Integer, ForeignKey('stops.id'), nullable=False)
    trip_pri_key = Column(Integer, ForeignKey('trips.id'), nullable=False)
    # TODO rename to status and make a string
    future = Column(Boolean, server_default=text('true'))
    arrival_time = Column(TIMESTAMP(timezone=True))
    departure_time = Column(TIMESTAMP(timezone=True))
    last_update_time = Column(TIMESTAMP(timezone=True))
    # TODO rename? or is this a GTFS realtime name?
    sequence_index = Column(Integer, nullable=False)
    track = Column(String)
    stop_id_alias = Column(String)

    stop = relationship("Stop", back_populates="stop_events")
    trip = relationship("Trip", back_populates="stop_events")

    _short_repr_list = [
        'arrival_time', 'departure_time', 'track', 'sequence_index', 'stop_id_alias']


Index('myindex', StopEvent.trip_pri_key, StopEvent.arrival_time)

