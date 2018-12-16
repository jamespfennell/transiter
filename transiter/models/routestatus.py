from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class RouteStatus(Base):
    __tablename__ = 'route_status'

    pk = Column(Integer, primary_key=True)
    id = Column(String)

    type = Column(String)
    priority = Column(Integer)
    message_title = Column(String)
    message_content = Column(String)
    start_time = Column(TIMESTAMP(timezone=True))
    end_time = Column(TIMESTAMP(timezone=True))
    creation_time = Column(TIMESTAMP(timezone=True))

    route_ids = set()
    routes = relationship(
        'Route',
        secondary='route_status_route',
        back_populates='route_statuses',
        cascade='none'
    )

    _short_repr_list = [
        'id',
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