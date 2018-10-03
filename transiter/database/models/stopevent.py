from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, Float, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base


class StopEvent(Base):
    __tablename__ = 'stop_events'

    id = Column(Integer, primary_key=True)
    stop_pri_key = Column(Integer, ForeignKey('stops.id'))
    trip_pri_key = Column(Integer, ForeignKey('trips.id'))
    future = Column(Boolean)
    arrival_time = Column(TIMESTAMP(timezone=True))
    departure_time = Column(TIMESTAMP(timezone=True))
    last_update_time = Column(TIMESTAMP(timezone=True))
    sequence_index = Column(Integer)
    scheduled_track = Column(String)
    actual_track = Column(String)

    stop = relationship("Stop", back_populates="stop_events")
    trip = relationship("Trip", back_populates="stop_events")