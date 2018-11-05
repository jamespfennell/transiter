from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, Float, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base, model_eq


class Feed(Base):
    __tablename__ = 'feeds'
    id = Column(Integer, primary_key=True)
    system_id = Column(String, ForeignKey("systems.system_id"), index=True)
    feed_id = Column(String, index=True)
    url = Column(String)
    parser_module = Column(String)
    parser_function = Column(String)
    auto_updater_enabled = Column(Boolean)
    auto_updater_frequency = Column(Integer)
    # last_update_pri_key = Column(Integer, ForeignKey("feed_updates.id"))
    # TODO: or just run another sql query and get the most recent
    system = relationship("System", back_populates="feeds")
    updates = relationship("FeedUpdate", back_populates="feed", cascade="all, delete-orphan")

    _short_repr_list = ['feed_id']

