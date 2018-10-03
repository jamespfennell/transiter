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
    list_entries = relationship("RouteListEntry",
                                back_populates="route",
                                order_by="RouteListEntry.position",
                                cascade="all, delete-orphan")
    status_messages = relationship("StatusMessage", secondary="status_messages_routes",
        back_populates="routes")

    def repr_for_list(self):
        return {
            'route_id': self.route_id,
            'href': 'NI'
        }

    def repr_for_get(self, verbose=False):
        repr = {
            'route_id': self.route_id,
            'frequency': 'NI', #self.frequency
        }
        #'color': self.color,
        #'long_name': route.long_name,
        #'description': route.description,
        #'timetable_url': route.timetable_url,
        return repr
