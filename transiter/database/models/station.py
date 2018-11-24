from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class Station(Base):
    __tablename__ = 'station'

    pk = Column(Integer, primary_key=True)
    system_id = Column(String, ForeignKey('system.id'), index=True)

    borough = Column(String)
    name = Column(String)

    system = relationship(
        'System')
    stops = relationship(
        'Stop')

    _short_repr_list = ['name']
    _short_repr_dict = {'id': 'pk'}

