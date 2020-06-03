import enum

from sqlalchemy import (
    Column,
    UniqueConstraint,
    Enum,
    Integer,
    String,
    Boolean,
    ForeignKey,
    Float,
)
from sqlalchemy.orm import relationship

from .base import Base


class Feed(Base):
    __tablename__ = "feed"

    pk = Column(Integer, primary_key=True)
    id = Column(String)
    system_pk = Column(Integer, ForeignKey("system.pk"))

    class BuiltInParser(enum.Enum):
        GTFS_STATIC = 1
        GTFS_REALTIME = 2

    built_in_parser = Column(Enum(BuiltInParser, native_enum=False))
    custom_parser = Column(String)
    parser_options = Column(String)
    url = Column(String)
    headers = Column(String)
    http_timeout = Column(Float)
    auto_update_enabled = Column(Boolean, nullable=False)
    auto_update_period = Column(Integer)
    required_for_install = Column(Boolean, nullable=False, default=False)

    system = relationship("System", back_populates="feeds")
    updates = relationship(
        "FeedUpdate", back_populates="feed", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("system_pk", "id"),)
