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
    vehicle_pk = Column(Integer, ForeignKey("vehicle.pk"), index=True, unique=True)
    source_pk = Column(Integer, ForeignKey("feed_update.pk"), index=True)

    direction_id = Column(Boolean)
    started_at = Column(TIMESTAMP(timezone=True))
    updated_at = Column(TIMESTAMP(timezone=True))
    delay = Column(Integer)

    source = relationship("FeedUpdate", cascade="none")
    route = relationship("Route", back_populates="trips", cascade="none")
    vehicle = relationship("Vehicle", back_populates="trip", cascade="none")
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
