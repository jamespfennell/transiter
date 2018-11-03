from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, Float, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base, model_eq


class ServicePatternVertex(Base):
    __tablename__ = 'service_pattern_vertices'

    id = Column(Integer, primary_key=True)
    stop_pri_key = Column(Integer, ForeignKey('stops.id'))
    position = Column(Integer, index=True)
    service_pattern_pri_key = Column(Integer,
                                     ForeignKey('service_patterns.id'))

    stop = relationship("Stop")
    service_pattern = relationship("ServicePattern",
                                   back_populates='vertices')

    def __eq__(self, other):
        return model_eq(self, other)
