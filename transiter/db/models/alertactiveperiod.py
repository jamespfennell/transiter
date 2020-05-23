from sqlalchemy import (
    Column,
    TIMESTAMP,
    Integer,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from transiter import parse
from .base import Base


class AlertActivePeriod(Base):
    __tablename__ = "alert_active_period"

    pk = Column(Integer, primary_key=True)
    alert_pk = Column(Integer, ForeignKey("alert.pk"), index=True, nullable=False)

    starts_at = Column(TIMESTAMP(timezone=True),)
    ends_at = Column(TIMESTAMP(timezone=True))

    alert = relationship("Alert", back_populates="active_periods", cascade="none")

    @staticmethod
    def from_parsed_active_period(
        active_period: parse.AlertActivePeriod,
    ) -> "AlertActivePeriod":
        return AlertActivePeriod(
            starts_at=active_period.starts_at, ends_at=active_period.ends_at
        )
