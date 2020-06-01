import datetime
import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Enum,
    TIMESTAMP,
    ForeignKey,
    Index,
    Float,
)
from sqlalchemy.orm import relationship

from .base import Base


class SystemUpdate(Base):
    __tablename__ = "system_update"

    pk = Column(Integer, primary_key=True)
    system_pk = Column(Integer, ForeignKey("system.pk"))

    class Status(enum.Enum):
        SCHEDULED = 1
        IN_PROGRESS = 2
        SUCCESS = 3
        FAILED = 4

    status = Column(Enum(Status, native_enum=False), nullable=False)
    status_message = Column(String)  # TODO: rename stack trace?
    total_duration = Column(Float)
    scheduled_at = Column(TIMESTAMP(timezone=True), default=datetime.datetime.utcnow)
    completed_at = Column(TIMESTAMP(timezone=True))
    config = Column(String)
    config_template = Column(String)
    config_parameters = Column(String)
    config_source_url = Column(String)
    transiter_version = Column(String)

    system = relationship("System", back_populates="updates")

    __table_args__ = (
        Index("system_update_system_pk_system_update_pk_idx", system_pk, pk),
    )
