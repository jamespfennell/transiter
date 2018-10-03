from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, Float, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base

class StatusMessage(Base):
    __tablename__ = "status_messages"

    id = Column(Integer, primary_key=True)
    message_id = Column(String)
    message = Column(String)
    time_posted = Column(String)
    message_type = Column(String)
    priority = Column(Integer)


    routes = relationship("Route", secondary="status_messages_routes")
    #    back_populates="status_messages")

    def repr_for_list(self):
        return {
            'type': self.message_type,
            'content': self.message
        }


status_messages_routes = Table(
    'status_messages_routes', Base.metadata,
    Column('status_message_pri_key', Integer, ForeignKey("status_messages.id")),
    Column('route_pri_key', Integer, ForeignKey("routes.id"))
)