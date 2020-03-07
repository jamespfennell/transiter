import enum

from sqlalchemy import (
    Column,
    TIMESTAMP,
    Index,
    Float,
    Enum,
    Integer,
    String,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import functions as sql_functions

from .base import Base, ToDictMixin


class FeedUpdate(ToDictMixin, Base):
    __tablename__ = "feed_update"

    pk = Column(Integer, primary_key=True)
    feed_pk = Column(Integer, ForeignKey("feed.pk"))

    class Type(enum.Enum):
        REGULAR = 1
        FLUSH = 2

    class Status(enum.Enum):
        SCHEDULED = 1
        IN_PROGRESS = 2
        SUCCESS = 3
        FAILURE = 4

    class Explanation(enum.Enum):
        UPDATED = 1
        NOT_NEEDED = 2
        PARSE_ERROR = 3
        DOWNLOAD_ERROR = 4
        INVALID_PARSER = 5
        EMPTY_FEED = 6
        SYNC_ERROR = 7
        UNEXPECTED_ERROR = 8

    update_type = Column(
        Enum(Type, name="update_type"), nullable=False, default=Type.REGULAR
    )
    status = Column(Enum(Status))
    explanation = Column(Enum(Explanation))
    failure_message = Column(String)
    raw_data_hash = Column(String)
    content_length = Column(Integer)
    execution_duration = Column(Float)
    last_action_time = Column(
        TIMESTAMP(timezone=True),
        server_default=sql_functions.now(),
        onupdate=sql_functions.current_timestamp(),
        index=True,
    )
    feed_time = Column(TIMESTAMP(timezone=True))

    feed = relationship("Feed", back_populates="updates")

    __table_args__ = (
        Index("feed_updates_last_successful_idx", feed_pk, last_action_time, status),
    )

    __dict_columns__ = [
        update_type,
        status,
        explanation,
        failure_message,
        raw_data_hash,
        content_length,
        last_action_time,
    ]

    def to_dict(self) -> dict:
        return {"id": self.pk, **self._to_dict(self.__dict_columns__)}
