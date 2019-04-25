from sqlalchemy import Column, UniqueConstraint, Enum, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base
import enum


# NOTE: if the table was foreign keyed to system though system.pk instead,
# wouldn't need to give the task service system info
class Feed(Base):
    __tablename__ = 'feed'

    pk = Column(Integer, primary_key=True)
    id = Column(String)
    system_id = Column(String, ForeignKey('system.id'))

    url = Column(String)

    class BuiltInParser(enum.Enum):
        GTFS_STATIC = 1
        GTFS_REALTIME = 2

    built_in_parser = Column(Enum(BuiltInParser))
    custom_parser = Column(String)

    # TODO: nuke these three
    parser = Column(String)
    custom_module = Column(String)
    custom_function = Column(String)


    # TODO: rename auto_update
    auto_updater_enabled = Column(Boolean)
    # TODO: rename auto_update_period
    auto_updater_frequency = Column(Integer)

    system = relationship(
        'System',
        back_populates='feeds')
    updates = relationship(
        'FeedUpdate',
        back_populates='feed',
        cascade='all, delete-orphan')

    __table_args__ = (UniqueConstraint('system_id', 'id'),)

    _short_repr_list = ['id']
