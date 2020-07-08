from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    Date,
    UniqueConstraint,
)
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
    source_pk = Column(
        Integer, ForeignKey("feed_update.pk"), index=True, nullable=False
    )

    monday = Column(Boolean)
    tuesday = Column(Boolean)
    wednesday = Column(Boolean)
    thursday = Column(Boolean)
    friday = Column(Boolean)
    saturday = Column(Boolean)
    sunday = Column(Boolean)
    start_date = Column(Date)
    end_date = Column(Date)

    source = relationship("FeedUpdate", cascade="none")
    system = relationship("System", back_populates="scheduled_services")
    trips = relationship(
        "ScheduledTrip", back_populates="service", cascade="delete, delete-orphan"
    )
    additions = relationship("ScheduledServiceAddition", cascade="all, delete-orphan")
    removals = relationship("ScheduledServiceRemoval", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint(system_pk, id),)

    @staticmethod
    def from_parsed_service(service: parse.ScheduledService) -> "ScheduledService":
        # PyCharm doesn't realize the addition and removal relationships are one to
        # many and so complains about the list assignments.
        # noinspection PyTypeChecker
        return ScheduledService(
            id=service.id,
            monday=service.monday,
            tuesday=service.tuesday,
            wednesday=service.wednesday,
            thursday=service.thursday,
            friday=service.friday,
            saturday=service.saturday,
            sunday=service.sunday,
            start_date=service.start_date,
            end_date=service.end_date,
            additions=[
                ScheduledServiceAddition(date=added_date)
                for added_date in service.added_dates
            ],
            removals=[
                ScheduledServiceRemoval(date=removed_date)
                for removed_date in service.removed_dates
            ],
        )


class ScheduledServiceAddition(Base):
    __tablename__ = "scheduled_service_addition"

    pk = Column(Integer, primary_key=True)
    service_pk = Column(Integer, ForeignKey("scheduled_service.pk"), index=True)

    date = Column(Date, nullable=False)


class ScheduledServiceRemoval(Base):
    __tablename__ = "scheduled_service_removal"

    pk = Column(Integer, primary_key=True)
    service_pk = Column(Integer, ForeignKey("scheduled_service.pk"), index=True)

    date = Column(Date, nullable=False)
