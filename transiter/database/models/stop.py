from sqlalchemy import Column, Integer, String, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base


class Stop(Base):
    __tablename__ = 'stops'

    id = Column(Integer, primary_key=True)
    stop_id = Column(String, index=True)
    station_pri_key = Column(Integer, ForeignKey("stations.id"), index=True)
    system_id = Column(String, ForeignKey("systems.system_id"), index=True)
    name = Column(String)
    longitude = Column(Numeric(precision=9, scale=6))
    lattitude = Column(Numeric(precision=9, scale=6))

    system = relationship("System")
    station = relationship("Station", back_populates="stops")
    direction_names = relationship("DirectionName", back_populates="stop",
                                   cascade="all, delete-orphan")
    stop_events = relationship("StopEvent", back_populates="stop",
        cascade="all, delete-orphan")

    def repr_for_list(self, verbose=False):
        return {
            'stop_id': self.stop_id,
            'name': self.name,
            'location': 'NI',
            'usual_service': 'NI',
            'href': 'NI'
        }