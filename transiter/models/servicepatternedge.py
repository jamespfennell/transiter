from sqlalchemy import Column, Integer, ForeignKey

from .base import Base


class ServicePatternEdge(Base):
    __tablename__ = 'service_pattern_edge'

    pk = Column(Integer, primary_key=True)
    source_pk = Column(Integer, ForeignKey('service_pattern_vertex.pk'))
    target_pk = Column(Integer, ForeignKey('service_pattern_vertex.pk'))

    #source = Relationship
    #target = Relationship
