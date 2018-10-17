from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class System(Base):
    __tablename__ = 'systems'

    id = Column(Integer, primary_key=True)
    system_id = Column(String, unique=True)
    name = Column(String, nullable=True)
    directory_hash = Column(String, nullable=True)

    routes = relationship("Route",
                          back_populates="system",
                          cascade="all, delete-orphan")
    stations = relationship("Station",
                            back_populates="system",
                            cascade="all, delete-orphan")
    feeds = relationship("Feed",
                         back_populates="system",
                         cascade="all, delete-orphan")

    def short_repr(self):
        return {
            'system_id': self.system_id,
        }
