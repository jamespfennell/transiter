import time

from sqlalchemy import Column, TIMESTAMP, Index, Float, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import functions as sql_functions

from .base import Base


class FeedUpdate(Base):
    __tablename__ = 'feed_update'

    pk = Column(Integer, primary_key=True)
    feed_pk = Column(Integer, ForeignKey('feed.pk'))

    status = Column(String)
    explanation = Column(String)
    failure_message = Column(String)
    raw_data_hash = Column(String)
    execution_duration = Column(Float)
    last_action_time = Column(TIMESTAMP(timezone=True),
                              server_default=sql_functions.now(),
                              onupdate=sql_functions.current_timestamp(),
                              index=True)

    feed = relationship(
        'Feed',
        back_populates='updates')

    _short_repr_dict = {'id': 'pk'}
    _short_repr_list = ['status', 'explanation', 'failure_message', 'raw_data_hash', 'last_action_time']
    _long_repr_dict = {'id': 'pk'}
    _long_repr_list = ['status', 'explanation', 'failure_message', 'raw_data_hash', 'last_action_time']

    def __init__(self, feed):
        self.feed = feed
        self.status = 'SCHEDULED'


Index('feed_updates_last_successful_idx',
      FeedUpdate.feed_pk,
      FeedUpdate.last_action_time,
      FeedUpdate.status)
