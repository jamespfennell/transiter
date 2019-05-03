from sqlalchemy import Column, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship

from .base import Base


class ServiceMapVertex(Base):
    __tablename__ = "service_map_vertex"

    pk = Column(Integer, primary_key=True)
    stop_pk = Column(Integer, ForeignKey("stop.pk"))
    map_pk = Column(Integer, ForeignKey("service_map.pk"))

    position = Column(Integer)

    stop = relationship("Stop", cascade=None)
    map = relationship("ServiceMap", back_populates="vertices", cascade=None)

    __table_args__ = (Index("service_map_vertex_map_pk_position", map_pk, position),)
