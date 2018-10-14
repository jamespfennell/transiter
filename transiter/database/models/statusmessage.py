from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, Float, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base


class RouteStatus(Base):
    __tablename__ = 'route_status'

    id = Column(Integer, primary_key=True)
    status_id = Column(String)
    status_type = Column(String)
    status_priority = Column(String)
    message_title = Column(String)
    message_content = Column(String)
    start_time = Column(TIMESTAMP(timezone=True))
    end_time = Column(TIMESTAMP(timezone=True))
    creation_time = Column(TIMESTAMP(timezone=True))

    routes = relationship("Route", secondary="route_status_routes")


route_status_routes = Table(
    'route_status_routes', Base.metadata,
    Column('route_status_pri_key', Integer, ForeignKey("route_status.id")),
    Column('route_pri_key', Integer, ForeignKey("routes.id"))
)


class StatusMessage(Base):
    __tablename__ = "status_messages"

    id = Column(Integer, primary_key=True)
    message_id = Column(String)
    message = Column(String)
    # TODO convert to timestamp field
    time_posted = Column(String)
    message_type = Column(String)
    priority = Column(Integer)


    routes = relationship("Route", secondary="status_messages_routes")
    #    back_populates="status_messages")

    def short_repr(self):
        return {
            'type': self.message_type,
            'content': self.message,
            'time_posted': self.time_posted
        }


status_messages_routes = Table(
    'status_messages_routes', Base.metadata,
    Column('status_message_pri_key', Integer, ForeignKey("status_messages.id")),
    Column('route_pri_key', Integer, ForeignKey("routes.id"))
)