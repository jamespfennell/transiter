import enum

from sqlalchemy import (
    Column,
    Enum,
    TIMESTAMP,
    Integer,
    String,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .base import Base
from .updatableentity import updatable_entity


@updatable_entity
class Trip(Base):
    __tablename__ = "trip"

    pk = Column(Integer, primary_key=True)
    id = Column(String)
    route_pk = Column(Integer, ForeignKey("route.pk"), nullable=False)
    source_pk = Column(Integer, ForeignKey("feed_update.pk"), index=True)

    class TripStatus(enum.Enum):
        SCHEDULED = 1
        INCOMING_AT = 2
        STOPPED_AT = 3
        IN_TRANSIT_TO = 4

    direction_id = Column(Boolean)
    start_time = Column(TIMESTAMP(timezone=True))

    last_update_time = Column(TIMESTAMP(timezone=True))
    vehicle_id = Column(String)
    current_status = Column(Enum(TripStatus))
    current_stop_sequence = Column(Integer)

    route_id = None
    stop_id = None

    source = relationship("FeedUpdate", cascade="none")
    route = relationship("Route", back_populates="trips", cascade="")
    stop_times = relationship(
        "TripStopTime",
        back_populates="trip",
        order_by="TripStopTime.stop_sequence",
        cascade="all, delete-orphan",
        cascade_backrefs=False,
    )

    __table_args__ = (UniqueConstraint(route_pk, id),)

    _short_repr_list = [id]
    _long_repr_list = [
        id,
        direction_id,
        start_time,
        last_update_time,
        current_status,
        current_stop_sequence,
        vehicle_id,
    ]
