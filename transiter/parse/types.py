"""
# Parser output types reference

This file contains a full description of the possible types that can be output
by a feed parser in Transiter.
This page is auto-generated from the
`transiter.parse.types` module, where the parser types are defined.
Most of the types and fields correspond to fields in the
[GTFS Static](https://developers.google.com/transit/gtfs/reference/) and
[GTFS Realtime](https://developers.google.com/transit/gtfs-realtime/reference)
specifications.
It may be useful to consult those specs for more information on particular fields.


"""
import datetime
import enum
import typing
from dataclasses import dataclass
import dataclasses


def foreign_key_str(type_, field):
    new_type = typing.NewType("ForeignKey", str)
    new_type.__fk_type__ = type_
    new_type.__fk_field__ = field
    return new_type


def _field(arg_1, arg_2=None):
    doc = arg_1
    default = dataclasses.MISSING
    default_factory = dataclasses.MISSING
    if arg_2 is not None:
        doc = arg_2
        if arg_1 is list:
            default_factory = list
        else:
            default = arg_1
    return dataclasses.field(
        default=default, default_factory=default_factory, metadata={"doc": doc}
    )


def dfield(*args, **kwargs):
    return dataclasses.field(*args, **kwargs)


@dataclass
class Agency:
    """
    Represents a transit system agency.
    This type corresponds closely to the GTFS Static `agency.txt` table.

    As in GTFS Static, the timezone field is mandatory.
    If the system this agency is imported into has no timezone, the system timezone
    will be set to the agency timezone.
    """

    id: str
    name: str
    url: str
    timezone: str
    language: str = None
    phone: str = None
    fare_url: str = None
    email: str = None


class BoardingPolicy(enum.Enum):
    ALLOWED = 0
    NOT_ALLOWED = 1
    COORDINATE_WITH_AGENCY = 2
    COORDINATE_WITH_DRIVER = 3


@dataclass
class Route:
    """
    Represents a route in a transit system.
    This type corresponds closely to the GTFS Static `routes.txt` table.

    The sort_order field is used to order routes, with routes having lower sort_orders
    coming first.
    """

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
    agency_id: foreign_key_str(Agency, "id") = None
    short_name: str = None
    long_name: str = None
    description: str = None
    color: str = None
    text_color: str = None
    url: str = None
    sort_order: int = None
    continuous_pickup: BoardingPolicy = BoardingPolicy.NOT_ALLOWED
    continuous_drop_off: BoardingPolicy = BoardingPolicy.NOT_ALLOWED


@dataclass
class Stop:
    """
    Represents a stop in a transit system, like the GTFS Static `stops.txt` table.
    A stop can mean different things depending on its type:

    - A `BOARDING_AREA` is a physical location within a `PLATFORM` where passengers
        can board a vehicle. It must have a parent stop of type `PLATFORM`.

    - A `PLATFORM` generally denotes a place where vehicles can stop.
        Its optional parent stop, if provided, must be a `STATION`.

    - A `STATION` often refers to the physical idea of station, containing multiple
        platforms where vehicles can stop.
        In the GTFS Static spec stations can't have parent stops but in Transiter
        they can have a parent stop of type `STATION_GROUP`.

    - A `STATION_GROUP` represents a collection of different stations.
        This type does not exist in the GTFS Static spec but is unique to Transiter.
        The station group type is useful when
        distinct "stations" in a feed are actually in the same physical structure,
        and linking them with `Transfer` types is not as meaningful.

    - A `ENTRANCE_OR_EXIT` is what it says it is, and it must have a parent stop
        of type `STATION`.

    - A `GENERIC_NODE` represent some other point in a station. It must have a parent
        stop of type `STATION`.

    Note that none of the "must" statements here are enforced by Transiter.
    """

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
class Transfer:
    """
    Represents an available transfer between two stops.
    It is closely connected to the GTFS Static `transfers.txt` table.

    Note that the parse and import process can only create transfers between two
    stops in the same system. For creating cross-system transfers, see the docs here.
    """

    class Type(enum.Enum):
        RECOMMENDED = 0
        COORDINATED = 1
        POSSIBLE = 2
        NO_TRANSFER = 3
        GEOGRAPHIC = 4  # TODO remove check constraint

    from_stop_id: foreign_key_str(Stop, "id")
    to_stop_id: foreign_key_str(Stop, "id")
    type: Type = Type.RECOMMENDED
    min_transfer_time: typing.Optional[int] = None


@dataclass
class ScheduledService:
    """
    A scheduled service relates a group of trips with the days those trips run.
    The field corresponding to a day of the week is true if the trips run on that day,
    and false otherwise. It can also specify additional dates
    (`added_dates`) and skipped dates (`removed_dates`) that the trips do and don't
    run on, respectively.

    It is a combination of the GTFS Static tables `calender.txt` and
    `calender_dates.txt`.
    """

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
    trips: typing.List["ScheduledTrip"] = dfield(default_factory=list)
    added_dates: typing.List[datetime.date] = dfield(default_factory=list)
    removed_dates: typing.List[datetime.date] = dfield(default_factory=list)

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
    """
    Represents a trip in a scheduled service.
    This type corresponds closely to the GTFS Static `trips.txt` table.
    """

    class WheelchairAccessible(enum.Enum):
        UNKNOWN = 0
        ACCESSIBLE = 1
        NOT_ACCESSIBLE = 2

    class BikesAllowed(enum.Enum):
        UNKNOWN = 0
        ALLOWED = 1
        NOT_ALLOWED = 2

    id: str
    route_id: foreign_key_str(Route, "id")
    direction_id: bool
    headsign: str = None
    short_name: str = None
    block_id: str = None
    wheelchair_accessible: WheelchairAccessible = WheelchairAccessible.UNKNOWN
    bikes_allowed: BikesAllowed = BikesAllowed.UNKNOWN
    stop_times: typing.List["ScheduledTripStopTime"] = dfield(default_factory=list)
    frequencies: typing.List["ScheduledTripFrequency"] = dfield(default_factory=list)


@dataclass
class ScheduledTripFrequency:
    """
    This type corresponds to the GTFS Static `frequencies.txt` and is used to denote
    the 'same' trip running multiple times at a fixed interval.
    """

    start_time: datetime.time
    end_time: datetime.time
    headway: int
    frequency_based: bool = True


@dataclass
class ScheduledTripStopTime:
    """
    Contains data on when a specific trip calls at a specific stop.
    Corresponds to the GTFS Static `stop_times.txt` table.
    """

    stop_id: foreign_key_str(Stop, "id")
    arrival_time: typing.Optional[datetime.time]
    departure_time: typing.Optional[datetime.time]
    stop_sequence: int
    headsign: str = None
    pickup_type: BoardingPolicy = BoardingPolicy.ALLOWED
    drop_off_type: BoardingPolicy = BoardingPolicy.ALLOWED
    continuous_pickup: BoardingPolicy = BoardingPolicy.NOT_ALLOWED
    continuous_drop_off: BoardingPolicy = BoardingPolicy.NOT_ALLOWED
    shape_distance_traveled: float = None
    exact_times: bool = False


@dataclass
class Trip:
    """
    Represents a realtime trip in a transit system.
    This type corresponds to the TripUpdate and TripDescriptor types in GTFS Realtime.

    In Transiter, every trip must have a unique trip ID, but this trip ID does not
    need to correspond to a trip in the schedule (i.e., a trip coming from GTFS
    Static and parsed as a `ScheduledTrip` type.)
    Each trip must also have a valid route ID.
    However, if the trip ID refers to a scheduled trip then the route ID can
    be omitted and will be copied from the scheduled trip.
    """

    class ScheduleRelationship(enum.Enum):
        SCHEDULED = 0
        ADDED = 1
        UNSCHEDULED = 2
        CANCELED = 3
        REPLACEMENT = 4
        UNKNOWN = 10

    id: str
    route_id: typing.Optional[foreign_key_str(Route, "id")] = None
    direction_id: typing.Optional[bool] = None
    schedule_relationship: ScheduleRelationship = ScheduleRelationship.UNKNOWN
    start_time: typing.Optional[datetime.datetime] = None
    updated_at: datetime.datetime = None
    delay: int = None
    stop_times: typing.List["TripStopTime"] = dfield(default_factory=list)


@dataclass
class TripStopTime:
    """
    Contains data on when a specific realtime trip calls at a specific stop.
    Corresponds to GTFS Realtime StopTimeUpdate data.
    """

    class ScheduleRelationship(enum.Enum):
        SCHEDULED = 0
        SKIPPED = 1
        NO_DATA = 2
        UNSCHEDULED = 3

    stop_id: str
    stop_sequence: int = None
    schedule_relationship: ScheduleRelationship = ScheduleRelationship.SCHEDULED
    arrival_time: datetime.datetime = None
    arrival_delay: int = None
    arrival_uncertainty: int = None
    departure_time: datetime.datetime = None
    departure_delay: int = None
    departure_uncertainty: int = None
    track: str = None  # Transiter-only non-GTFS field


@dataclass
class Vehicle:
    """
    Represents a (realtime) vehicle moving through the transit system.
    This type is based on the GTFS Realtime VehiclePosition and VehicleDescriptor
    types.

    There are two types of vehicle supported in Transiter:

    - Vehicle with a valid trip ID. The vehicle ID is optional for these vehicles
        as the vehicle can be uniquely identified using its trip.

    - Vehicles with no associated trip. These vehicles must have a valid and
        unique vehicle ID.
    """

    class Status(enum.Enum):
        INCOMING_AT = 0
        STOPPED_AT = 1
        IN_TRANSIT_TO = 2

    class CongestionLevel(enum.Enum):
        UNKNOWN_CONGESTION_LEVEL = 0
        RUNNING_SMOOTHLY = 1
        STOP_AND_GO = 2
        CONGESTION = 3
        SEVERE_CONGESTION = 4

    class OccupancyStatus(enum.Enum):
        EMPTY = 0
        MANY_SEATS_AVAILABLE = 1
        FEW_SEATS_AVAILABLE = 2
        STANDING_ROOM_ONLY = 3
        CRUSHED_STANDING_ROOM_ONLY = 4
        FULL = 5
        NOT_ACCEPTING_PASSENGERS = 6
        UNKNOWN = 100

    id: typing.Optional[str] = None
    trip_id: foreign_key_str(Trip, "id") = None
    label: str = None
    license_plate: str = None
    current_stop_sequence: int = None
    current_status: Status = Status.IN_TRANSIT_TO
    current_stop_id: str = None
    latitude: float = None
    longitude: float = None
    bearing: float = None
    odometer: float = None
    speed: float = None
    updated_at: datetime.datetime = None
    congestion_level: CongestionLevel = CongestionLevel.UNKNOWN_CONGESTION_LEVEL
    occupancy_status: OccupancyStatus = OccupancyStatus.UNKNOWN


@dataclass
class Alert:
    """
    Represents an alert in the system.
    This type closely corresponds to the GTFS Realtime `Alert` type.
    """

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

    messages: typing.List["AlertMessage"] = dfield(default_factory=list)
    active_periods: typing.List["AlertActivePeriod"] = dfield(default_factory=list)
    agency_ids: typing.List[foreign_key_str(Agency, "id")] = dfield(
        default_factory=list
    )
    route_ids: typing.List[foreign_key_str(Route, "id")] = dfield(default_factory=list)
    route_types: typing.List[Route.Type] = dfield(default_factory=list)
    trip_ids: typing.List[foreign_key_str(Trip, "id")] = dfield(default_factory=list)
    stop_ids: typing.List[foreign_key_str(Stop, "id")] = dfield(default_factory=list)


@dataclass
class AlertMessage:
    """
    Represents the message of an alert.
    """

    header: str
    description: str
    url: str = None
    language: str = None


@dataclass
class AlertActivePeriod:
    """
    Represents the active period of an alert.
    In general in Transiter, alerts are only returned if the curren time is
    contained in one of the alert's active periods.
    """

    starts_at: datetime.datetime = None
    ends_at: datetime.datetime = None


@dataclass
class DirectionRule:
    """
    A direction rule is a Transiter-only type.
    It enables assigning a "direction" or "direction name" to a realtime trip
    stop time.

    At a given stop, all of the direction rules for that stop are retrieved and
    ordered by priority (lowest first).
    Each rule is checked in order to see if it matches data in the the trip stop time,
    like the direction ID of the trip or the track.
    The first rule that matches determines the direction.
    """

    name: str
    id: str = None
    priority: int = None
    stop_id: foreign_key_str(Stop, "id") = None
    direction_id: bool = None
    track: str = None
