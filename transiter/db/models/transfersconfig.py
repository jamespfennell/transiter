from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Table,
    Numeric,
)
from sqlalchemy.orm import relationship

from .base import Base


class TransfersConfig(Base):
    __tablename__ = "transfers_config"

    pk = Column(Integer, primary_key=True)

    distance = Column(Numeric, nullable=False)

    systems = relationship(
        "System",
        back_populates="transfers_configs",
        secondary="transfers_config_system",
        cascade="none",
    )
    transfers = relationship(
        "Transfer",
        back_populates="config_source",
        cascade="all, delete-orphan",
        order_by="Transfer.distance",
    )

    @property
    def id(self):
        return str(self.pk) if self.pk is not None else None


transfers_config_system = Table(
    "transfers_config_system",
    Base.metadata,
    Column(
        "transfers_config_pk", Integer, ForeignKey("transfers_config.pk"), index=True
    ),
    Column("system_pk", Integer, ForeignKey("system.pk"), index=True),
)
