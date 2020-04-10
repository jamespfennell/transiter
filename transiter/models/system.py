import enum

from sqlalchemy import Column, Integer, String, Enum, Boolean
from sqlalchemy.orm import relationship

from .base import Base, ToDictMixin


class System(ToDictMixin, Base):
    __tablename__ = "system"

    pk = Column(Integer, primary_key=True)
    id = Column(String, unique=True, index=True)

    class SystemStatus(enum.Enum):
        SCHEDULED = 1
        INSTALLING = 2
        ACTIVE = 3
        INSTALL_FAILED = 4
        DELETING = 5

    name = Column(String, nullable=True)
    status = Column(Enum(SystemStatus), nullable=False)
    timezone = Column(String, nullable=True)
    auto_update_enabled = Column(Boolean, nullable=False, server_default="True")

    updates = relationship(
        "SystemUpdate", back_populates="system", cascade="all, delete-orphan"
    )
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

    __dict_columns__ = [id, status, name]
