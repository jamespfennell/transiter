from sqlalchemy import Column, Float, UniqueConstraint, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class ServiceMapGroup(Base):
    __tablename__='service_map_group'

    pk = Column(Integer, primary_key=True)
    id = Column(String, nullable=False)
    system_pk = Column(Integer, ForeignKey('system.pk'), nullable=False)

    source = Column(String, nullable=False)
    conditions = Column(String)
    # TODO: add defaults to all of these: 0, False, False
    threshold = Column(Float, nullable=False)
    use_for_routes_at_stop = Column(Boolean, nullable=False)
    use_for_stops_in_route = Column(Boolean, nullable=False)

    maps = relationship(
        'ServicePattern',
        cascade='all, delete-orphan',
        back_populates='group',
    )
    system = relationship(
        'System',
        cascade='',
        back_populates='service_map_groups'
    )
