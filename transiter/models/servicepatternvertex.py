from sqlalchemy import Column, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship

from .base import Base


class ServicePatternVertex(Base):
    __tablename__ = "service_pattern_vertex"

    pk = Column(Integer, primary_key=True)
    stop_pk = Column(Integer, ForeignKey("stop.pk"))
    # TODO: change to map_pk
    service_pattern_pk = Column(Integer, ForeignKey("service_pattern.pk"))

    position = Column(Integer)

    stop = relationship("Stop")
    # TODO change to map
    service_pattern = relationship("ServicePattern", back_populates="vertices")


Index(
    "service_pattern_vertex_sp_position",
    ServicePatternVertex.service_pattern_pk,
    ServicePatternVertex.position,
)
