import requests
import hashlib
from transiter.data import database
from transiter.data.dams import feeddam, routedam, stopdam
from transiter import models
import time
import logging
import importlib
import traceback

from . import gtfsrealtimeutil, gtfsstaticutil, tripupdater

logger = logging.getLogger(__name__)
"""
Some tests:


    def _test_execute_feed_update_success(self):
        self.feed_update_one.raw_data_hash = 'HASH1'

        feedservice._execute_feed_update(self.feed_update_two)

        self.assertEqual(self.feed_update_two.status, 'SUCCESS')
        self.module.custom_function.assert_called_once_with(
            self.feed_one, self.request.content)

    def _test_execute_feed_update_not_needed(self):
        self.feed_update_one.raw_data_hash = 'HASH2'

        feedservice._execute_feed_update(self.feed_update_two)

        self.assertEqual(self.feed_update_two.status, 'SUCCESS')
        self.module.custom_function.assert_not_called()

    def _test_execute_feed_update_failure(self):
        self.feed_update_one.raw_data_hash = 'HASH1'
        self.module.custom_function.side_effect = Exception

        feedservice._execute_feed_update(self.feed_update_two)

        self.assertEqual(self.feed_update_two.status, 'FAILURE')
        self.module.custom_function.assert_called_once_with(
            self.feed_one, self.request.content)
"""

class InvalidParser(ValueError):
    pass


class DownloadError(Exception):
    pass


def execute_feed_update(feed_update, content=None):
    start_time = time.time()
    _execute_feed_update_helper(feed_update, content)
    feed_update.execution_duration = time.time() - start_time
    log_prefix = '[{}/{}]'.format(
        feed_update.feed.system.id,
        feed_update.feed.id
    )
    logger.debug(
        '{} Feed update for took {} seconds'.format(
            log_prefix,
            feed_update.execution_duration
        )
    )


def _execute_feed_update_helper(feed_update, content=None):
    feed = feed_update.feed
    feed_update.status = 'IN_PROGRESS'

    try:
        parser = _get_parser(feed)
    except InvalidParser as invalid_parser:
        feed_update.status = 'FAILURE'
        feed_update.explanation = 'INVALID_PARSER'
        feed_update.failure_message = str(invalid_parser)
        return

    if content is None:
        try:
            content = _get_content(feed)
        except requests.RequestException as download_error:
            feed_update.status = 'FAILURE'
            feed_update.explanation = 'DOWNLOAD_ERROR'
            feed_update.failure_message = str(download_error)
            return

    content_hash = _calculate_content_hash(content)
    feed_update.raw_data_hash = content_hash
    last_successful_update = feeddam.get_last_successful_update(feed.pk)
    if (
        last_successful_update is not None and
        last_successful_update.raw_data_hash == feed_update.raw_data_hash
    ):
        feed_update.status = 'SUCCESS'
        feed_update.explanation = 'NOT_NEEDED'
        return

    try:
        parser(feed, content)
    except Exception:
        feed_update.status = 'FAILURE'
        feed_update.explanation = 'PARSE_ERROR'
        feed_update.failure_message = str(traceback.format_exc())
        logger.debug('Feed parse error:\n' + feed_update.failure_message)
        return

    feed_update.status = 'SUCCESS'
    feed_update.explanation = 'UPDATED'


def _get_parser(feed):
    parser_str = feed.parser
    builtin_parser = _builtin_parser_id_to_parser.get(parser_str, None)
    if builtin_parser is not None:
        return builtin_parser

    colon_char = parser_str.find(':')
    if colon_char == -1:
        raise InvalidParser(
            'Custom parser specifier must be of the form module:method'
        )
    module_str = parser_str[:colon_char]
    method_str = parser_str[colon_char+1:]

    try:
        module = _import_module(module_str)
    except ModuleNotFoundError:
        raise InvalidParser('Unknown module \'{}\''.format(module_str))

    try:
        return getattr(module, method_str)
    except AttributeError:
        raise InvalidParser('Module \'{}\' has no method \'{}\'.'.format(
            module_str, method_str))


def _import_module(module_str, invalidate_caches=False):
    try:
        return importlib.import_module(module_str)
    except ModuleNotFoundError:
        if invalidate_caches:
            return _import_module(module_str, invalidate_caches=True)
        else:
            raise


def _get_content(feed):
    request = requests.get(feed.url)
    request.raise_for_status()
    return request.content


def _calculate_content_hash(content):
    m = hashlib.md5()
    m.update(content)
    return m.hexdigest()


# TODO: move to gtfsrealtimeutil.py? Yes yes yes
def _gtfs_realtime_parser(feed, content):

    gtfs_data = gtfsrealtimeutil.read_gtfs_realtime(content)
    (__, __, trips) = gtfsrealtimeutil.transform_to_transiter_structure(
        gtfs_data, 'America/New_York')
    tripupdater.sync_trips(feed.system, None, trips)





def _parse_gtfs_static(feed, gtfs_static_zip_data):
    system = feed.system

    gtfs_static_parser = gtfsstaticutil.GtfsStaticParser()
    gtfs_static_parser.parse_from_zip_data(gtfs_static_zip_data)

    for route in gtfs_static_parser.route_id_to_route.values():
        route.system = system

    stop_id_to_station_id = {}

    # next 3 bits: Construct larger stations using transfers.txt
    # TODO: make a separate method in the GTFS parser or stopgraphmanager.py
    station_sets_by_stop_id = {}
    for stop in gtfs_static_parser.stop_id_to_stop.values():
        stop.system = system
        if not stop.is_station:
            parent_stop = gtfs_static_parser.stop_id_to_stop.get(stop.parent_stop_id, None)
            if parent_stop is None:
                stop.is_station = True
            else:
                stop.parent_stop = parent_stop
        if stop.is_station:
            station_sets_by_stop_id[stop.id] = {stop.id}
        else:
            stop_id_to_station_id[stop.id] = stop.parent_stop.id

    for (stop_id_1, stop_id_2) in gtfs_static_parser.transfer_tuples:
        print(stop_id_1, stop_id_2)
        updated_station_set = station_sets_by_stop_id[stop_id_1].union(
            station_sets_by_stop_id[stop_id_2])
        for stop_id in updated_station_set:
            station_sets_by_stop_id[stop_id] = updated_station_set

    for station_set in station_sets_by_stop_id.values():
        if len(station_set) <= 1:
            continue
        parent_stop = models.Stop()
        child_stops = [gtfs_static_parser.stop_id_to_stop[stop_id] for stop_id in station_set]
        for child_stop in child_stops:
            child_stop.parent_stop = parent_stop
        _lift_stop_properties(parent_stop, child_stops)
        parent_stop.is_station = True
        parent_stop.system = system

        station_set.clear()
    session = database.get_session()
    session.flush()

    route_id_to_pk = routedam.get_id_to_pk_map_in_system(system.id)
    stop_id_to_pk = stopdam.get_id_to_pk_map_in_system(system.id)

    gtfsstaticutil.fast_scheduled_entities_inserter(
        gtfs_static_zip_data,
        system.pk,
        route_id_to_pk,
        stop_id_to_pk,
    )
    session.flush()
    from transiter.services.servicepattern import servicepatternmanager
    servicepatternmanager.calculate_scheduled_service_maps_for_system(system)

    #for service in gtfs_static_parser.service_id_to_service.values():
    #    service.system = system


def _lift_stop_properties(parent_stop, child_stops):

    parent_stop.latitude = sum(float(child_stop.latitude) for child_stop in child_stops)/len(child_stops)
    parent_stop.longitude = sum(float(child_stop.longitude) for child_stop in child_stops)/len(child_stops)

    if parent_stop.id is None:
        child_stop_ids = [child_stop.id for child_stop in child_stops]
        parent_stop.id = '-'.join(sorted(child_stop_ids))

    if parent_stop.name is None:
        child_stop_names = {child_stop.name: 0 for child_stop in child_stops}
        for child_stop in child_stops:
            child_stop_names[child_stop.name] += 1
        max_freq = max(child_stop_names.values())
        most_frequent_names = set()
        for child_stop_name, freq in child_stop_names.items():
            if freq == max_freq:
                most_frequent_names.add(child_stop_name)

        for name in most_frequent_names.copy():
            remove = False
            for other_name in most_frequent_names:
                if name != other_name and name in other_name:
                    remove = True
            if remove:
                most_frequent_names.remove(name)
        parent_stop.name = ' / '.join(sorted(most_frequent_names))



_builtin_parser_id_to_parser = {
    'gtfsrealtime': _gtfs_realtime_parser,
    'gtfsstatic': _parse_gtfs_static,
}

