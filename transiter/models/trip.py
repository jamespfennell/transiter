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

    route_id = None
    stop_id = None

    vehicle_id = Column(String)
    last_update_time = Column(TIMESTAMP(timezone=True))
    current_status = Column(String)
    current_stop_sequence = Column(Integer)

    route = relationship(
        'Route',
        back_populates='trips',
        cascade='')
    # TODO: rename stop_time_updates
    stop_events = relationship(
        'StopTimeUpdate',
        back_populates='trip',
        order_by='StopTimeUpdate.stop_sequence',
        cascade='delete, delete-orphan',
        cascade_backrefs=False
    )

    _short_repr_list = ['id']
    _long_repr_list = [
        'id',
        'direction_id',
        'start_time',
        'last_update_time',
        'current_status',
        'current_stop_sequence',
        'vehicle_id'
    ]

# TODO: this should be a unique constraint
Index('get_trip_in_route_idx',
      Trip.route_pk,
      Trip.id)
