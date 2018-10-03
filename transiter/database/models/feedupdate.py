from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, Float, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from sqlalchemy.sql import functions as sql_functions
from .base import Base


class FeedUpdate(Base):
    __tablename__ = 'feed_updates'

    id = Column(Integer, primary_key=True)
    feed_pri_key = Column(Integer, ForeignKey("feeds.id"), index=True)
    status = Column(String)
    # SCHEDULED,
    # IN_PROGRESS,
    # SUCCESS_UPDATED,
    # SUCCESS_NOT_NEEDED,
    # FAILURE_COULD_NOT_PARSE,
    # FAILURE_COULD_NOT_DOWNLOAD,
    # FAILURE_EMPTY_FEED
    failure_message = Column(String)
    raw_data_hash = Column(String)
    time = Column(TIMESTAMP(timezone=True))
    last_action_time = Column(TIMESTAMP(timezone=True),
                              server_default=sql_functions.now(),
                              onupdate=sql_functions.current_timestamp())

    feed = relationship("Feed", back_populates="updates")