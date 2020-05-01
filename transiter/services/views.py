import dataclasses
import datetime
import enum
import typing

from transiter import models


class NULL:
    pass


class View:
    def to_dict(self):
        return {
            key: getattr(self, key)
            for key in self.__dataclass_fields__.keys()
            if key[0] != "_" and getattr(self, key) is not NULL
        }


@dataclasses.dataclass
class System(View):
    id: str
    status: models.System.SystemStatus
    name: str

    @classmethod
    def from_model(cls, system: models.System):
        return cls(id=system.id, status=system.status, name=system.name)


@dataclasses.dataclass
class _EntitiesInSystem(View):
    count: int
    _system_id: str

    @classmethod
    def from_model(cls, system: models.System, count):
        return cls(count=count, _system_id=system.id)


class RoutesInSystem(_EntitiesInSystem):
    pass


class StopsInSystem(_EntitiesInSystem):
    pass


class FeedsInSystem(_EntitiesInSystem):
    pass


@dataclasses.dataclass
class SystemLarge(System):
    stops: StopsInSystem = NULL
    routes: RoutesInSystem = NULL
    feeds: FeedsInSystem = NULL
    agency_alerts: list = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class SystemUpdate(View):
    id: str
    status: models.SystemUpdate.Status
    status_message: str
    scheduled_at: datetime.datetime
    completed_at: datetime.datetime
    system: System = NULL

    @classmethod
    def from_model(cls, update: models.SystemUpdate):
        return cls(
            id=str(update.pk),
            status=update.status,
            status_message=update.status_message,
            scheduled_at=update.scheduled_at,
            completed_at=update.completed_at,
        )


@dataclasses.dataclass
class Route(View):
    class Status(enum.Enum):
        NO_SERVICE = 0
        GOOD_SERVICE = 1
        PLANNED_SERVICE_CHANGE = 2
        UNPLANNED_SERVICE_CHANGE = 3
        DELAYS = 4

    id: str
    color: str
    _system_id: str
    status: Status = NULL

    @classmethod
    def from_model(cls, route: models.Route):
        return cls(id=route.id, color=route.color, _system_id=route.system.id)


@dataclasses.dataclass
class RouteLarge(View):

    id: str
    color: str
    short_name: str
    long_name: str
    description: str
    url: str
    type: models.Route.Type
    _system_id: str
    status: Route.Status
    periodicity: float
    alerts: list
    service_maps: list

    @classmethod
    def from_model(cls, route: models.Route, status, periodicity, alerts, service_maps):
        return cls(
            id=route.id,
            color=route.color,
            short_name=route.short_name,
            long_name=route.long_name,
            description=route.description,
            url=route.url,
            type=route.type,
            _system_id=route.system.id,
            status=status,
            periodicity=periodicity,
            alerts=alerts,
            service_maps=service_maps,
        )


@dataclasses.dataclass
class Stop(View):
    id: str
    name: str
    _system_id: str
    service_maps: list = NULL
    parent_stop: typing.Optional["Stop"] = NULL
    child_stops: list = NULL

    @classmethod
    def from_model(cls, stop: models.Stop):
        return cls(id=stop.id, name=stop.name, _system_id=stop.system.id)


@dataclasses.dataclass
class StopLarge(View):
    id: str
    name: str
    longitude: float
    latitude: float
    url: str
    _system_id: str
    service_maps: list = NULL
    parent_stop: typing.Optional["Stop"] = NULL
    child_stops: list = NULL
    directions: list = NULL
    stop_times: list = dataclasses.field(default_factory=list)

    @classmethod
    def from_model(cls, stop: models.Stop):
        return cls(
            id=stop.id,
            name=stop.name,
            longitude=stop.longitude,
            latitude=stop.latitude,
            url=stop.url,
            _system_id=stop.system.id,
        )


@dataclasses.dataclass
class ServiceMapWithRoutes(View):
    group_id: str
    routes: typing.List[Route]


@dataclasses.dataclass
class ServiceMapWithStops(View):
    group_id: str
    stops: typing.List[Stop]


@dataclasses.dataclass
class Trip(View):
    id: str
    direction_id: bool
    start_time: datetime.datetime
    last_update_time: datetime.datetime
    current_status: models.Trip.TripStatus
    current_stop_sequence: int
    vehicle_id: str
    _system_id: str
    _route_id: str
    route: Route = NULL
    last_stop: Stop = NULL
    stop_times: list = NULL

    @classmethod
    def from_model(cls, trip: models.Trip):
        return cls(
            id=trip.id,
            direction_id=trip.direction_id,
            start_time=trip.start_time,
            last_update_time=trip.last_update_time,
            current_status=trip.current_status,
            current_stop_sequence=trip.current_stop_sequence,
            vehicle_id=trip.vehicle_id,
            _system_id=trip.route.system.id,
            _route_id=trip.route.id,
        )


@dataclasses.dataclass
class _TripStopTimeEvent(View):
    time: datetime.datetime
    delay: typing.Optional[int]
    uncertainty: typing.Optional[int]


@dataclasses.dataclass
class TripStopTime(View):
    arrival: _TripStopTimeEvent
    departure: _TripStopTimeEvent
    track: str
    future: bool
    stop_sequence: int
    direction: str = NULL
    stop: Stop = NULL
    trip: Trip = NULL

    @classmethod
    def from_model(cls, trip_stop_time: models.TripStopTime):
        return cls(
            arrival=_TripStopTimeEvent(
                time=trip_stop_time.arrival_time,
                delay=trip_stop_time.arrival_delay,
                uncertainty=trip_stop_time.arrival_uncertainty,
            ),
            departure=_TripStopTimeEvent(
                time=trip_stop_time.departure_time,
                delay=trip_stop_time.departure_delay,
                uncertainty=trip_stop_time.departure_uncertainty,
            ),
            track=trip_stop_time.track,
            future=trip_stop_time.future,
            stop_sequence=trip_stop_time.stop_sequence,
        )


@dataclasses.dataclass
class Feed(View):
    id: str
    auto_update_period: int
    _system_id: str
    updates: "UpdatesInFeedLink" = NULL
    system: models.System = NULL

    @classmethod
    def from_model(cls, feed: models.Feed, add_system=False):
        return cls(
            id=feed.id,
            auto_update_period=feed.auto_update_period,
            _system_id=feed.system.id,
            system=System.from_model(feed.system) if add_system else NULL,
        )


@dataclasses.dataclass
class FeedLarge(Feed):
    pass


@dataclasses.dataclass
class UpdatesInFeedLink(View):
    _feed_id: str
    _system_id: str

    @classmethod
    def from_model(cls, feed: models.Feed):
        return cls(_feed_id=feed.id, _system_id=feed.system.id)


@dataclasses.dataclass
class FeedUpdate(View):
    id: str
    type: models.FeedUpdate.Type
    status: models.FeedUpdate.Status
    result: models.FeedUpdate.Result
    result_message: str
    content_hash: str
    content_length: int
    completed_at: datetime.datetime

    @classmethod
    def from_model(cls, feed_update: models.FeedUpdate):
        return cls(
            id=str(feed_update.pk),
            type=feed_update.update_type,
            status=feed_update.status,
            result=feed_update.result,
            result_message=feed_update.result_message,
            content_hash=feed_update.content_hash,
            content_length=feed_update.content_length,
            completed_at=feed_update.completed_at,
        )


@dataclasses.dataclass
class AlertLarge(View):
    id: str
    start_time: datetime.datetime
    end_time: datetime.datetime
    creation_time: datetime.datetime
    header: str
    description: str
    url: str
    cause: models.Alert.Cause
    effect: models.Alert.Effect

    @classmethod
    def from_model(cls, alert: models.Alert):
        return cls(
            id=alert.id,
            start_time=alert.start_time,
            end_time=alert.end_time,
            creation_time=alert.creation_time,
            header=alert.header,
            description=alert.description,
            url=alert.url,
            cause=alert.cause,
            effect=alert.effect,
        )
