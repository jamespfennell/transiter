from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base


class Stop(Base):
    __tablename__ = 'stops'

    id = Column(Integer, primary_key=True)
    stop_id = Column(String, index=True)
    station_pri_key = Column(Integer, ForeignKey("stations.id"), index=True)
    system_id = Column(String, ForeignKey("systems.system_id"), index=True)
    name = Column(String)
    longitude = Column(Numeric(precision=9, scale=6))
    latitude = Column(Numeric(precision=9, scale=6))

    system = relationship("System")
    station = relationship("Station", back_populates="stops")
    direction_name_rules = relationship(
        "DirectionNameRule",
        back_populates="stop",
        cascade="all, delete-orphan",
        order_by='DirectionNameRule.priority')
    stop_events = relationship("StopEvent", back_populates="stop",
        cascade="all, delete-orphan")

    service_pattern_vertices = relationship(
        "ServicePatternVertex",
        back_populates="stop",
        cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint('system_id', 'stop_id'), )

    stop_aliases = relationship(
        "StopAlias",
        back_populates="stop",
        cascade="all, delete-orphan")

    _short_repr_list = ['stop_id', 'name']
