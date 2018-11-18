from sqlalchemy import Column, Integer, String, Index, UniqueConstraint, ForeignKeyConstraint
from sqlalchemy.orm import relationship

from .base import Base


# TODO: should this be StopIdAlias? I think so

class StopIdAlias(Base):
    __tablename__ = 'stop_id_alias'

    pk = Column(Integer, primary_key=True)
    system_id = Column(String)
    stop_id = Column(String)
    stop_id_alias = Column(String)

    stop = relationship(
        'Stop',
        back_populates='stop_id_aliases')

    __table_args__ = (
        ForeignKeyConstraint(
            ('system_id', 'stop_id'),
            ('stop.system_id', 'stop.id')),
        UniqueConstraint('system_id', 'stop_id_alias')
    )

