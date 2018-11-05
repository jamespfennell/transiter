from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class DirectionName(Base):
    __tablename__ = 'direction_names'

    id = Column(Integer, primary_key=True)
    stop_pri_key = Column(Integer, ForeignKey("stops.id"), index=True)
    direction = Column(String)
    name = Column(String)
    track = Column(String)

    stop = relationship("Stop", back_populates="direction_names")

