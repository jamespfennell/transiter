from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, Float, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base


class ServicePatternEntry(Base):
    pass
    """

    id = Column(Integer, primary_key=True)
    service_pattern_pri_key
    stop_pri_key
    position =
    """
