from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, Float, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base

class Station(Base):
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True)
    borough = Column(String)
    name = Column(String)
    system_id = Column(Integer, ForeignKey("systems.id"), index=True)

    system = relationship("System", back_populates="stations")
    stops = relationship("Stop", back_populates="station", cascade="all, delete-orphan")

    def short_repr(self):
        return {
            'station_id': self.id,
            'name': self.name
        }