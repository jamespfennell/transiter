from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, Float, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base


class ServicePattern(Base):
    __tablename__ = 'service_pattern'

    pk = Column(Integer, primary_key=True)
    route_pk = Column(Integer, ForeignKey('route.pk'), index=True, nullable=False)
    name = Column(String)
    # use_for_routes_at_stop = Column(Boolean)

    route = relationship(
        'Route',
        foreign_keys=[route_pk],
        back_populates='service_patterns')
    vertices = relationship(
        'ServicePatternVertex',
        back_populates='service_pattern',
        order_by='ServicePatternVertex.position',
        cascade='all, delete-orphan')
    # edges=? How can we delete them

