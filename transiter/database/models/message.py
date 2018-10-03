from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, Float, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base


class Message(Base):
    __tablename__ = "status_messages"

    id = Column(Integer, primary_key=True)
    message_id = Column(String)
    header = Column(String)
    content = Column(String)
    title = Column(String)
    time_posted = Column(String)

    routes = relationship("Route", secondary="status_messages_routes",
        back_populates="status_messages")


route_messages = Table(
    'status_messages_routes', Base.metadata,
    Column('status_message_pri_key', Integer, ForeignKey("status_messages.id")),
    Column('route_pri_key', Integer, ForeignKey("routes.id"))
)