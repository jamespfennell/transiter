from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, Float, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base


class Route(Base):
    __tablename__ = 'routes'

    id = Column(Integer, primary_key=True)
    route_id = Column(String, index=True)
    system_id = Column(String, ForeignKey("systems.system_id"), index=True)
    frequency = Column(Float, nullable=True, default=None)
    running = Column(Boolean, default=False)
    color = Column(String)
    short_name = Column(String)
    long_name = Column(String)
    description = Column(String)
    timetable_url = Column(String)
    last_update_time = Column(TIMESTAMP(timezone=True))

    system = relationship("System",
                          back_populates="routes")
    trips = relationship("Trip",
                         back_populates="route",
                         cascade="all, delete-orphan")
    service_patterns = relationship("ServicePattern",
                                back_populates="route",
                                primaryjoin='ServicePattern.route_pri_key==Route.id',
                                cascade="all, delete-orphan")

    route_statuses = relationship('RouteStatus',
                                  secondary="route_status_routes",
                                  back_populates="routes")

    # NOTE(fennell): need the post_update=True condition on all of these relationships
    # because the service_patterns table has a FK constraint to this table.
    regular_service_pattern_pri_key = Column(Integer, ForeignKey('service_patterns.id'))
    regular_service_pattern = relationship(
        'ServicePattern',
        post_update=True,
        foreign_keys=[regular_service_pattern_pri_key])

    default_service_pattern_pri_key = Column(Integer, ForeignKey('service_patterns.id'))
    default_service_pattern = relationship(
        'ServicePattern',
        post_update=True,
        foreign_keys=[default_service_pattern_pri_key])

    dynamic_service_pattern_pri_key = Column(Integer, ForeignKey('service_patterns.id'))
    dynamic_service_pattern = relationship(
        'ServicePattern',
        post_update=True,
        foreign_keys=[dynamic_service_pattern_pri_key])

    def short_repr(self):
        return {
            'route_id': self.route_id,
        }

    def long_repr(self, verbose=False):
        repr = {
            'route_id': self.route_id,
            'frequency': 'NI', #self.frequency
        }
        #'color': self.color,
        #'long_name': route.long_name,
        #'description': route.description,
        #'timetable_url': route.timetable_url,
        return repr
