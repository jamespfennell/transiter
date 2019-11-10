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

from .base import Base


class FeedUpdate(Base):
    __tablename__ = "feed_update"

    pk = Column(Integer, primary_key=True)
    feed_pk = Column(Integer, ForeignKey("feed.pk"))

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

    _short_repr_dict = {"id": pk}
    _short_repr_list = [
        status,
        explanation,
        failure_message,
        raw_data_hash,
        content_length,
        last_action_time,
    ]
    _long_repr_dict = _short_repr_dict
    _long_repr_list = _short_repr_list

    def __init__(self, feed, *args, **kwargs):
        self.status = self.Status.SCHEDULED
        super().__init__(*args, **kwargs)
        self.feed = feed
