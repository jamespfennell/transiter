from sqlalchemy import (
    Index,
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from transiter import parse
from .base import Base
from .updatableentity import updatable_from


@updatable_from(parse.DirectionRule)
class DirectionRule(Base):
    __tablename__ = "direction_name_rule"

    pk = Column(Integer, primary_key=True)
    id = Column(String)
    stop_pk = Column(Integer, ForeignKey("stop.pk"))
    source_pk = Column(
        Integer, ForeignKey("feed_update.pk"), index=True, nullable=False
    )

    priority = Column(Integer)
    direction_id = Column(Boolean)
    track = Column(String)
    name = Column(String)

    source = relationship("FeedUpdate", cascade="none")
    stop = relationship("Stop", back_populates="direction_rules", cascade="none")

    __table_args__ = (
        Index("direction_name_rule_stop_pk_priority_idx", stop_pk, priority),
        UniqueConstraint(source_pk, id),
    )

    @staticmethod
    def from_parsed_direction_rule(parsed_direction_rule: parse.DirectionRule):
        return DirectionRule(
            id=parsed_direction_rule.id,
            priority=parsed_direction_rule.priority,
            direction_id=parsed_direction_rule.direction_id,
            track=parsed_direction_rule.track,
            name=parsed_direction_rule.name,
        )
