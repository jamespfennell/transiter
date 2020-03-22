import datetime
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

    class Result(enum.Enum):
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
    result = Column(Enum(Result, native_enum=False))
    result_message = Column(String)
    content_hash = Column(String)
    content_length = Column(Integer)
    content_created_at = Column(TIMESTAMP(timezone=True))
    download_duration = Column(Float)
    total_duration = Column(Float)
    scheduled_at = Column(TIMESTAMP(timezone=True), default=datetime.datetime.utcnow)
    completed_at = Column(TIMESTAMP(timezone=True))
    num_parsed_entities = Column(Integer)
    num_added_entities = Column(Integer)
    num_updated_entities = Column(Integer)
    num_deleted_entities = Column(Integer)

    feed = relationship("Feed", back_populates="updates")

    __table_args__ = (
        Index(
            "feed_update_success_pk_completed_at_idx",
            feed_pk,
            completed_at,
            postgresql_where=(status == Status.SUCCESS),
        ),
        Index("feed_update_feed_pk_feed_update_pk_idx", feed_pk, pk),
    )

    __dict_columns__ = [
        update_type,
        status,
        result,
        result_message,
        content_hash,
        content_length,
    ]

    def to_dict(self) -> dict:
        return {"id": self.pk, **self._to_dict(self.__dict_columns__)}
