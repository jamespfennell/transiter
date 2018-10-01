from sqlalchemy import Column, TIMESTAMP, Table, Integer, String, Float, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import functions as sql_functions
Base = declarative_base()

# TODO: put in UniqueConstraint on stop_ids

status_messages_routes = Table(
    'status_messages_routes', Base.metadata,
    Column('status_message_pri_key', Integer, ForeignKey("status_messages.id")),
    Column('route_pri_key', Integer, ForeignKey("routes.id"))
)

class System(Base):
    __tablename__ = 'systems'

    id = Column(Integer, primary_key=True)
    system_id = Column(String, unique=True)
    name = Column(String, nullable=True)
    directory_hash = Column(String, nullable=True)

    routes = relationship("Route", back_populates="system",
        cascade="all, delete-orphan")
    stations = relationship("Station", back_populates="system",
        cascade="all, delete-orphan")
    feeds = relationship("Feed", back_populates="system",
        cascade="all, delete-orphan")

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

    system = relationship("System", back_populates="routes")
    trips = relationship("Trip", back_populates="route",
                                cascade="all, delete-orphan")
    list_entries = relationship("RouteListEntry", back_populates="route",
        order_by="RouteListEntry.position", cascade="all, delete-orphan")

    status_messages = relationship("StatusMessage", secondary="status_messages_routes",
        back_populates="routes")

    def __repr__(self):
        return 'Route {}'.format(self.route_id)

class Stop(Base):
    __tablename__ = 'stops'

    id = Column(Integer, primary_key=True)
    stop_id = Column(String, index=True)
    station_pri_key = Column(Integer, ForeignKey("stations.id"), index=True)
    system_id = Column(String, ForeignKey("systems.system_id"), index=True)
    name = Column(String)
    longitude = Column(Numeric(precision=9, scale=6))
    lattitude = Column(Numeric(precision=9, scale=6))

    system = relationship("System")
    station = relationship("Station", back_populates="stops")
    direction_names = relationship("DirectionName", back_populates="stop",
                                   cascade="all, delete-orphan")
    stop_events = relationship("StopEvent", back_populates="stop",
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

class Feed(Base):
    __tablename__ = 'feeds'
    id = Column(Integer, primary_key=True)
    system_id = Column(String, ForeignKey("systems.system_id"), index=True)
    feed_id = Column(String, index=True)
    url = Column(String)
    parser_module = Column(String)
    parser_function = Column(String)
    auto_updater_enabled = Column(Boolean)
    auto_updater_frequency = Column(Integer)
    # last_update_pri_key = Column(Integer, ForeignKey("feed_updates.id"))
    # TODO: or just run another sql query and get the most recent
    system = relationship("System", back_populates="feeds")
    updates = relationship("FeedUpdate", back_populates="feed", cascade="all, delete-orphan")


class FeedUpdate(Base):
    __tablename__ = 'feed_updates'

    id = Column(Integer, primary_key=True)
    feed_pri_key = Column(Integer, ForeignKey("feeds.id"), index=True)
    status = Column(String)
    # SCHEDULED,
    # IN_PROGRESS,
    # SUCCESS_UPDATED,
    # SUCCESS_NOT_NEEDED,
    # FAILURE_COULD_NOT_PARSE,
    # FAILURE_COULD_NOT_DOWNLOAD,
    # FAILURE_EMPTY_FEED
    failure_message = Column(String)
    raw_data_hash = Column(String)
    time = Column(TIMESTAMP(timezone=True))
    last_action_time = Column(TIMESTAMP(timezone=True),
                              server_default=sql_functions.now(),
                              onupdate=sql_functions.current_timestamp())

    feed = relationship("Feed", back_populates="updates")


class StatusMessage(Base):
    __tablename__ = "status_messages"

    id = Column(Integer, primary_key=True)
    message_id = Column(String)
    message = Column(String)
    time_posted = Column(String)
    message_type = Column(String)


    routes = relationship("Route", secondary="status_messages_routes",
        back_populates="status_messages")


"""

Need to make this less NYC subway specific
class TerminusAbbr(Base):
    __tablename__ = "terminus_abbrs"

    id = Column(Integer, primary_key=True)
    abbreviation = Column(String)
    stop_id = Column(String, ForeignKey("stops.stop_id"), nullable=False, index=True)
"""

class Trip(Base):
    __tablename__ = 'trips'

    id = Column(Integer, primary_key=True)
    trip_id = Column(String, unique=True, index=True)
    route_pri_key = Column(Integer, ForeignKey("routes.id"))
    direction = Column(String)
    start_time = Column(TIMESTAMP(timezone=True))
    is_assigned = Column(Boolean)
    train_id = Column(String)
    last_update_time = Column(TIMESTAMP(timezone=True))
    current_status = Column(String)
    current_stop_sequence = Column(Integer)

    route = relationship("Route", back_populates="trips")
    stop_events = relationship("StopEvent", back_populates="trip")

class StopEvent(Base):
    __tablename__ = 'stop_events'

    id = Column(Integer, primary_key=True)
    stop_pri_key = Column(Integer, ForeignKey('stops.id'))
    trip_pri_key = Column(Integer, ForeignKey('trips.id'))
    future = Column(Boolean)
    arrival_time = Column(TIMESTAMP(timezone=True))
    departure_time = Column(TIMESTAMP(timezone=True))
    last_update_time = Column(TIMESTAMP(timezone=True))
    sequence_index = Column(Integer)
    scheduled_track = Column(String)
    actual_track = Column(String)

    stop = relationship("Stop", back_populates="stop_events")
    trip = relationship("Trip", back_populates="stop_events")
