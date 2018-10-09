from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, Float, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base


class ServicePatternVertex(Base):
    __tablename__ = 'service_pattern_vertices'

    id = Column(Integer, primary_key=True)
    stop_pri_key = Column(Integer, ForeignKey('stops.id'))
    position = Column(Integer, index=True)
    service_pattern_pri_key = Column(Integer,
                                     ForeignKey('service_patterns.id'))

    #stop = Relationship
    #service_pattern = Relationship
    pass
    """

    service_pattern_pri_key
    stop_pri_key
    position =
    """
