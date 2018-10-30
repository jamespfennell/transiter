from sqlalchemy import Index, Column, TIMESTAMP, Table, Integer, String, Float, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base

#TODO allow route to feature in the direction name rule

class DirectionNameRule(Base):
    __tablename__ = 'direction_name_rule'

    pk = Column(Integer, primary_key=True)
    # Should be not null
    stop_pk = Column(Integer, ForeignKey("stops.id"))
    priority = Column(Integer)
    direction_id = Column(Boolean)
    track = Column(String)
    stop_id_alias = Column(String)
    name = Column(String)

    stop = relationship("Stop", back_populates="direction_name_rules")


Index('direction_name_rule_stop_pk_priority_idx',
      DirectionNameRule.stop_pk,
      DirectionNameRule.priority)

