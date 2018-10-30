from sqlalchemy import Column, Integer, String, UniqueConstraint, ForeignKey, Numeric, ForeignKeyConstraint
from sqlalchemy.orm import relationship

from .base import Base


class StopAlias(Base):
    __tablename__ = 'stop_alias'

    pk = Column(Integer, primary_key=True)
    system_id = Column(String)
    stop_id = Column(String)
    stop_id_alias = Column(String)

    stop = relationship("Stop")


    __table_args__ = (
        ForeignKeyConstraint(
            ('system_id', 'stop_id'),
            ('stops.system_id', 'stops.stop_id')),
        UniqueConstraint('system_id', 'stop_id_alias')
    )
