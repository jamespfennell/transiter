from sqlalchemy import (
    Column,
    Enum,
    TIMESTAMP,
    Integer,
    String,
    Float,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from transiter import parse
from .base import Base
from .updatableentity import updatable_from


@updatable_from(parse.Vehicle)
class Vehicle(Base):
    __tablename__ = "vehicle"

    pk = Column(Integer, primary_key=True)
    id = Column(String)
    source_pk = Column(
        Integer, ForeignKey("feed_update.pk"), index=True, nullable=False
    )
    system_pk = Column(Integer, ForeignKey("system.pk"), nullable=False, index=True)
    trip_pk = Column(Integer, ForeignKey("trip.pk"), index=True, unique=True)

    Status = parse.Vehicle.Status
    CongestionLevel = parse.Vehicle.CongestionLevel
    OccupancyStatus = parse.Vehicle.OccupancyStatus

    current_stop_sequence = Column(Integer)
    current_stop_pk = Column(
        Integer, ForeignKey("stop.pk")
    )  # TODO: how can delete stops now?
    label = Column(String)
    license_plate = Column(String)
    current_status = Column(
        Enum(Status, native_enum=False), nullable=False, default=Status.IN_TRANSIT_TO
    )
    latitude = Column(Float)
    longitude = Column(Float)
    bearing = Column(Float)
    odometer = Column(Float)
    speed = Column(Float)
    congestion_level = Column(
        Enum(CongestionLevel, native_enum=False),
        nullable=False,
        default=CongestionLevel.UNKNOWN_CONGESTION_LEVEL,
    )
    occupancy_status = Column(
        Enum(OccupancyStatus, native_enum=False),
        nullable=False,
        default=OccupancyStatus.UNKNOWN,
    )
    updated_at = Column(TIMESTAMP(timezone=True))

    source = relationship("FeedUpdate", cascade="none")
    system = relationship("System", back_populates="vehicles", cascade="none")
    trip = relationship("Trip", back_populates="vehicle", cascade="none", lazy="joined")
    current_stop = relationship("Stop", cascade="none")

    __table_args__ = (UniqueConstraint(system_pk, id),)

    @staticmethod
    def from_parsed_vehicle(vehicle: parse.Vehicle) -> "Vehicle":
        return Vehicle(
            id=vehicle.id,
            label=vehicle.label,
            license_plate=vehicle.license_plate,
            current_stop_sequence=vehicle.current_stop_sequence,
            current_status=vehicle.current_status,
            latitude=vehicle.latitude,
            longitude=vehicle.longitude,
            bearing=vehicle.bearing,
            odometer=vehicle.odometer,
            speed=vehicle.speed,
            congestion_level=vehicle.congestion_level,
            occupancy_status=vehicle.occupancy_status,
            updated_at=vehicle.updated_at,
        )
