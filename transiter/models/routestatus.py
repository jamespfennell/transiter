from sqlalchemy import Boolean, Column, TIMESTAMP, Table, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship

from .base import Base
import enum


# TODO: Rename Alert (following
# GTFS realtime. Also update routeendpoint with the right api when this is done
class RouteStatus(Base):
    __tablename__ = 'route_status'

    pk = Column(Integer, primary_key=True)
    id = Column(String)

    # TODO: delete the first 3 here
    type = Column(String)
    message_title = Column(String)
    message_content = Column(String)
    start_time = Column(TIMESTAMP(timezone=True))
    end_time = Column(TIMESTAMP(timezone=True))
    creation_time = Column(TIMESTAMP(timezone=True))

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

    route_ids = set()

    routes = relationship(
        'Route',
        secondary='route_status_route',
        back_populates='route_statuses',
        cascade='none'
    )

    _short_repr_list = [
        'id',
        'type',
        'message_title',
        'message_content',
        'start_time',
        'end_time',
        'creation_time',
    ]


route_status_route = Table(
    'route_status_route',
    Base.metadata,
    Column('route_status_pk', Integer, ForeignKey('route_status.pk')),
    Column('route_pk', Integer, ForeignKey('route.pk'), index=True)
)