from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship

from transiter import parse
from .base import Base
from .updatableentity import updatable_from


@updatable_from(parse.Alert)
class Alert(Base):
    __tablename__ = "alert"

    pk = Column(Integer, primary_key=True)
    id = Column(String)
    source_pk = Column(Integer, ForeignKey("feed_update.pk"), index=True)

    Cause = parse.Alert.Cause
    Effect = parse.Alert.Effect

    header = Column(String)
    description = Column(String)
    url = Column(String)

    cause = Column(Enum(Cause, native_enum=False))
    effect = Column(Enum(Effect, native_enum=False))
    priority = Column(Integer)
    start_time = Column(TIMESTAMP(timezone=True))
    end_time = Column(TIMESTAMP(timezone=True))
    creation_time = Column(TIMESTAMP(timezone=True))

    # NOTE: the following foreign key is *temporary*! It is used when, in a feed, the
    # alert's selector references an agency. Pending the introduction of a
    # models.Agency type with which we can many-to-many relate, we just relate such an
    # alert to the system it is in.
    system_pk = Column(Integer, ForeignKey("system.pk"), index=True)

    route_ids = set()
    agency_ids = set()

    source = relationship("FeedUpdate", cascade="none")
    routes = relationship(
        "Route",
        secondary="alert_route",
        back_populates="route_statuses",
        cascade="none",
    )

    @staticmethod
    def from_parsed_alert(alert: parse.Alert) -> "Alert":
        return Alert(
            id=alert.id,
            cause=alert.cause,
            effect=alert.effect,
            header=alert.header,
            description=alert.description,
            url=alert.url,
            start_time=alert.start_time,
            end_time=alert.end_time,
            priority=alert.priority,
        )


alert_route = Table(
    "alert_route",
    Base.metadata,
    Column("alert_pk", Integer, ForeignKey("alert.pk")),
    Column("route_pk", Integer, ForeignKey("route.pk"), index=True),
)
