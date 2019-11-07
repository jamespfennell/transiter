from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base
from .updatableentity import UpdatableEntity


class Route(Base, UpdatableEntity):
    __tablename__ = "route"

    pk = Column(Integer, primary_key=True)
    id = Column(String, index=True)
    system_id = Column(String, ForeignKey("system.id"), index=True)
    source_pk = Column(Integer, ForeignKey("feed_update.pk"), index=True)

    color = Column(String)
    short_name = Column(String)
    long_name = Column(String)
    description = Column(String)
    url = Column(String)

    system = relationship("System", back_populates="routes")
    source = relationship("FeedUpdate", cascade="none")
    trips = relationship("Trip", back_populates="route", cascade="all, delete-orphan")
    service_maps = relationship(
        "ServiceMap",
        back_populates="route",
        primaryjoin="ServiceMap.route_pk==Route.pk",
        cascade="all, delete-orphan",
    )
    route_statuses = relationship(
        "Alert", secondary="alert_route", back_populates="routes", cascade="all"
    )

    _short_repr_list = [id, color]
    _long_repr_list = [id, short_name, long_name, color, description, url]
