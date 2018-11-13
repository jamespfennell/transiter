from sqlalchemy import Column, TIMESTAMP, Integer, String, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship

from .base import Base


class Trip(Base):
    __tablename__ = 'trips'

    id = Column(Integer, primary_key=True)
    trip_id = Column(String)
    route_pri_key = Column(Integer, ForeignKey("routes.id"), nullable=False)
    # TODO: rename to direction_id and make boolean
    direction = Column(String)
    direction_id = Column(Boolean)
    start_time = Column(TIMESTAMP(timezone=True))
    # TODO: remove
    is_assigned = Column(Boolean)
    train_id = Column(String)
    last_update_time = Column(TIMESTAMP(timezone=True))
    feed_update_time = Column(TIMESTAMP(timezone=True))
    # TODO: rename status
    current_status = Column(String)
    # This is redundant -> can be inferred from stop events
    current_stop_sequence = Column(Integer)

    route = relationship("Route", back_populates="trips")
    stop_events = relationship("StopEvent",
                               back_populates="trip",
                               order_by="StopEvent.sequence_index",
                               cascade="all, delete-orphan")

    _short_repr_list = ['trip_id']
    _long_repr_list = [
        'trip_id',
        'direction_id',
        'start_time',
        'last_update_time',
        'feed_update_time',
        'status',
        'train_id'
    ]


Index('get_trip_in_route_idx',
      Trip.route_pri_key,
      Trip.trip_id)