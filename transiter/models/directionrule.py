from sqlalchemy import Index, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base
from .updatableentity import updatable_entity


@updatable_entity
class DirectionRule(Base):
    __tablename__ = "direction_name_rule"

    pk = Column(Integer, primary_key=True)
    id = Column(String)
    stop_pk = Column(Integer, ForeignKey("stop.pk"))
    source_pk = Column(Integer, ForeignKey("feed_update.pk"), index=True)

    priority = Column(Integer)
    direction_id = Column(Boolean)
    track = Column(String)
    name = Column(String)

    stop_id = None

    source = relationship("FeedUpdate", cascade="none")
    stop = relationship("Stop", back_populates="direction_rules", cascade="none")

    __table_args__ = (
        Index("direction_name_rule_stop_pk_priority_idx", stop_pk, priority),
    )
