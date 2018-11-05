from sqlalchemy import Column, TIMESTAMP, Index, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import functions as sql_functions

from .base import Base, model_eq


class FeedUpdate(Base):
    __tablename__ = 'feed_updates'

    id = Column(Integer, primary_key=True)
    feed_pri_key = Column(Integer, ForeignKey("feeds.id"))
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
                              onupdate=sql_functions.current_timestamp(),
                              index=True)

    feed = relationship("Feed", back_populates="updates")

    _short_repr_list = ['id', 'status', 'raw_data_hash', 'last_action_time']
    _long_repr_list = ['id', 'status', 'raw_data_hash', 'last_action_time']


Index('feed_updates_ordered_for_feed_idx',
      FeedUpdate.feed_pri_key,
      FeedUpdate.last_action_time)

Index('feed_updates_last_successful_idx',
      FeedUpdate.feed_pri_key,
      FeedUpdate.last_action_time,
      FeedUpdate.status)

