from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, Float, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base


class StopEvent(Base):
    __tablename__ = 'stop_events'

    id = Column(Integer, primary_key=True)
    direction = Column(String)
    stop_pri_key = Column(Integer, ForeignKey('stops.id'), nullable=False)
    trip_pri_key = Column(Integer, ForeignKey('trips.id'), nullable=False)
    # TODO rename to status and make a string
    future = Column(Boolean)
    arrival_time = Column(TIMESTAMP(timezone=True))
    departure_time = Column(TIMESTAMP(timezone=True))
    last_update_time = Column(TIMESTAMP(timezone=True))
    # TODO rename? or is this a GTFS realtime name?
    sequence_index = Column(Integer)
    # TODO(have only one track and let the update logic populate it)
    scheduled_track = Column(String)
    actual_track = Column(String)

    stop = relationship("Stop", back_populates="stop_events")
    trip = relationship("Trip", back_populates="stop_events")

    def repr_for_list(self):
        return {
            'arrival_time': self.arrival_time,
            'departure_time': self.departure_time,
            'scheduled_track': self.scheduled_track,
            'actual_track': self.actual_track,
            'sequence_index': self.sequence_index,
            'status': 'NI'
        }