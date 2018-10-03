from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, Float, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base

class Trip(Base):
    __tablename__ = 'trips'

    id = Column(Integer, primary_key=True)
    trip_id = Column(String, unique=True, index=True)
    route_pri_key = Column(Integer, ForeignKey("routes.id"))
    direction = Column(String)
    start_time = Column(TIMESTAMP(timezone=True))
    is_assigned = Column(Boolean)
    train_id = Column(String)
    last_update_time = Column(TIMESTAMP(timezone=True))
    current_status = Column(String)
    current_stop_sequence = Column(Integer)

    route = relationship("Route", back_populates="trips")
    stop_events = relationship("StopEvent", back_populates="trip")


    def repr_for_list(self):
        return {
            'trip_id': self.trip_id
        }
    def repr_for_get(self):
        return {
            'trip_id': self.trip_id
        }