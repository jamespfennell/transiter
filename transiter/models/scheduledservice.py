from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class ScheduledService(Base):
    __tablename__ = "scheduled_service"

    pk = Column(Integer, primary_key=True)
    id = Column(String, nullable=False)
    system_pk = Column(Integer, ForeignKey("system.pk"), index=True, nullable=False)

    monday = Column(Boolean)
    tuesday = Column(Boolean)
    wednesday = Column(Boolean)
    thursday = Column(Boolean)
    friday = Column(Boolean)
    saturday = Column(Boolean)
    sunday = Column(Boolean)

    system = relationship("System", back_populates="scheduled_services", cascade="")
    trips = relationship(
        "ScheduledTrip", back_populates="service", cascade="all, delete-orphan"
    )
