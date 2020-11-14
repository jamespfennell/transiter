import dataclasses
import datetime
import enum
import typing

from transiter.db import models


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


class AgenciesInSystem(_EntitiesInSystem):
    pass


class RoutesInSystem(_EntitiesInSystem):
    pass


class StopsInSystem(_EntitiesInSystem):
    pass


class FeedsInSystem(_EntitiesInSystem):
    pass


class TransfersInSystem(_EntitiesInSystem):
    pass


@dataclasses.dataclass
class SystemLarge(System):
    agencies: AgenciesInSystem = NULL
    feeds: FeedsInSystem = NULL
    routes: RoutesInSystem = NULL
    stops: StopsInSystem = NULL
    transfers: TransfersInSystem = NULL


SystemUpdateStatus = models.SystemUpdate.Status


@dataclasses.dataclass
class SystemUpdate(View):
    id: str
    status: models.SystemUpdate.Status
    stack_trace: typing.Optional[typing.List[str]]
    scheduled_at: datetime.datetime
    completed_at: datetime.datetime
    system: System = NULL

    @classmethod
    def from_model(cls, update: models.SystemUpdate):
        return cls(
            id=str(update.pk),
            status=update.status,
            stack_trace=update.status_message.splitlines()
            if update.status_message is not None
            else None,
            scheduled_at=update.scheduled_at,
            completed_at=update.completed_at,
        )


@dataclasses.dataclass
class Agency(View):
    id: str
    name: str
    _system_id: str
    alerts: list = NULL

    @classmethod
    def from_model(cls, agency: models.Agency):
        return cls(id=agency.id, name=agency.name, _system_id=agency.system.id)


@dataclasses.dataclass
class AgencyLarge(View):
    id: str
    name: str
    url: str
    timezone: str
    language: str = None
    phone: str = None
    fare_url: str = None
    email: str = None
    alerts: list = NULL
    routes: list = dataclasses.field(default_factory=list)

    @classmethod
    def from_model(cls, agency: models.Agency):
        return cls(
            id=agency.id,
            name=agency.name,
            url=agency.url,
            timezone=agency.timezone,
            language=agency.language,
            phone=agency.phone,
            fare_url=agency.fare_url,
            email=agency.email,
        )


@dataclasses.dataclass
class Route(View):
    id: str
    color: str
    _system_id: str
    alerts: typing.List["AlertSmall"] = NULL

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
    periodicity: float
    agency: Agency = None
    alerts: list = NULL
    service_maps: list = dataclasses.field(default_factory=list)

    @classmethod
    def from_model(cls, route: models.Route, periodicity):
        return cls(
            id=route.id,
            color=route.color,
            short_name=route.short_name,
            long_name=route.long_name,
            description=route.description,
            url=route.url,
            type=route.type,
            _system_id=route.system.id,
            periodicity=periodicity,
        )


@dataclasses.dataclass
class Stop(View):
    id: str
    name: str
    _system_id: str
    distance: float = NULL
    system: System = NULL
    service_maps: list = NULL
    parent_stop: typing.Optional["Stop"] = NULL
    child_stops: list = NULL
    alerts: typing.List["AlertSmall"] = NULL

    @classmethod
    def from_model(cls, stop: models.Stop, show_system=False):
        result = cls(id=stop.id, name=stop.name, _system_id=stop.system.id)
        if show_system:
            result.system = System.from_model(stop.system)
        return result


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
    alerts: typing.List["AlertSmall"] = NULL
    transfers: typing.List["Transfer"] = NULL
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
class Transfer(View):
    from_stop: Stop
    to_stop: Stop
    type: models.Transfer.Type
    min_transfer_time: int = None
    distance: int = None

    @classmethod
    def from_model(cls, transfer: models.Transfer, from_stop_view, to_stop_view):
        return cls(
            from_stop=from_stop_view,
            to_stop=to_stop_view,
            type=transfer.type,
            min_transfer_time=transfer.min_transfer_time,
            distance=transfer.distance,
        )


@dataclasses.dataclass
class TransfersConfig(View):
    id: str
    distance: float
    systems: typing.List[System] = NULL

    @classmethod
    def from_model(cls, transfers_config: models.TransfersConfig):
        return cls(
            id=transfers_config.id,
            distance=transfers_config.distance,
            systems=list(map(System.from_model, transfers_config.systems)),
        )


@dataclasses.dataclass
class TransfersConfigBig(TransfersConfig):
    transfers: typing.List[Transfer] = NULL


@dataclasses.dataclass
class ServiceMapWithRoutes(View):
    group_id: str
    routes: typing.List[Route]


@dataclasses.dataclass
class ServiceMapWithStops(View):
    group_id: str
    stops: typing.List[Stop]


# TODO: add a vehicle endpoint and relevant href
@dataclasses.dataclass
class VehicleInTrip(View):
    id: typing.Optional[str]

    @classmethod
    def from_model(cls, vehicle: typing.Optional[models.Vehicle]):
        if vehicle is None:
            return None
        return cls(id=vehicle.id)


@dataclasses.dataclass
class Trip(View):
    id: str
    direction_id: bool
    started_at: datetime.datetime
    updated_at: datetime.datetime
    _system_id: str
    _route_id: str
    delay: int = None
    vehicle: VehicleInTrip = NULL
    route: Route = NULL
    last_stop: Stop = NULL
    stop_times: list = NULL
    alerts: list = NULL

    @classmethod
    def from_model(cls, trip: models.Trip):
        return cls(
            id=trip.id,
            direction_id=trip.direction_id,
            started_at=trip.started_at,
            updated_at=trip.updated_at,
            delay=trip.delay,
            vehicle=VehicleInTrip.from_model(trip.vehicle),
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
class FeedWStatisticsOutcome(View):
    status: models.FeedUpdate.Status
    result: models.FeedUpdate.Result
    count: int


@dataclasses.dataclass
class FeedStatistics(View):
    start_time: datetime.datetime
    end_time: datetime.datetime = NULL
    update_periodicity: float = None
    count: int = 0
    outcomes: typing.List[FeedWStatisticsOutcome] = dataclasses.field(
        default_factory=list
    )


@dataclasses.dataclass
class Feed(View):
    id: str
    auto_update_period: int
    _system_id: str
    updates: "UpdatesInFeedLink" = NULL
    statistics: typing.List[FeedStatistics] = NULL
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
    stack_trace: typing.Optional[typing.List[str]]
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
            stack_trace=feed_update.result_message.splitlines()
            if feed_update.result_message is not None
            else None,
            content_hash=feed_update.content_hash,
            content_length=feed_update.content_length,
            completed_at=feed_update.completed_at,
        )


@dataclasses.dataclass
class AlertMessage(View):
    header: str
    description: str
    url: str = None
    language: str = None

    @classmethod
    def from_model(cls, alert_message: models.AlertMessage):
        return cls(
            header=alert_message.header,
            description=alert_message.description,
            url=alert_message.url,
            language=alert_message.language,
        )


@dataclasses.dataclass
class AlertSmall(View):
    id: str
    cause: models.Alert.Cause
    effect: models.Alert.Effect

    @classmethod
    def from_models(cls, active_period, alert: models.Alert):
        return cls(id=alert.id, cause=alert.cause, effect=alert.effect)


@dataclasses.dataclass
class AlertLarge(View):
    id: str
    cause: models.Alert.Cause
    effect: models.Alert.Effect
    active_period: "AlertActivePeriod"
    messages: typing.List[AlertMessage] = dataclasses.field(default_factory=list)

    @classmethod
    def from_models(cls, active_period: models.AlertActivePeriod, alert: models.Alert):
        return cls(
            id=alert.id,
            cause=alert.cause,
            effect=alert.effect,
            active_period=AlertActivePeriod.from_model(active_period),
            messages=list(map(AlertMessage.from_model, alert.messages)),
        )


@dataclasses.dataclass
class AlertActivePeriod(View):
    starts_at: datetime.datetime
    ends_at: datetime.datetime

    @classmethod
    def from_model(cls, active_period: models.AlertActivePeriod):
        return cls(starts_at=active_period.starts_at, ends_at=active_period.ends_at)


@dataclasses.dataclass
class _AlertsDetailValue:
    clazz: typing.Optional[typing.Type[View]]
    need_messages: bool
    need_all_active_periods: bool


class AlertsDetail(enum.Enum):
    NONE = _AlertsDetailValue(None, False, False)
    CAUSE_AND_EFFECT = _AlertsDetailValue(AlertSmall, False, False)
    MESSAGES = _AlertsDetailValue(AlertLarge, True, False)
    ALL = _AlertsDetailValue(AlertLarge, True, True)
