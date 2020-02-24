import enum

from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship

from .base import Base, ToDictMixin
from .updatableentity import updatable_entity


@updatable_entity
class Alert(ToDictMixin, Base):
    __tablename__ = "alert"

    pk = Column(Integer, primary_key=True)
    id = Column(String)
    source_pk = Column(Integer, ForeignKey("feed_update.pk"), index=True)

    class Cause(enum.Enum):
        UNKNOWN_CAUSE = 1
        OTHER_CAUSE = 2
        TECHNICAL_PROBLEM = 3
        STRIKE = 4
        DEMONSTRATION = 5
        ACCIDENT = 6
        HOLIDAY = 7
        WEATHER = 8
        MAINTENANCE = 9
        CONSTRUCTION = 10
        POLICE_ACTIVITY = 11
        MEDICAL_EMERGENCY = 12

    class Effect(enum.Enum):
        NO_SERVICE = 0
        REDUCED_SERVICE = 1
        SIGNIFICANT_DELAYS = 2
        DETOUR = 3
        ADDITIONAL_SERVICE = 4
        MODIFIED_SERVICE = 5
        OTHER_EFFECT = 6
        UNKNOWN_EFFECT = 7
        STOP_MOVED = 8

    header = Column(String)
    description = Column(String)
    url = Column(String)

    cause = Column(Enum(Cause))
    effect = Column(Enum(Effect))
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

    __dict_columns__ = [id, start_time, end_time, creation_time, header, description]
    __large_dict_columns__ = [
        id,
        start_time,
        end_time,
        creation_time,
        header,
        description,
        url,
        cause,
        effect,
    ]


alert_route = Table(
    "alert_route",
    Base.metadata,
    Column("alert_pk", Integer, ForeignKey("alert.pk")),
    Column("route_pk", Integer, ForeignKey("route.pk"), index=True),
)
