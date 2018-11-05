from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, Float, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base

class Station(Base):
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True)
    borough = Column(String)
    name = Column(String)
    system_id = Column(String, ForeignKey("systems.system_id"), index=True)

    system = relationship("System", back_populates="stations")
    stops = relationship("Stop", back_populates="station", cascade="all, delete-orphan")

    _short_repr_list = ['name']
    _short_repr_dict = {'station_id': 'id'}

