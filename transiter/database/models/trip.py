from sqlalchemy import Column, TIMESTAMP, Integer, String, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship

from .base import Base


class Trip(Base):
    __tablename__ = 'trip'

    pk = Column(Integer, primary_key=True)
    id = Column(String)
    route_pk = Column(Integer, ForeignKey('route.pk'), nullable=False)

    direction_id = Column(Boolean)
    start_time = Column(TIMESTAMP(timezone=True))
    # TODO: remove, incorporate into status
    is_assigned = Column(Boolean)
    # TODO: rename vehicle_id
    train_id = Column(String)
    # TODO: both of these should be foreign keyed to feed updates
    last_update_time = Column(TIMESTAMP(timezone=True))
    feed_update_time = Column(TIMESTAMP(timezone=True))
    # TODO: rename status
    current_status = Column(String)
    # TODO This is redundant -> can be inferred from stop events
    current_stop_sequence = Column(Integer)

    route = relationship(
        'Route',
        back_populates='trips')
    stop_events = relationship(
        'StopTimeUpdate',
        back_populates='trip',
        order_by='StopTimeUpdate.stop_sequence',
        cascade='all, delete-orphan')

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
      Trip.route_pk,
      Trip.id)
