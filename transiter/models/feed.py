import enum

from sqlalchemy import (
    Column,
    UniqueConstraint,
    Enum,
    Integer,
    String,
    Boolean,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from .base import Base


class Feed(Base):
    __tablename__ = "feed"

    pk = Column(Integer, primary_key=True)
    id = Column(String)
    system_id = Column(String, ForeignKey("system.id"))

    class BuiltInParser(enum.Enum):
        GTFS_STATIC = 1
        GTFS_REALTIME = 2

    built_in_parser = Column(Enum(BuiltInParser))
    custom_parser = Column(String)
    url = Column(String)
    headers = Column(String)
    auto_update_on = Column(Boolean)
    auto_update_period = Column(Integer)

    system = relationship("System", back_populates="feeds")
    updates = relationship(
        "FeedUpdate", back_populates="feed", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("system_id", "id"),)

    _short_repr_list = [id]
