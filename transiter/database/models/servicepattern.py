from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, Float, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base


class ServicePattern(Base):
    __tablename__ = 'service_patterns'

    id = Column(Integer, primary_key=True)
    route_pri_key = Column(Integer, ForeignKey('routes.id'))
    name = Column(String)

    route = relationship("Route",
                         foreign_keys=[route_pri_key],
                         back_populates='service_patterns')
    vertices = relationship("ServicePatternVertex",
                            back_populates='service_pattern',
                            order_by="ServicePatternVertex.position",
                            cascade='all, delete-orphan')
    # edges=? How can we delete them

