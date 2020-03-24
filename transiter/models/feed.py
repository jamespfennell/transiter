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

from .base import Base, ToDictMixin


class Feed(ToDictMixin, Base):
    __tablename__ = "feed"

    pk = Column(Integer, primary_key=True)
    id = Column(String)
    system_pk = Column(Integer, ForeignKey("system.pk"))

    class BuiltInParser(enum.Enum):
        GTFS_STATIC = 1
        GTFS_REALTIME = 2

    built_in_parser = Column(Enum(BuiltInParser))
    custom_parser = Column(String)
    url = Column(String)
    headers = Column(String)
    auto_update_enabled = Column(Boolean, nullable=False)
    auto_update_period = Column(Integer)

    system = relationship("System", back_populates="feeds")
    updates = relationship(
        "FeedUpdate", back_populates="feed", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("system_pk", "id"),)

    __dict_columns__ = [id]
