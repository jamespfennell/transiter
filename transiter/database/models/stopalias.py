from sqlalchemy import Column, Integer, String, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base


class StopAlias(Base):
    __tablename__ = 'stop_alias'

    id = Column(Integer, primary_key=True)
    stop_id = Column(String, ForeignKey("stops.stop_id"))
    system_id = Column(String, ForeignKey("systems.system_id"))
    stop_id_alias = Column(String, index=True)

    # Need a two column index on (stop_id, system_id)
