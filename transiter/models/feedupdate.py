from sqlalchemy import Column, TIMESTAMP, Index, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import functions as sql_functions

from .base import Base


class FeedUpdate(Base):
    __tablename__ = 'feed_update'

    pk = Column(Integer, primary_key=True)
    feed_pk = Column(Integer, ForeignKey('feed.pk'))

    status = Column(String)
    explanation = Column(String)
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

    feed = relationship(
        'Feed',
        back_populates='updates')

    _short_repr_dict = {'id': 'pk'}
    _short_repr_list = ['status', 'explanation', 'raw_data_hash', 'last_action_time']
    _long_repr_dict = {'id': 'pk'}
    _long_repr_list = ['status', 'explanation', 'raw_data_hash', 'last_action_time']


Index('feed_updates_last_successful_idx',
      FeedUpdate.feed_pk,
      FeedUpdate.last_action_time,
      FeedUpdate.status)
