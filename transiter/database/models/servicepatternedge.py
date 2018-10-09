from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, Float, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base


class ServicePatternEdge(Base):
    __tablename__ = 'service_pattern_edges'

    id = Column(Integer, primary_key=True)
    source_vertex_pri_key = Column(Integer,
                                   ForeignKey('service_pattern_vertices.id'))
    target_vertex_pri_key = Column(Integer,
                                   ForeignKey('service_pattern_vertices.id'))

    #source_vertex = Relationship
    #target_vertex = Relationship
    pass
    """

    id = Column(Integer, primary_key=True)
    service_pattern_pri_key
    stop_pri_key
    position =
    """
