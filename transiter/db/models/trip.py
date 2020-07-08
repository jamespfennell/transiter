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
    source_pk = Column(
        Integer, ForeignKey("feed_update.pk"), index=True, nullable=False
    )

    direction_id = Column(Boolean)
    started_at = Column(TIMESTAMP(timezone=True))
    updated_at = Column(TIMESTAMP(timezone=True))
    delay = Column(Integer)
    # Stop times are considered in the past if their stop sequence is less than
    # the trip's current stop sequence
    current_stop_sequence = Column(Integer)  # TODO: make non-nullable

    source = relationship("FeedUpdate", cascade="none")
    route = relationship("Route", back_populates="trips", cascade="none")
    vehicle = relationship(
        "Vehicle", back_populates="trip", cascade="none", uselist=False, lazy="joined"
    )
    stop_times = relationship(
        "TripStopTime",
        back_populates="trip",
        order_by="TripStopTime.stop_sequence",
        cascade="all, delete-orphan",
        cascade_backrefs=False,
    )
    alerts = relationship(
        "Alert", secondary="alert_trip", back_populates="trips", cascade="all"
    )

    __table_args__ = (UniqueConstraint(route_pk, id),)
