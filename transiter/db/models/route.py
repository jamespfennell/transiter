from sqlalchemy import Column, Integer, String, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship

from transiter import parse
from .base import Base
from .updatableentity import updatable_from


@updatable_from(parse.Route)
class Route(Base):
    __tablename__ = "route"

    pk = Column(Integer, primary_key=True)
    id = Column(String)
    agency_pk = Column(Integer, ForeignKey("agency.pk"))
    source_pk = Column(
        Integer, ForeignKey("feed_update.pk"), index=True, nullable=False
    )
    system_pk = Column(Integer, ForeignKey("system.pk"), nullable=False)

    Type = parse.Route.Type
    BoardingPolicy = parse.BoardingPolicy

    color = Column(String)
    text_color = Column(String)
    short_name = Column(String)
    long_name = Column(String)
    description = Column(String)
    url = Column(String)
    type = Column(Enum(Type, name="route_type", native_enum=False))
    sort_order = Column(Integer)
    continuous_pickup = Column(
        Enum(BoardingPolicy, native_enum=False),
        nullable=False,
        default=BoardingPolicy.NOT_ALLOWED,
    )
    continuous_drop_off = Column(
        Enum(BoardingPolicy, native_enum=False),
        nullable=False,
        default=BoardingPolicy.NOT_ALLOWED,
    )

    system = relationship("System", back_populates="routes")
    agency = relationship("Agency", back_populates="routes")
    source = relationship("FeedUpdate", cascade="none")
    trips = relationship("Trip", back_populates="route", cascade="all, delete-orphan")
    scheduled_trips = relationship(
        "ScheduledTrip", back_populates="route", cascade="all, delete-orphan"
    )
    service_maps = relationship(
        "ServiceMap",
        back_populates="route",
        primaryjoin="ServiceMap.route_pk==Route.pk",
        cascade="all, delete-orphan",
    )
    alerts = relationship(
        "Alert", secondary="alert_route", back_populates="routes", cascade="all"
    )

    __table_args__ = (UniqueConstraint("system_pk", "id"),)

    @staticmethod
    def from_parsed_route(route: parse.Route) -> "Route":
        return Route(
            id=route.id,
            type=route.type,
            short_name=route.short_name,
            long_name=route.long_name,
            description=route.description,
            color=route.color,
            text_color=route.text_color,
            url=route.url,
            sort_order=route.sort_order,
            continuous_pickup=route.continuous_pickup,
            continuous_drop_off=route.continuous_drop_off,
        )
