import enum

from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship

from .base import Base


class Alert(Base):
    __tablename__ = "alert"

    pk = Column(Integer, primary_key=True)
    id = Column(String)

    class Cause(enum.Enum):
        ACCIDENT = 1
        MAINTENANCE = 2

    class Effect(enum.Enum):
        MODIFIED_SERVICE = 1
        SIGNIFICANT_DELAYS = 2

    header = Column(String)
    description = Column(String)
    cause = Column(Enum(Cause))
    effect = Column(Enum(Effect))
    priority = Column(Integer)
    start_time = Column(TIMESTAMP(timezone=True))
    end_time = Column(TIMESTAMP(timezone=True))
    creation_time = Column(TIMESTAMP(timezone=True))

    route_ids = set()

    routes = relationship(
        "Route",
        secondary="alert_route",
        back_populates="route_statuses",
        cascade="none",
    )

    _short_repr_list = [id, start_time, end_time, creation_time, header, description]


alert_route = Table(
    "alert_route",
    Base.metadata,
    Column("alert_pk", Integer, ForeignKey("alert.pk")),
    Column("route_pk", Integer, ForeignKey("route.pk"), index=True),
)
