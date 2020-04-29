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

from transiter import parse
from .base import Base
from .updatableentity import updatable_from


@updatable_from(parse.Trip)
class Trip(Base):
    __tablename__ = "trip"

    pk = Column(Integer, primary_key=True)
    id = Column(String)
    route_pk = Column(Integer, ForeignKey("route.pk"), nullable=False)
    source_pk = Column(Integer, ForeignKey("feed_update.pk"), index=True)

    TripStatus = parse.Trip.Status

    direction_id = Column(Boolean)
    start_time = Column(TIMESTAMP(timezone=True))

    last_update_time = Column(TIMESTAMP(timezone=True))
    vehicle_id = Column(String)
    current_status = Column(Enum(TripStatus, name="tripstatus", native_enum=False))
    current_stop_sequence = Column(Integer)

    source = relationship("FeedUpdate", cascade="none")
    route = relationship("Route", back_populates="trips", cascade="none")
    stop_times = relationship(
        "TripStopTime",
        back_populates="trip",
        order_by="TripStopTime.stop_sequence",
        cascade="all, delete-orphan",
        cascade_backrefs=False,
    )

    __table_args__ = (UniqueConstraint(route_pk, id),)
