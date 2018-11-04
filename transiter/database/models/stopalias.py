from sqlalchemy import Column, Integer, String, UniqueConstraint, ForeignKey, Numeric, ForeignKeyConstraint
from sqlalchemy.orm import relationship

from .base import Base, model_eq

# TODO: should this be StopIdAlias? I think so

class StopAlias(Base):
    __tablename__ = 'stop_alias'

    pk = Column(Integer, primary_key=True)
    system_id = Column(String)
    stop_id = Column(String)
    stop_id_alias = Column(String)

    stop = relationship("Stop", back_populates="stop_aliases")


    __table_args__ = (
        ForeignKeyConstraint(
            ('system_id', 'stop_id'),
            ('stops.system_id', 'stops.stop_id')),
        UniqueConstraint('system_id', 'stop_id_alias')
    )


    def __eq__(self, other):
        return model_eq(self, other)
