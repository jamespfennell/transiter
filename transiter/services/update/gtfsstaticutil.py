"""
The GTFS Static Util contains the logic for reading feeds of this format.

The official reference is here: https://gtfs.org/reference/static
"""

import csv
import datetime
import enum
import io
import zipfile

from transiter import models
from transiter.data import fastoperations
from transiter.data.dams import routedam, stopdam, genericqueries
from transiter.services.servicemap import servicemapmanager


def parse_gtfs_static(feed_update, gtfs_static_zip_data):
    """
    Parse a GTFS Static feed

    :param feed_update: the feed update
    :param gtfs_static_zip_data: raw binary GTFS static zip data
    """
    system = feed_update.feed.system

    gtfs_static_data = GtfsStaticData()
    gtfs_static_data.parse_from_zip_data(gtfs_static_zip_data)

    for route in gtfs_static_data.route_id_to_route.values():
        route.system = system

    stop_id_to_station_id = {}
    station_sets_by_stop_id = {}
    for stop in gtfs_static_data.stop_id_to_stop.values():
        stop.system = system
        if not stop.is_station:
            parent_stop = gtfs_static_data.stop_id_to_stop.get(
                stop.parent_stop_id, None
            )
            if parent_stop is None:
                stop.is_station = True
            else:
                stop.parent_stop = parent_stop
        if stop.is_station:
            station_sets_by_stop_id[stop.id] = {stop.id}
        else:
            stop_id_to_station_id[stop.id] = stop.parent_stop.id

    for (stop_id_1, stop_id_2) in gtfs_static_data.transfer_tuples:
        updated_station_set = station_sets_by_stop_id[stop_id_1].union(
            station_sets_by_stop_id[stop_id_2]
        )
        for stop_id in updated_station_set:
            station_sets_by_stop_id[stop_id] = updated_station_set

    for station_set in station_sets_by_stop_id.values():
        if len(station_set) <= 1:
            continue
        child_stops = [
            gtfs_static_data.stop_id_to_stop[stop_id] for stop_id in station_set
        ]
        parent_stop = _create_station_from_child_stops(child_stops)
        parent_stop.system = system
        station_set.clear()

    fast_scheduled_entities_insert(gtfs_static_zip_data, system)

    servicemapmanager.calculate_scheduled_service_maps_for_system(system)


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
    parent_stop = models.Stop()
    for child_stop in child_stops:
        child_stop.parent_stop = parent_stop
    parent_stop.is_station = True

    parent_stop.latitude = sum(
        float(child_stop.latitude) for child_stop in child_stops
    ) / len(child_stops)
    parent_stop.longitude = sum(
        float(child_stop.longitude) for child_stop in child_stops
    ) / len(child_stops)

    child_stop_ids = [child_stop.id for child_stop in child_stops]
    parent_stop.id = "-".join(sorted(child_stop_ids))

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
    parent_stop.name = " / ".join(sorted(most_frequent_names))

    return parent_stop


class GtfsStaticFile(enum.Enum):
    CALENDAR = "calendar.txt"
    ROUTES = "routes.txt"
    STOP_TIMES = "stop_times.txt"
    STOPS = "stops.txt"
    TRANSFERS = "transfers.txt"
    TRIPS = "trips.txt"


def read_gtfs_static_file(zip_file, gtfs_static_file):
    """
    Read a GTFS static file

    :param zip_file: the zip file IO reader
    :param gtfs_static_file: which static file to real
    :return: iterator of dictionaries for each row
    """
    file_name = gtfs_static_file.value
    try:
        with zip_file.open(file_name) as raw_csv_file:
            csv_file = io.TextIOWrapper(raw_csv_file, "utf-8")
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                yield row
    except KeyError:
        return []


class GtfsStaticData:
    """
    Object to parse GTFS static data and store the data as Transiter models

    In general, it does not parse the huge data sets (stop_times.txt) as
    converting these to Transiter models is too expensive. Instead those
    entities are persisted to the database using the fast updater.
    """

    def __init__(self):
        self._zip_file = None
        self.route_id_to_route = {}
        self.stop_id_to_stop = {}
        self.service_id_to_service = {}
        self.trip_id_to_trip = {}
        self.transfer_tuples = []

    def parse_from_zip_data(self, zip_data):
        """
        Parse data

        :param zip_data: binary zip data
        :return: nothing. Data is accessed in the class.
        """
        self._zip_file = zipfile.ZipFile(io.BytesIO(zip_data))
        self._parse_routes()
        self._parse_stops()
        self._parse_transfers()

    def _parse_routes(self):
        for row in read_gtfs_static_file(self._zip_file, GtfsStaticFile.ROUTES):
            route = models.Route()
            route.id = row["route_id"]
            route.color = row.get("route_color")
            route.url = row.get("route_url")
            route.short_name = row.get("route_short_name")
            route.long_name = row.get("route_long_name")
            route.description = row.get("route_desc")
            self.route_id_to_route[route.id] = route

    def _parse_stops(self):
        for row in read_gtfs_static_file(self._zip_file, GtfsStaticFile.STOPS):
            stop = models.Stop()
            stop.id = row["stop_id"]
            stop.name = row["stop_name"]
            stop.longitude = row["stop_lon"]
            stop.latitude = row["stop_lat"]

            if row["location_type"] == "1":
                stop.is_station = True
                stop.parent_stop_id = None
                self.stop_id_to_stop[stop.id] = stop
                continue
            stop.is_station = False
            stop.parent_stop_id = row.get("parent_station", None)
            self.stop_id_to_stop[stop.id] = stop

    def _parse_transfers(self):
        for row in read_gtfs_static_file(self._zip_file, GtfsStaticFile.TRANSFERS):
            stop_id_1 = row["from_stop_id"]
            stop_id_2 = row["to_stop_id"]
            if stop_id_1 == stop_id_2:
                continue
            self.transfer_tuples.append((stop_id_1, stop_id_2))


def fast_scheduled_entities_insert(gtfs_static_zip_data, system: models.System):
    """
    This function syncs scheduled entities (services, trips and stop times)
    with the DB by executing a broad SQL DELETE query, and then
    manually constructing and executing three SQL INSERT queries. In a typical
    GTFS static feed there can be hundreds of thousands of scheduled entities;
    by bypassing SQL Alchemy in this specific case, the GTFS static parser can
    be made much more performant. For the NYC Subway GTFS static data, this
    function reduces this step from about 3 minutes to about 20 seconds.

    This is only really possible because other
    Transiter entities do not rely on scheduled entities, so performing a full
    DELETE followed by INSERT does not corrupt any foreign key references.

    :param gtfs_static_zip_data: binary data
    :param system: the system
    :return:
    """
    route_id_to_pk = routedam.get_id_to_pk_map_in_system(system.id)
    stop_id_to_pk = stopdam.get_id_to_pk_map_in_system(system.id)
    zip_file = zipfile.ZipFile(io.BytesIO(gtfs_static_zip_data))
    str_to_bool = {"0": False, "1": True}

    fast_inserter = fastoperations.FastInserter(models.ScheduledService)
    for row in read_gtfs_static_file(zip_file, GtfsStaticFile.CALENDAR):
        fast_inserter.add(
            {
                "id": row["service_id"],
                "system_pk": system.pk,
                "monday": str_to_bool[row["monday"]],
                "tuesday": str_to_bool[row["tuesday"]],
                "wednesday": str_to_bool[row["wednesday"]],
                "thursday": str_to_bool[row["thursday"]],
                "friday": str_to_bool[row["friday"]],
                "saturday": str_to_bool[row["saturday"]],
                "sunday": str_to_bool[row["sunday"]],
            }
        )
    fast_inserter.flush()

    service_id_to_pk = genericqueries.get_id_to_pk_map(models.ScheduledService)

    fast_inserter = fastoperations.FastInserter(models.ScheduledTrip)
    for row in read_gtfs_static_file(zip_file, GtfsStaticFile.TRIPS):
        direction_id = str_to_bool[row["direction_id"]]
        fast_inserter.add(
            {
                "id": row["trip_id"],
                "service_pk": service_id_to_pk[row["service_id"]],
                "route_pk": route_id_to_pk[row["route_id"]],
                "direction_id": direction_id,
            }
        )
    fast_inserter.flush()
    trip_id_to_pk = genericqueries.get_id_to_pk_map(models.ScheduledTrip)

    def time_str_to_datetime_time(time_str):
        hour, minute, second = time_str.split(":")
        return datetime.time(
            hour=int(hour) % 24, minute=int(minute), second=int(second)
        )

    fast_inserter = fastoperations.FastInserter(models.ScheduledTripStopTime)
    for row in read_gtfs_static_file(zip_file, GtfsStaticFile.STOP_TIMES):
        fast_inserter.add(
            {
                "trip_pk": trip_id_to_pk[row["trip_id"]],
                "stop_pk": stop_id_to_pk[row["stop_id"]],
                "stop_sequence": int(row["stop_sequence"]),
                "departure_time": time_str_to_datetime_time(row["departure_time"]),
                "arrival_time": time_str_to_datetime_time(row["arrival_time"]),
            }
        )
    fast_inserter.flush()
