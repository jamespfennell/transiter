from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class System(Base):
    __tablename__ = "system"

    pk = Column(Integer, primary_key=True)
    id = Column(String, unique=True, index=True)

    name = Column(String, nullable=True)
    timezone = Column(String, nullable=True)
    raw_config = Column(String)

    routes = relationship(
        "Route", back_populates="system", cascade="all, delete-orphan"
    )
    stops = relationship("Stop", back_populates="system", cascade="all, delete-orphan")
    feeds = relationship("Feed", back_populates="system", cascade="all, delete-orphan")
    scheduled_services = relationship(
        "ScheduledService", back_populates="system", cascade="all, delete-orphan"
    )
    service_map_groups = relationship(
        "ServiceMapGroup", back_populates="system", cascade="all, delete-orphan"
    )

    _short_repr_list = [id, name]
