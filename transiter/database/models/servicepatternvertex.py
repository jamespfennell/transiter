from sqlalchemy import Column, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship

from .base import Base


class ServicePatternVertex(Base):
    __tablename__ = 'service_pattern_vertices'

    id = Column(Integer, primary_key=True)
    stop_pri_key = Column(Integer, ForeignKey('stops.id'))
    position = Column(Integer)
    service_pattern_pri_key = Column(Integer,
                                     ForeignKey('service_patterns.id'))

    stop = relationship("Stop")
    service_pattern = relationship("ServicePattern",
                                   back_populates='vertices')


Index('service_pattern_vertex_sp_position',
      ServicePatternVertex.service_pattern_pri_key,
      ServicePatternVertex.position)
