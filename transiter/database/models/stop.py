from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base


class Stop(Base):
    __tablename__ = 'stop'

    pk = Column(Integer, primary_key=True)
    id = Column(String)
    system_id = Column(String, ForeignKey('system.id'))
    station_pk = Column(Integer, ForeignKey('station.pk'), index=True)

    name = Column(String)
    longitude = Column(Numeric(precision=9, scale=6))
    latitude = Column(Numeric(precision=9, scale=6))

    system = relationship(
        'System')
    station = relationship(
        'Station',
        back_populates='stops')
    direction_name_rules = relationship(
        'DirectionNameRule',
        back_populates='stop',
        cascade='all, delete-orphan',
        order_by='DirectionNameRule.priority')
    stop_events = relationship(
        'StopTimeUpdate',
        back_populates='stop',
        cascade='all, delete-orphan')
    service_pattern_vertices = relationship(
        'ServicePatternVertex',
        back_populates='stop',
        cascade='all, delete-orphan')
    stop_id_aliases = relationship(
        'StopIdAlias',
        back_populates='stop',
        cascade='all, delete-orphan')

    __table_args__ = (UniqueConstraint('system_id', 'id'), )

    _short_repr_list = ['id', 'name']
