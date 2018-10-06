from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, Float, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base

class Trip(Base):
    __tablename__ = 'trips'

    id = Column(Integer, primary_key=True)
    trip_id = Column(String, index=True)
    route_pri_key = Column(Integer, ForeignKey("routes.id"), nullable=False)
    direction = Column(String)
    start_time = Column(TIMESTAMP(timezone=True))
    # TODO: remove
    is_assigned = Column(Boolean)
    train_id = Column(String)
    last_update_time = Column(TIMESTAMP(timezone=True))
    feed_update_time = Column(TIMESTAMP(timezone=True))
    #TODO: rename status
    current_status = Column(String)
    current_stop_sequence = Column(Integer)

    route = relationship("Route", back_populates="trips")
    stop_events = relationship("StopEvent",
                               back_populates="trip",
                               order_by="StopEvent.sequence_index",
                               cascade="all, delete-orphan")


    def repr_for_list(self):
        return {
            'trip_id': self.trip_id
        }
    def repr_for_get(self):
        return {
            'trip_id': self.trip_id,
            'direction': self.direction,
            'start_time': self.start_time,
            'last_update_time': self.last_update_time,
            'feed_update_time': self.feed_update_time,
            'status': self.current_status,
            'train_id': self.train_id,
            'terminus': 'NI'
        }