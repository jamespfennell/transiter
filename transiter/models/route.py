from sqlalchemy import Column, TIMESTAMP, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class Route(Base):
    __tablename__ = 'route'

    pk = Column(Integer, primary_key=True)
    id = Column(String, index=True)
    system_id = Column(String, ForeignKey('system.id'), index=True)

    frequency = Column(Float, nullable=True, default=None)
    running = Column(Boolean, default=False)
    color = Column(String)
    short_name = Column(String)
    long_name = Column(String)
    description = Column(String)
    timetable_url = Column(String)
    last_update_time = Column(TIMESTAMP(timezone=True))

    system = relationship(
        'System',
        back_populates='routes')
    trips = relationship(
        'Trip',
        back_populates='route',
        cascade='delete, delete-orphan')
    service_patterns = relationship(
        'ServicePattern',
        back_populates='route',
        primaryjoin='ServicePattern.route_pk==Route.pk',
        cascade='all, delete-orphan')
    route_statuses = relationship(
        'RouteStatus',
        secondary='route_status_route',
        back_populates='routes')

    # NOTE(fennell): need the post_update=True condition on all of these relationships
    # because the service_patterns table has a FK constraint to this table.
    # TODO: stops_in_route_service_map_pk = ...
    regular_service_pattern_pk = Column(
        Integer,
        ForeignKey('service_pattern.pk', name='james_f_1')
    )
    regular_service_pattern = relationship(
        'ServicePattern',
        post_update=True,
        foreign_keys=[regular_service_pattern_pk])
    default_service_pattern_pk = Column(
        Integer,
        ForeignKey('service_pattern.pk', name='james_f_2')
    )
    default_service_pattern = relationship(
        'ServicePattern',
        post_update=True,
        foreign_keys=[default_service_pattern_pk])
    dynamic_service_pattern_pk = Column(
        Integer,
        ForeignKey('service_pattern.pk', name='james_f_3')
    )
    dynamic_service_pattern = relationship(
        'ServicePattern',
        post_update=True,
        foreign_keys=[dynamic_service_pattern_pk])

    _short_repr_list = ['id'] #, 'system_id']
    _long_repr_list = ['id']
