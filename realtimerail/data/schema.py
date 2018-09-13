from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# TODO: put in UniqueConstraint on stop_ids

class System(Base):
    __tablename__ = 'systems'

    id = Column(Integer, primary_key=True)
    system_id = Column(String, unique=True)
    name = Column(String, nullable=True)
    directory_hash = Column(String, nullable=True)

    routes = relationship("Route", back_populates="system", cascade="all, delete-orphan")
    stations = relationship("Station", back_populates="system", cascade="all, delete-orphan")

class Route(Base):
    __tablename__ = 'routes'

    id = Column(Integer, primary_key=True)
    route_id = Column(String, index=True)
    system_pri_key = Column(Integer, ForeignKey("systems.id"), index=True)
    frequency = Column(Float, nullable=True, default=None)
    running = Column(Boolean, default=False)
    color = Column(String)
    short_name = Column(String)
    long_name = Column(String)
    description = Column(String)
    timetable_url = Column(String)

    system = relationship("System", back_populates="routes")
    list_entries = relationship("RouteListEntry", back_populates="route",
        order_by="RouteListEntry.position", cascade="all, delete-orphan")

    def __repr__(self):
        return 'Route {}'.format(route_id)

class Stop(Base):
    __tablename__ = 'stops'

    id = Column(Integer, primary_key=True)
    stop_id = Column(String, index=True)
    station_pri_key = Column(Integer, ForeignKey("stations.id"), index=True)
    name = Column(String)
    longitude = Column(Numeric(precision=9, scale=6))
    lattitude = Column(Numeric(precision=9, scale=6))

    station = relationship("Station", back_populates="stops")
    direction_names = relationship("DirectionName", back_populates="stop",
        cascade="all, delete-orphan")

class Station(Base):
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True)
    borough = Column(String)
    name = Column(String)
    system_id = Column(Integer, ForeignKey("systems.id"), index=True)

    system = relationship("System", back_populates="stations")
    stops = relationship("Stop", back_populates="station", cascade="all, delete-orphan")

class DirectionName(Base):
    __tablename__ = 'direction_names'

    id = Column(Integer, primary_key=True)
    stop_pri_key = Column(Integer, ForeignKey("stops.id"), index=True)
    direction = Column(String)
    name = Column(String)
    track = Column(String)

    stop = relationship("Stop", back_populates="direction_names")

class RouteListEntry(Base):
    __tablename__ = 'route_list_entries'

    id = Column(Integer, primary_key=True)
    stop_pri_key = Column(Integer, ForeignKey("stops.id"), index=True)
    route_pri_key = Column(Integer, ForeignKey("routes.id"), index=True)
    position = Column(Integer)

    stop = relationship("Stop") #, back_populates="direction_names")
    route = relationship("Route", back_populates="list_entries")

"""
class ServiceAdvisory(Base):
    __tablename__ = "service_advisories"

    id = Column(Integer, primary_key=True)
    message = Column(String)
    time_posted = Column(String)
    message_type = Column(String)

# is this really how we are doing this many-to-many relationship?
class RouteServiceAdvisory(Base):
    __tablename__ = "route_service_advisories"

    id = Column(Integer, primary_key=True)
    service_advisory_message = Column(Integer, ForeignKey("service_advisories.id"))
    route_id = Column(String, ForeignKey("routes.route_id"))
class TerminusAbbr(Base):
    __tablename__ = "terminus_abbrs"

    id = Column(Integer, primary_key=True)
    abbreviation = Column(String)
    stop_id = Column(String, ForeignKey("stops.stop_id"), nullable=False, index=True)

class ServiceEntry(Base):
    __tablename__ = 'regular_service_entries'

    id = Column(Integer, primary_key=True)
    stop_id = Column(String, ForeignKey("stops.stop_id"), nullable=False, index=True)
    route_id = Column(String, ForeignKey("routes.route_id"), nullable=False, index=True)
    sequence_index = Column(Integer) #Index for when sorting it?
    kind = Column(String) # Enum with Day, Night, Weekend?

class Trips(Base):
    __tablename__ = 'trips'

    id = Column(Integer, primary_key=True)
    trip_id = Column(String, unique=True)
    route_id = Column(String, ForeignKey("routes.route_id"))
    direction = Column(String)
    start_time = Column(String)
    is_assigned = Column(Boolean)
    train_id = Column(String)
    update_time = Column(String)
    current_status = Column(Integer)
    current_stop_sequence = Column(Integer)


class StopEvent(Base):
    __tablename__ = 'stop_events'

    id = Column(Integer, primary_key=True)
    stop_id = Column(String, ForeignKey('stops.stop_id'))
    trip_id = Column(String, ForeignKey('trips.trip_id'))
    future = Column(Boolean)
    arrival_time = Column(Integer)
    departure_time = Column(Integer)
    update_time = Column(Integer)
    sequence_index = Column(Integer)
    scheduled_track = Column(String)
    actual_track = Column(String)
"""
