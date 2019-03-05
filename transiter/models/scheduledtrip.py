
from sqlalchemy import Column, TIMESTAMP, UniqueConstraint, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class ScheduledTrip(Base):
    __tablename__ = 'scheduled_trip'

    pk = Column(Integer, primary_key=True)
    id = Column(String, nullable=False)
    route_pk = Column(Integer, ForeignKey('route.pk'), nullable=False)
    service_pk = Column(Integer, ForeignKey('scheduled_service.pk'), nullable=False)

    direction_id = Column(Boolean)

    raw_service_map_string = Column(String, index=True)
    #crosses_midnight = Column(Boolean, default=False)
    # Investigate not deuplicating this data
    #start_time = Column(TIMESTAMP)
    #end_time = Column(TIMESTAMP)

    route = relationship(
        'Route',
        cascade=''
    )
    service = relationship(
        'ScheduledService',
        back_populates='trips',
        cascade=''
    )
    stop_times = relationship(
        'ScheduledTripStopTime',
        back_populates='trip',
        cascade='all, delete-orphan',
        # order_by='ScheduledTripStopTime.stop_sequence'
    )


"""
reverse_property 'trip' on relationship ScheduledTrip.stop_times 
references relationship ScheduledTripStopTime.trip, which does not reference 
mapper Mapper|ScheduledTrip|scheduled_trip
"""

