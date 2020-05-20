import datetime
import enum
import typing
from dataclasses import dataclass, field


@dataclass
class Agency:
    id: str
    name: str
    url: str
    timezone: str
    language: str = None
    phone: str = None
    fare_url: str = None
    email: str = None


@dataclass
class Route:
    class Type(enum.Enum):
        LIGHT_RAIL = 0
        SUBWAY = 1
        RAIL = 2
        BUS = 3
        FERRY = 4
        CABLE_CAR = 5
        GONDOLA = 6
        FUNICULAR = 7
        TROLLEYBUS = 11
        MONORAIL = 12

    id: str
    type: Type
    agency_id: str = None
    short_name: str = None
    long_name: str = None
    description: str = None
    color: str = None
    text_color: str = None
    url: str = None
    sort_order: int = None


@dataclass
class Stop:
    class Type(enum.Enum):
        PLATFORM = 0
        STATION = 1
        ENTRANCE_OR_EXIT = 2
        GENERIC_NODE = 3
        BOARDING_AREA = 4
        GROUPED_STATION = 101  # Transiter only

    class WheelchairBoarding(enum.Enum):
        NOT_SPECIFIED = 0
        ACCESSIBLE = 1
        NOT_ACCESSIBLE = 2

    id: str
    name: str
    longitude: float
    latitude: float
    type: Type
    parent_stop: typing.Optional["Stop"] = None
    code: str = None
    description: str = None
    zone_id: str = None
    url: str = None
    timezone: str = None
    wheelchair_boarding: WheelchairBoarding = WheelchairBoarding.NOT_SPECIFIED
    platform_code: str = None


@dataclass
class ScheduledService:
    id: str
    monday: bool
    tuesday: bool
    wednesday: bool
    thursday: bool
    friday: bool
    saturday: bool
    sunday: bool
    start_date: datetime.date = None
    end_date: datetime.date = None
    trips: typing.List["ScheduledTrip"] = field(default_factory=list)
    added_dates: typing.List[datetime.date] = field(default_factory=list)
    removed_dates: typing.List[datetime.date] = field(default_factory=list)

    @classmethod
    def create_empty(cls, id_) -> "ScheduledService":
        return cls(
            id=id_,
            monday=False,
            tuesday=False,
            wednesday=False,
            thursday=False,
            friday=False,
            saturday=False,
            sunday=False,
        )


@dataclass
class ScheduledTrip:
    id: str
    route_id: str
    direction_id: bool
    stop_times: typing.List["ScheduledTripStopTime"] = field(default_factory=list)
    frequencies: typing.List["ScheduledTripFrequency"] = field(default_factory=list)


@dataclass
class ScheduledTripFrequency:
    start_time: datetime.time
    end_time: datetime.time
    headway: int
    frequency_based: bool = True


@dataclass
class ScheduledTripStopTime:
    stop_id: str
    arrival_time: typing.Optional[datetime.time]
    departure_time: typing.Optional[datetime.time]
    stop_sequence: int


@dataclass
class Trip:
    class Status(enum.Enum):
        SCHEDULED = 1
        INCOMING_AT = 2
        STOPPED_AT = 3
        IN_TRANSIT_TO = 4

    id: str
    route_id: typing.Optional[str]
    direction_id: typing.Optional[bool]
    start_time: datetime.datetime = None
    stop_times: typing.List["TripStopTime"] = field(default_factory=list)

    # The following 5 fields correspond to VehiclePosition in the GTFS Realtime spec
    # and will be eventually moved to a new Vehicle type.
    train_id: str = None  # ?
    current_stop_sequence: int = None
    current_status: Status = None
    current_stop_id: str = None
    updated_at: datetime.datetime = None


@dataclass
class TripStopTime:
    stop_id: str
    arrival_time: datetime.datetime = None
    arrival_delay: int = None
    arrival_uncertainty: int = None
    departure_time: datetime.datetime = None
    departure_delay: int = None
    departure_uncertainty: int = None
    track: str = None  # Transiter-only non-GTFS field
    stop_sequence: int = None
    future: bool = True


@dataclass
class Alert:
    class Cause(enum.Enum):
        UNKNOWN_CAUSE = 1
        OTHER_CAUSE = 2
        TECHNICAL_PROBLEM = 3
        STRIKE = 4
        DEMONSTRATION = 5
        ACCIDENT = 6
        HOLIDAY = 7
        WEATHER = 8
        MAINTENANCE = 9
        CONSTRUCTION = 10
        POLICE_ACTIVITY = 11
        MEDICAL_EMERGENCY = 12

    class Effect(enum.Enum):
        NO_SERVICE = 1
        REDUCED_SERVICE = 2
        SIGNIFICANT_DELAYS = 3
        DETOUR = 4
        ADDITIONAL_SERVICE = 5
        MODIFIED_SERVICE = 6
        OTHER_EFFECT = 7
        UNKNOWN_EFFECT = 8
        STOP_MOVED = 9

    id: str
    cause: Cause = Cause.UNKNOWN_CAUSE
    effect: Effect = Effect.UNKNOWN_EFFECT
    created_at: datetime.datetime = None  # Non-GTFS field
    updated_at: datetime.datetime = None  # Non-GTFS field
    sort_order: int = None  # Non-GTFS field

    messages: typing.List["AlertMessage"] = field(default_factory=list)
    active_periods: typing.List["AlertActivePeriod"] = field(default_factory=list)
    agency_ids: typing.List[str] = field(default_factory=list)
    route_ids: typing.List[str] = field(default_factory=list)
    route_types: typing.List[Route.Type] = field(default_factory=list)
    trip_ids: typing.List[str] = field(default_factory=list)
    stop_ids: typing.List[str] = field(default_factory=list)


@dataclass
class AlertMessage:
    header: str
    description: str
    url: str = None
    language: str = None


@dataclass
class AlertActivePeriod:
    starts_at: datetime.datetime = None
    ends_at: datetime.datetime = None


@dataclass
class DirectionRule:
    name: str
    id: str = None
    priority: int = None
    stop_id: str = None
    direction_id: bool = None
    track: str = None
