from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from transiter import parse
from .base import Base
from .updatableentity import updatable_from


@updatable_from(parse.ScheduledService)
class ScheduledService(Base):
    __tablename__ = "scheduled_service"

    pk = Column(Integer, primary_key=True)
    id = Column(String, nullable=False)
    system_pk = Column(Integer, ForeignKey("system.pk"), index=True)
    source_pk = Column(Integer, ForeignKey("feed_update.pk"), index=True)

    monday = Column(Boolean)
    tuesday = Column(Boolean)
    wednesday = Column(Boolean)
    thursday = Column(Boolean)
    friday = Column(Boolean)
    saturday = Column(Boolean)
    sunday = Column(Boolean)

    source = relationship("FeedUpdate", cascade="none")
    system = relationship("System", back_populates="scheduled_services")
    trips = relationship(
        "ScheduledTrip", back_populates="service", cascade="delete, delete-orphan"
    )

    @staticmethod
    def from_parsed_service(service: parse.ScheduledService) -> "ScheduledService":
        return ScheduledService(
            id=service.id,
            monday=service.monday,
            tuesday=service.tuesday,
            wednesday=service.wednesday,
            thursday=service.thursday,
            friday=service.friday,
            saturday=service.saturday,
            sunday=service.sunday,
        )
