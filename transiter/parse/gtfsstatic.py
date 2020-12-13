"""
The GTFS Static module contains the logic for reading feeds of this format.

The official reference is here: https://gtfs.org/reference/static
"""

import csv
import datetime
import enum
import io
import typing
import uuid
import zipfile
import dataclasses
from transiter.parse import types as parse
from transiter.parse.parser import TransiterParser


class GtfsStaticParser(TransiterParser):

    gtfs_static_file = None

    def __init__(self):
        super().__init__()
        self._transfers_config = _TransfersConfig()

    def load_options(self, options_blob: typing.Optional[dict]) -> None:
        self._transfers_config = _TransfersConfig.load_from_options_blob(
            options_blob.get("transfers")
        )

    def load_content(self, content: bytes) -> None:
        self.gtfs_static_file = _GtfsStaticFile(content)

    def get_agencies(self) -> typing.Iterable[parse.Agency]:
        for row in self.gtfs_static_file.agency():
            yield parse.Agency(
                id=row.get(
                    "agency_id", "transiter_auto_generated_id_" + str(uuid.uuid4())
                ),
                name=row["agency_name"],
                url=row["agency_url"],
                timezone=row["agency_timezone"],
                language=row.get("agency_language"),
                phone=row.get("agency_phone"),
                fare_url=row.get("agency_fare_url"),
                email=row.get("agency_email"),
            )

    def get_routes(self) -> typing.Iterable[parse.Route]:
        yield from _parse_routes(self.gtfs_static_file)

    def get_stops(self) -> typing.Iterable[parse.Stop]:
        yield from _parse_stops(self.gtfs_static_file, self._transfers_config)

    def get_transfers(self) -> typing.Iterable[parse.Transfer]:
        yield from _parse_transfers(self.gtfs_static_file, self._transfers_config)

    def get_scheduled_services(self) -> typing.Iterable[parse.ScheduledService]:
        yield from _parse_schedule(self.gtfs_static_file)


class _TransfersStrategy(enum.Enum):
    DEFAULT = 0
    GROUP_STATIONS = 1


@dataclasses.dataclass
class _TransfersConfigException:
    strategy: _TransfersStrategy
    stop_ids: typing.Set[str]


@dataclasses.dataclass
class _TransfersConfig:
    default_strategy: _TransfersStrategy = _TransfersStrategy.DEFAULT
    exceptions: typing.List[typing.Set[str]] = dataclasses.field(default_factory=list)

    @classmethod
    def load_from_options_blob(cls, options_blob):
        config = cls()
        if options_blob is None:
            return config
        config.default_strategy = _TransfersStrategy[
            options_blob.pop("strategy", "DEFAULT").upper()
        ]
        for exceptions_blob in options_blob.pop("exceptions", []):
            if not isinstance(exceptions_blob, list):
                raise ValueError(
                    "A specific transfer strategy exception must be a list of stop IDs"
                )
            config.exceptions.append(set(exceptions_blob))
        if len(options_blob) > 0:
            raise ValueError(
                "Unrecognized transfers sub-options: {}".format(options_blob)
            )
        return config

    def get_strategy(self, stop_1_id, stop_2_id) -> _TransfersStrategy:
        for exception in self.exceptions:
            if stop_1_id not in exception:
                continue
            if stop_2_id not in exception:
                continue
            return (
                _TransfersStrategy.DEFAULT
                if self.default_strategy == _TransfersStrategy.GROUP_STATIONS
                else _TransfersStrategy.GROUP_STATIONS
            )
        return self.default_strategy


class _GtfsStaticFile:
    class _InternalFileName(enum.Enum):
        AGENCY = "agency.txt"
        CALENDAR = "calendar.txt"
        CALENDAR_DATES = "calendar_dates.txt"
        FREQUENCIES = "frequencies.txt"
        ROUTES = "routes.txt"
        STOP_TIMES = "stop_times.txt"
        STOPS = "stops.txt"
        TRANSFERS = "transfers.txt"
        TRIPS = "trips.txt"

    def __init__(self, binary_content):
        self._zip_file = zipfile.ZipFile(io.BytesIO(binary_content))

    def agency(self):
        return self._read_internal_file(self._InternalFileName.AGENCY)

    def calendar(self):
        return self._read_internal_file(self._InternalFileName.CALENDAR)

    def calendar_dates(self):
        return self._read_internal_file(self._InternalFileName.CALENDAR_DATES)

    def routes(self):
        return self._read_internal_file(self._InternalFileName.ROUTES)

    def stops(self):
        return self._read_internal_file(self._InternalFileName.STOPS)

    def stop_times(self):
        return self._read_internal_file(self._InternalFileName.STOP_TIMES)

    def transfers(self):
        return self._read_internal_file(self._InternalFileName.TRANSFERS)

    def trips(self):
        return self._read_internal_file(self._InternalFileName.TRIPS)

    def trip_frequencies(self):
        return self._read_internal_file(self._InternalFileName.FREQUENCIES)

    def _read_internal_file(self, file_name):
        """
        Read a GTFS static file

        :param file_name: which static file to real
        :return: iterator of dictionaries for each row
        """
        file_name = file_name.value
        try:
            with self._zip_file.open(file_name) as raw_csv_file:
                csv_file = io.TextIOWrapper(raw_csv_file, "utf-8-sig")
                csv_reader = csv.DictReader(csv_file)
                for row in csv_reader:
                    yield row
        except KeyError:
            return []


def _parse_routes(gtfs_static_file: _GtfsStaticFile):
    for row in gtfs_static_file.routes():
        yield parse.Route(
            id=row["route_id"],
            type=parse.Route.Type(int(row["route_type"])),
            agency_id=row.get("agency_id"),
            color=row.get("route_color", "FFFFF"),
            text_color=row.get("route_text_color", "000000"),
            url=row.get("route_url"),
            short_name=row.get("route_short_name"),
            long_name=row.get("route_long_name"),
            description=row.get("route_desc"),
            sort_order=_cast_to_int(row.get("route_sort_order")),
            continuous_pickup=_get_enum_by_key(
                parse.BoardingPolicy,
                row.get("continuous_pickup"),
                parse.BoardingPolicy.NOT_ALLOWED,
            ),
            continuous_drop_off=_get_enum_by_key(
                parse.BoardingPolicy,
                row.get("continuous_drop_off"),
                parse.BoardingPolicy.NOT_ALLOWED,
            ),
        )


def _parse_stops(gtfs_static_file: _GtfsStaticFile, transfers_config: _TransfersConfig):

    stop_id_to_stop = {}
    stop_id_to_parent_stop_id = {}

    for row in gtfs_static_file.stops():
        stop = parse.Stop(
            id=row["stop_id"],
            name=row["stop_name"],
            longitude=float(row["stop_lon"]),
            latitude=float(row["stop_lat"]),
            type=parse.Stop.Type(int(row.get("location_type", "0"))),
            code=row.get("stop_code"),
            description=row.get("stop_desc"),
            zone_id=row.get("zone_id"),
            url=row.get("stop_url"),
            timezone=row.get("stop_timezone"),
            wheelchair_boarding=parse.Stop.WheelchairBoarding(
                int(row.get("wheelchair_boarding", "0"))
            ),
            platform_code=row.get("platform_code"),
        )
        parent_stop_id = row.get("parent_station", "")
        if parent_stop_id != "":
            stop_id_to_parent_stop_id[stop.id] = parent_stop_id
        stop_id_to_stop[stop.id] = stop

    for stop_id, parent_stop_id in stop_id_to_parent_stop_id.items():
        stop_id_to_stop[stop_id].parent_stop = stop_id_to_stop[parent_stop_id]

    yield from stop_id_to_stop.values()

    station_sets_by_stop_id = _build_station_sets(gtfs_static_file, transfers_config)
    for station_set in station_sets_by_stop_id.values():
        if len(station_set) <= 1:
            continue
        child_stops = [stop_id_to_stop[stop_id] for stop_id in station_set]
        parent_stop = _create_station_from_child_stops(child_stops)
        for child_stop in child_stops:
            child_stop.parent_stop = parent_stop
        yield parent_stop
        station_set.clear()


def _parse_transfers(
    gtfs_static_file: _GtfsStaticFile, transfers_config: _TransfersConfig
):
    station_sets_by_stop_id = _build_station_sets(gtfs_static_file, transfers_config)

    for row in gtfs_static_file.transfers():
        stop_id_1 = row["from_stop_id"]
        stop_id_2 = row["to_stop_id"]
        if stop_id_1 == stop_id_2:
            continue
        # Don't create transfers for stops that share a grouped station parent
        if stop_id_1 in station_sets_by_stop_id.get(stop_id_2, set()):
            continue
        yield parse.Transfer(
            from_stop_id=stop_id_1,
            to_stop_id=stop_id_2,
            type=_get_enum_by_key(
                parse.Transfer.Type,
                row.get("transfer_type"),
                parse.Transfer.Type.RECOMMENDED,
            ),
            min_transfer_time=_cast_to_int(row.get("min_transfer_time")),
        )


def _get_enum_by_key(enum_class, key, default):
    try:
        return enum_class(_cast_to_int(key))
    except ValueError:
        return default


def _cast_to_int(string) -> typing.Optional[int]:
    try:
        return int(string)
    except (ValueError, TypeError):
        return None


def _cast_to_float(string) -> typing.Optional[float]:
    try:
        return float(string)
    except (ValueError, TypeError):
        return None


def _build_station_sets(
    gtfs_static_file: _GtfsStaticFile, transfers_config: _TransfersConfig
) -> typing.Dict[str, typing.Set[str]]:
    station_sets_by_stop_id = {}
    for row in gtfs_static_file.transfers():
        stop_id_1 = row["from_stop_id"]
        stop_id_2 = row["to_stop_id"]
        if stop_id_1 == stop_id_2:
            continue
        if (
            transfers_config.get_strategy(stop_id_1, stop_id_2)
            != _TransfersStrategy.GROUP_STATIONS
        ):
            continue
        for stop_id in [stop_id_1, stop_id_2]:
            if stop_id not in station_sets_by_stop_id:
                station_sets_by_stop_id[stop_id] = {stop_id}
        updated_station_set = station_sets_by_stop_id[stop_id_1].union(
            station_sets_by_stop_id[stop_id_2]
        )
        for stop_id in updated_station_set:
            station_sets_by_stop_id[stop_id] = updated_station_set
    return station_sets_by_stop_id


def _create_station_from_child_stops(child_stops):
    """
    Create a station from child stops.

    Some attributes will be set automatically based on the children:
    - latitude: the average of the child stops' latitudes
    - longitude: same
    - id: A-B-C, where [A, B, C] are the child stops' ids in sorted order.
    - name: grouping children by name, if there is unique largest group then
        this is set to be the parents name. Otherwise its the names in the
        largest groups in sorted order separated by forward slash.

    :param child_stops: list of child stops
    :return: the parent station
    """
    latitude = sum(float(child_stop.latitude) for child_stop in child_stops) / len(
        child_stops
    )
    longitude = sum(float(child_stop.longitude) for child_stop in child_stops) / len(
        child_stops
    )

    child_stop_ids = [child_stop.id for child_stop in child_stops]
    stop_id = "-".join(sorted(child_stop_ids))

    child_stop_names = {child_stop.name: 0 for child_stop in child_stops}
    for child_stop in child_stops:
        child_stop_names[child_stop.name] += 1
    max_freq = max(child_stop_names.values())
    most_frequent_names = set()
    for child_stop_name, freq in child_stop_names.items():
        if freq == max_freq:
            most_frequent_names.add(child_stop_name)

    # This part removes names which appear as substrings in other names
    for name in most_frequent_names.copy():
        remove = False
        for other_name in most_frequent_names:
            if name != other_name and name in other_name:
                remove = True
        if remove:
            most_frequent_names.remove(name)
    name = " / ".join(sorted(most_frequent_names))

    return parse.Stop(
        id=stop_id,
        name=name,
        longitude=longitude,
        latitude=latitude,
        type=parse.Stop.Type.GROUPED_STATION,
    )


def _parse_schedule(gtfs_static_file: _GtfsStaticFile):
    str_to_bool = {"0": False, "1": True}

    service_id_to_service = {}
    for row in gtfs_static_file.calendar():
        service_id = row["service_id"]
        service_id_to_service[service_id] = parse.ScheduledService(
            id=service_id,
            monday=str_to_bool[row["monday"]],
            tuesday=str_to_bool[row["tuesday"]],
            wednesday=str_to_bool[row["wednesday"]],
            thursday=str_to_bool[row["thursday"]],
            friday=str_to_bool[row["friday"]],
            saturday=str_to_bool[row["saturday"]],
            sunday=str_to_bool[row["sunday"]],
            start_date=date_string_to_datetime_date(row["start_date"]),
            end_date=date_string_to_datetime_date(row["end_date"]),
        )

    for row in gtfs_static_file.calendar_dates():
        service_id = row["service_id"]
        if service_id not in service_id_to_service:
            service_id_to_service[service_id] = parse.ScheduledService.create_empty(
                service_id
            )
        date = date_string_to_datetime_date(row["date"])
        if row["exception_type"] == "1":
            service_id_to_service[service_id].added_dates.append(date)
        else:
            service_id_to_service[service_id].removed_dates.append(date)

    trip_id_to_trip = {}
    for row in gtfs_static_file.trips():
        service_id = row["service_id"]
        if service_id not in service_id_to_service:
            continue
        trip = parse.ScheduledTrip(
            id=row["trip_id"],
            route_id=row["route_id"],
            direction_id=str_to_bool.get(row["direction_id"]),
            headsign=row.get("trip_headsign"),
            short_name=row.get("trip_short_name"),
            block_id=row.get("block_id"),
            wheelchair_accessible=_get_enum_by_key(
                parse.ScheduledTrip.WheelchairAccessible,
                row.get("wheelchair_accessible"),
                parse.ScheduledTrip.WheelchairAccessible.UNKNOWN,
            ),
            bikes_allowed=_get_enum_by_key(
                parse.ScheduledTrip.BikesAllowed,
                row.get("bikes_allowed"),
                parse.ScheduledTrip.BikesAllowed.UNKNOWN,
            ),
        )
        service_id_to_service[service_id].trips.append(trip)
        trip_id_to_trip[trip.id] = trip

    # NOTE: memoization of the next function cuts about 2 seconds off the time taken to
    # parse the NYC Subway's GTFS static feed. However because the function itself is
    # not very computationally intensive, to see any benefit it is necessary to have
    # a very simple memoization process.
    cache = {}

    def time_string_to_datetime_time(time_string):
        if time_string not in cache:
            s = time_string.split(":")
            if len(s) != 3:
                return None
            hour, minute, second = s
            cache[time_string] = datetime.time(
                hour=int(hour) % 24, minute=int(minute), second=int(second)
            )
        return cache[time_string]

    for row in gtfs_static_file.trip_frequencies():
        trip = trip_id_to_trip.get(row["trip_id"])
        if trip is None:
            continue
        trip.frequencies.append(
            parse.ScheduledTripFrequency(
                start_time=time_string_to_datetime_time(row["start_time"]),
                end_time=time_string_to_datetime_time(row["end_time"]),
                headway=int(row["headway_secs"]),
                frequency_based=row.get("exact_times") != "1",
            )
        )

    for row in gtfs_static_file.stop_times():
        trip_id = row["trip_id"]
        if trip_id not in trip_id_to_trip:
            continue
        dep_time = time_string_to_datetime_time(row["departure_time"])
        arr_time = time_string_to_datetime_time(row["arrival_time"])
        if dep_time is None:
            print("Skipping stop_times.txt row", row)
            continue
        if arr_time is None:
            arr_time = dep_time
        stop_time = parse.ScheduledTripStopTime(
            stop_id=row["stop_id"],
            stop_sequence=int(row["stop_sequence"]),
            departure_time=dep_time,
            arrival_time=arr_time,
            headsign=row.get("stop_headsign"),
            pickup_type=_get_enum_by_key(
                parse.BoardingPolicy,
                row.get("pickup_type"),
                parse.BoardingPolicy.ALLOWED,
            ),
            drop_off_type=_get_enum_by_key(
                parse.BoardingPolicy,
                row.get("drop_off_type"),
                parse.BoardingPolicy.ALLOWED,
            ),
            continuous_pickup=_get_enum_by_key(
                parse.BoardingPolicy,
                row.get("continuous_pickup"),
                parse.BoardingPolicy.NOT_ALLOWED,
            ),
            continuous_drop_off=_get_enum_by_key(
                parse.BoardingPolicy,
                row.get("continuous_drop_off"),
                parse.BoardingPolicy.NOT_ALLOWED,
            ),
            shape_distance_traveled=_cast_to_float(row.get("shape_dist_traveled")),
            exact_times=row.get("timepoint", "0") == "1",
        )
        trip_id_to_trip[trip_id].stop_times.append(stop_time)

    yield from service_id_to_service.values()


def date_string_to_datetime_date(date_string):
    return datetime.date(
        year=int(date_string[0:4]),
        month=int(date_string[4:6]),
        day=int(date_string[6:8]),
    )
