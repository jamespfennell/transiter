"""
The GTFS Static Util contains the logic for reading feeds of this format.

The official reference is here: https://gtfs.org/reference/static
"""

import csv
import datetime
import enum
import io
import zipfile

from transiter import parse


# Additional arguments are accepted for forwards compatibility
# noinspection PyUnusedLocal
def parse_gtfs_static(binary_content, *args, **kwargs):
    """
    Parse a GTFS Static feed

    :param binary_content: raw binary GTFS static zip data
    """
    gtfs_static_file = GtfsStaticFile(binary_content)
    for parsing_function in [parse_routes, parse_stops, parse_schedule]:
        yield from parsing_function(gtfs_static_file)


class GtfsStaticFile:
    class _InternalFileName(enum.Enum):
        CALENDAR = "calendar.txt"
        ROUTES = "routes.txt"
        STOP_TIMES = "stop_times.txt"
        STOPS = "stops.txt"
        TRANSFERS = "transfers.txt"
        TRIPS = "trips.txt"

    def __init__(self, binary_content):
        self._zip_file = zipfile.ZipFile(io.BytesIO(binary_content))

    def calendar(self):
        return self._read_internal_file(self._InternalFileName.CALENDAR)

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


def parse_routes(gtfs_static_file: GtfsStaticFile):
    for row in gtfs_static_file.routes():
        yield parse.Route(
            id=row["route_id"],
            type=parse.Route.Type(int(row["route_type"])),
            color=row.get("route_color", "FFFFF"),
            text_color=row.get("route_text_color", "000000"),
            url=row.get("route_url"),
            short_name=row.get("route_short_name"),
            long_name=row.get("route_long_name"),
            description=row.get("route_desc"),
            sort_order=row.get("route_sort_order"),
        )


def parse_stops(gtfs_static_file: GtfsStaticFile):

    stop_id_to_stop = {}
    stop_id_to_parent_stop_id = {}

    # Step 1: read the basic stops in the GTFS feed into Stop objects.
    for row in gtfs_static_file.stops():
        stop = parse.Stop(
            id=row["stop_id"],
            name=row["stop_name"],
            longitude=float(row["stop_lon"]),
            latitude=float(row["stop_lat"]),
            url=row.get("stop_url"),
            is_station=row.get("location_type") == "1",
        )
        parent_stop_id = row.get("parent_station", "")
        if parent_stop_id != "":
            stop_id_to_parent_stop_id[stop.id] = parent_stop_id
        stop_id_to_stop[stop.id] = stop

    for stop_id, parent_stop_id in stop_id_to_parent_stop_id.items():
        stop_id_to_stop[stop_id].parent_stop = stop_id_to_stop[parent_stop_id]

    # Step 2: replace the parent stop IDs with the actual parent stop. If a stop does
    # not have a parent, make it a station.
    stop_id_to_station_id = {}
    station_sets_by_stop_id = {}
    for stop in stop_id_to_stop.values():
        if stop.parent_stop is None:
            stop.is_station = True
        if stop.is_station:
            station_sets_by_stop_id[stop.id] = {stop.id}
        else:
            stop_id_to_station_id[stop.id] = stop.parent_stop.id
        yield stop

    # Step 3: using the GTFS transfers data, link together stops which have a free
    # transfer.
    for row in gtfs_static_file.transfers():
        stop_id_1 = row["from_stop_id"]
        stop_id_2 = row["to_stop_id"]
        if stop_id_1 == stop_id_2:
            continue
        updated_station_set = station_sets_by_stop_id[stop_id_1].union(
            station_sets_by_stop_id[stop_id_2]
        )
        for stop_id in updated_station_set:
            station_sets_by_stop_id[stop_id] = updated_station_set

    # Step 4: create parent stations for stop linked together in Step 3.
    for station_set in station_sets_by_stop_id.values():
        if len(station_set) <= 1:
            continue
        child_stops = [stop_id_to_stop[stop_id] for stop_id in station_set]
        parent_stop = create_station_from_child_stops(child_stops)
        for child_stop in child_stops:
            child_stop.parent_stop = parent_stop
        yield parent_stop
        station_set.clear()


def create_station_from_child_stops(child_stops):
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
        id=stop_id, name=name, longitude=longitude, latitude=latitude, is_station=True
    )


def parse_schedule(gtfs_static_file: GtfsStaticFile):
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
        )

    trip_id_to_trip = {}
    for row in gtfs_static_file.trips():
        service_id = row["service_id"]
        if service_id not in service_id_to_service:
            continue
        trip = parse.ScheduledTrip(
            id=row["trip_id"],
            route_id=row["route_id"],
            direction_id=str_to_bool.get(row["direction_id"]),
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
            hour, minute, second = time_string.split(":")
            cache[time_string] = datetime.time(
                hour=int(hour) % 24, minute=int(minute), second=int(second)
            )
        return cache[time_string]

    for row in gtfs_static_file.stop_times():
        trip_id = row["trip_id"]
        if trip_id not in trip_id_to_trip:
            continue
        stop_time = parse.ScheduledTripStopTime(
            stop_id=row["stop_id"],
            stop_sequence=int(row["stop_sequence"]),
            departure_time=time_string_to_datetime_time(row["departure_time"]),
            arrival_time=time_string_to_datetime_time(row["arrival_time"]),
        )
        trip_id_to_trip[trip_id].stop_times.append(stop_time)

    yield from service_id_to_service.values()
