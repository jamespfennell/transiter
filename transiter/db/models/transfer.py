from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import relationship

from transiter import parse
from .base import Base
from .updatableentity import updatable_from


@updatable_from(parse.Transfer)
class Transfer(Base):
    __tablename__ = "transfer"

    pk = Column(Integer, primary_key=True)
    system_pk = Column(Integer, ForeignKey("system.pk"), index=True)
    source_pk = Column(Integer, ForeignKey("feed_update.pk"), index=True)
    from_stop_pk = Column(Integer, ForeignKey("stop.pk"), index=True)
    to_stop_pk = Column(Integer, ForeignKey("stop.pk"), index=True)

    Type = parse.Transfer.Type

    type = Column(
        Enum(Type, native_enum=False), nullable=False, default=Type.RECOMMENDED
    )
    min_transfer_time = Column(Integer)

    system = relationship("System", cascade="none")
    source = relationship("FeedUpdate", cascade="none")
    from_stop = relationship("Stop", foreign_keys=from_stop_pk, cascade="none")
    to_stop = relationship("Stop", foreign_keys=to_stop_pk, cascade="none")

    @staticmethod
    def from_parsed_transfer(transfer: parse.Transfer) -> "Transfer":
        return Transfer(
            type=transfer.type, min_transfer_time=transfer.min_transfer_time
        )
