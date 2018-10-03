from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, Float, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base


class RouteListEntry(Base):
    __tablename__ = 'route_list_entries'

    id = Column(Integer, primary_key=True)
    stop_pri_key = Column(Integer, ForeignKey("stops.id"), index=True)
    route_pri_key = Column(Integer, ForeignKey("routes.id"), index=True)
    position = Column(Integer)

    stop = relationship("Stop") #, back_populates="direction_names")
    route = relationship("Route")#, back_populates="list_entries")