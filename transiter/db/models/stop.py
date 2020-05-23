from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Numeric,
    UniqueConstraint,
    Enum,
)
from sqlalchemy.orm import relationship, backref

from transiter import parse
from .base import Base
from .updatableentity import updatable_from


@updatable_from(parse.Stop)
class Stop(Base):
    __tablename__ = "stop"

    pk = Column(Integer, primary_key=True)
    id = Column(String)
    system_pk = Column(Integer, ForeignKey("system.pk"), nullable=False)
    source_pk = Column(Integer, ForeignKey("feed_update.pk"), index=True)
    parent_stop_pk = Column(Integer, ForeignKey("stop.pk"), index=True)

    Type = parse.Stop.Type
    STATION_TYPES = {Type.STATION, Type.GROUPED_STATION}
    WheelchairBoarding = parse.Stop.WheelchairBoarding

    name = Column(String)
    longitude = Column(Numeric(precision=9, scale=6))
    latitude = Column(Numeric(precision=9, scale=6))
    type = Column(Enum(Type, native_enum=False), nullable=False)
    code = Column(String)
    description = Column(String)
    zone_id = Column(String)
    url = Column(String)
    timezone = Column(String)
    wheelchair_boarding = Column(
        Enum(WheelchairBoarding, native_enum=False),
        default=WheelchairBoarding.NOT_SPECIFIED,
    )
    platform_code = Column(String)

    system = relationship("System", back_populates="stops")
    source = relationship("FeedUpdate", cascade="none")
    # NOTE: this relationship is a little tricky and this definition follows
    # https://docs.sqlalchemy.org/en/latest/_modules/examples/adjacency_list/adjacency_list.html
    child_stops = relationship(
        "Stop",
        cascade="none",
        backref=backref("parent_stop", remote_side=pk, cascade="none"),
    )
    direction_rules = relationship(
        "DirectionRule",
        back_populates="stop",
        cascade="all, delete-orphan",
        order_by="DirectionRule.priority",
    )
    trip_times = relationship(
        "TripStopTime", back_populates="stop", cascade="delete, delete-orphan"
    )
    service_pattern_vertices = relationship(
        "ServiceMapVertex", back_populates="stop", cascade="delete, delete-orphan"
    )
    scheduled_trip_times = relationship(
        "ScheduledTripStopTime", back_populates="stop", cascade="delete, delete-orphan"
    )
    alerts = relationship(
        "Alert", secondary="alert_stop", back_populates="stops", cascade="all"
    )

    __table_args__ = (UniqueConstraint("system_pk", "id"),)

    @staticmethod
    def from_parsed_stop(stop: parse.Stop) -> "Stop":
        return Stop(
            id=stop.id,
            name=stop.name,
            latitude=stop.latitude,
            longitude=stop.longitude,
            type=stop.type,
            code=stop.code,
            description=stop.description,
            zone_id=stop.zone_id,
            url=stop.url,
            timezone=stop.timezone,
            wheelchair_boarding=stop.wheelchair_boarding,
            platform_code=stop.platform_code,
        )

    def is_station(self):
        return self.type in Stop.STATION_TYPES or self.parent_stop_pk is None
