import csv
import logging

import json
import pytimeparse
import toml

from transiter import models
from transiter.data import database
from transiter.data.dams import systemdam, stopdam
from transiter.general import linksutil, exceptions
from transiter.services.update import updatemanager

logger = logging.getLogger(__name__)


@database.unit_of_work
def list_all():
    """
    List all installed systems.
    :return: A list of short representation of systems
    """
    response = []
    for system in systemdam.list_all():
        system_response = system.short_repr()
        print(system_response)
        system_response.update({
            'href': linksutil.SystemEntityLink(system)
        })
        response.append(system_response)
    return response


@database.unit_of_work
def get_by_id(system_id):
    system = systemdam.get_by_id(system_id)
    if system is None:
        raise exceptions.IdNotFoundError

    from transiter.services.servicepattern import servicepatternmanager
    servicepatternmanager.calculate_scheduled_service_maps_for_system(system)

    response = system.short_repr()
    response.update({
        "stops": {
            "count": systemdam.count_stops_in_system(system_id),
            "href": linksutil.StopsInSystemIndexLink(system)
        },
        "routes": {
            "count": systemdam.count_routes_in_system(system_id),
            "href": linksutil.RoutesInSystemIndexLink(system)
        },
        "feeds": {
            "count": systemdam.count_feeds_in_system(system_id),
            "href": linksutil.FeedsInSystemIndexLink(system)
        }
    })
    return response


@database.unit_of_work
def install(system_id, config_str, extra_files, extra_settings):
    if systemdam.get_by_id(system_id) is not None:
        return False

    system = systemdam.create()
    system.id = system_id
    system_config = _SystemConfig(config_str, extra_files, extra_settings)
    # Service maps must come first in case calculations are triggered
    # by install_required feed updates
    _install_service_maps(system, system_config)
    _install_feeds(system, system_config)
    _install_direction_names(system, system_config)
    return True


@database.unit_of_work
def delete_by_id(system_id):
    deleted = systemdam.delete_by_id(system_id)
    if not deleted:
        raise exceptions.IdNotFoundError
    return True


class _SystemConfig:

    def __init__(self, config_str, extra_files, extra_settings):

        config = toml.loads(config_str)

        # TODO: Verify packages are available

        required_settings = set(config.get('prerequisites', {}).get('settings', {}))
        required_settings.difference_update(extra_settings.keys())
        if len(required_settings) > 0:
            raise Exception('Invalid config')

        self.feeds = config.get('feeds', {})
        print(self.feeds)
        for feed_id, feed in self.feeds.items():
            print('here', feed)
            feed['url'] = (feed['url']).format(**extra_settings)

            file_upload_fallback = feed.get('file_upload_fallback', None)
            if 'required_for_install' in feed:
                if file_upload_fallback is not None:
                    feed['file_upload_fallback'] = extra_files[file_upload_fallback]
            else:
                feed['required_for_install'] = False

            if 'auto_update' in feed:
                auto_update_time_str = feed['auto_update_period']
                feed['auto_update_period'] = pytimeparse.parse(auto_update_time_str)
                logger.info(
                    f'Converted string "{auto_update_time_str}" '
                    f'to {feed["auto_update_period"]} seconds.')
            else:
                feed['auto_update'] = False

        self.service_maps = config.get('service_maps', {})
        for service_map_id, service_map in self.service_maps.items():
            if 'conditions' in service_map:
                service_map['conditions'] = json.dumps(service_map['conditions'])
            else:
                service_map['conditions'] = None
            service_map.setdefault('threshold', 0)
            service_map.setdefault('use_for_routes_at_stop', False)
            service_map.setdefault('use_for_stops_in_route', False)

        self.direction_name_files = []
        for file_key in config.get('direction_names', {}).get('file_uploads', []):
            self.direction_name_files.append(
                extra_files[file_key]
            )


def _install_feeds(system, system_config):

    for feed_id, feed_config in system_config.feeds.items():
        # make this a bulk_get_or_create(system_id, feed_ids)
        # ... but still need to delete old ones...maybe through reassigning
        # system.feeds? Yes
        feed = models.Feed()
        feed.system = system
        feed.id = feed_id
        feed.url = feed_config['url']
        feed.parser = feed_config['parser']
        feed.auto_updater_enabled = feed_config['auto_update']
        feed.auto_updater_frequency = feed_config['auto_update_period']

        if not feed_config['required_for_install']:
            continue
        feed_update = models.FeedUpdate(feed)
        updatemanager.execute_feed_update(feed_update)
        if feed_update.status != 'SUCCESS':
            raise ValueError('Update failed!')
        # TODO: check if successful and if not, try again with the local feed


def _install_service_maps(system, system_config):
    for service_map_id, service_map_config in system_config.service_maps.items():

        service_map_group = models.ServiceMapGroup()
        service_map_group.system = system
        service_map_group.id = service_map_id
        for field in [
            'source', 'conditions', 'threshold', 'use_for_routes_at_stop',
            'use_for_stops_in_route'
        ]:
            service_map_group.__setattr__(field, service_map_config[field])


def _install_direction_names(system, system_config):
    # For the moment, assume direction names involve a full reset
    direction_name_files = system_config.direction_name_files
    stop_id_to_stop = {
        stop.id: stop for stop in stopdam.list_all_in_system(system.id)
    }
    priority = 0
    for direction_name_file in direction_name_files:
        csv_reader = csv.DictReader(
            line.decode('utf-8') for line in direction_name_file.readlines()
        )
        for row in csv_reader:
            stop = stop_id_to_stop.get(row['stop_id'], None)
            if stop is None:
                continue
            direction_id = row.get('direction_id', None)
            if direction_id is not None:
                direction_id = (direction_id == '0')
            direction_name_rule = models.DirectionNameRule()
            direction_name_rule.stop = stop
            direction_name_rule.priority = priority
            direction_name_rule.direction_id = direction_id
            direction_name_rule.track = row.get('track', None)
            direction_name_rule.name = row['direction_name']
            priority += 1


