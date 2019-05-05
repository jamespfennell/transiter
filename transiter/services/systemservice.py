"""
The system service is used to install, delete and retrieve information about
(transit) systems.
"""

import csv
import importlib
import json
import logging

import pytimeparse
import toml

from transiter import models, exceptions
from transiter.data import dbconnection
from transiter.data.dams import systemdam, stopdam
from transiter.services import links
from transiter.services.update import updatemanager
from transiter.taskserver import client

logger = logging.getLogger(__name__)


@dbconnection.unit_of_work
def list_all(return_links=False):
    """
    List all installed systems.
    
    :param return_links: whether to return links
    :type return_links: bool
    :return: A list dictionaries, one for each system, containing the system's
             short representation and optionally its link.
    :rtype: list
    """
    response = []
    for system in systemdam.list_all():
        system_response = system.short_repr()
        if return_links:
            system_response["href"] = links.SystemEntityLink(system)
        response.append(system_response)
    return response


@dbconnection.unit_of_work
def get_by_id(system_id, return_links=False):
    """
    Get information on a specific system.

    :param system_id: the system ID
    :type system_id: str
    :param return_links: whether to return links
    :type return_links: bool
    :return: a dictionary containing the system's short representation, and
             three sub-dictionaries for stops, routes, and feeds. Each
             sub-dictionary contains the number of such entities in the system,
             and optionally a link to a list of such entities.
    """
    system = systemdam.get_by_id(system_id)
    if system is None:
        raise exceptions.IdNotFoundError
    response = {
        **system.short_repr(),
        "stops": {"count": systemdam.count_stops_in_system(system_id)},
        "routes": {"count": systemdam.count_routes_in_system(system_id)},
        "feeds": {"count": systemdam.count_feeds_in_system(system_id)},
    }
    if return_links:
        entity_type_to_link = {
            "stops": links.StopsInSystemIndexLink(system),
            "routes": links.RoutesInSystemIndexLink(system),
            "feeds": links.FeedsInSystemIndexLink(system),
        }
        for entity_type, link in entity_type_to_link.items():
            response[entity_type]["href"] = link
    return response


def install(system_id, config_str, extra_files, extra_settings):
    """
    Install a Transit system.

    :param system_id: the ID of the system
    :type system_id: str
    :param config_str: the system's TOML config in a string.
    :type config_str: str
    :param extra_files: a dictionary of file name to file stream for extra
                        files provided for this install.
    :type extra_files: dict
    :param extra_settings: a dictionary of setting name to value for extra
                           settings provided for this install
    :type extra_settings: dict
    :return: whether the install succeeded
    :rtype: bool
    """
    install_success = install_uow(system_id, config_str, extra_files, extra_settings)
    client.refresh_tasks()
    return install_success


@dbconnection.unit_of_work
def install_uow(system_id, config_str, extra_files, extra_settings):
    """
    Perform the DB actions neccesary to install a Transit system.
    """
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


@dbconnection.unit_of_work
def delete_by_id(system_id):
    """
    Delete a tranist system

    :param system_id: the ID of the system
    :type system_id: str
    :return: whether the delete succeeded
    :rtype: bool
    """
    deleted = systemdam.delete_by_id(system_id)
    if not deleted:
        raise exceptions.IdNotFoundError
    return True


class _SystemConfig:
    """
    Object to store system configuration. This is populated from the system's
    TOML configuration file.
    """

    class InvalidSystemConfig(exceptions.InvalidInput):
        """
        Exception thrown if the system config TOML file is invalid.
        """

        pass

    class FeedConfig:
        """
        Simple object to store feed configuration.
        """

        feed = None
        required_for_install = False
        file_upload_fallback = None

        def __init__(self, feed_id, raw_dict, extra_files, extra_settings):
            """
            Initialize a FeedConfig object with data from the raw config.

            :param raw_dict: the raw dictionary of feed settings
            :type raw_dict: dict
            :param extra_files: extra files provided in the system config
            :type extra_files: dict
            :param extra_settings: extra settings provided in the system config
            :type extra_settings: dict
            :raise KeyError: if any of the required feed config settings are
                             missing, or a referenced file is missing.
            """
            self.feed = models.Feed()
            self.feed.id = feed_id
            self.feed.url = raw_dict["url"].format(**extra_settings)
            built_in_parser_string = raw_dict.get("built_in_parser", None)
            if built_in_parser_string is not None:
                self.feed.built_in_parser = models.Feed.BuiltInParser[
                    built_in_parser_string
                ]
            else:
                self.feed.custom_parser = raw_dict["custom_parser"]

            self.required_for_install = raw_dict.get("required_for_install", False)
            if self.required_for_install:
                file_upload_fallback = raw_dict.get("file_upload_fallback", None)
                if (
                    file_upload_fallback is not None
                    and file_upload_fallback in extra_files
                ):
                    self.file_upload_fallback = extra_files[
                        raw_dict["file_upload_fallback"]
                    ]

            self.feed.auto_update_on = raw_dict.get("auto_update", False)
            if self.feed.auto_update_on:
                auto_update_time_str = raw_dict["auto_update_period"]
                self.feed.auto_update_period = pytimeparse.parse(auto_update_time_str)
                logger.info(
                    f'Converted string "{auto_update_time_str}" '
                    f"to {self.feed.auto_update_period} seconds."
                )
            else:
                self.feed.auto_update_on = False
                self.feed.auto_update_period = None

    class ServiceMapConfig:
        """
        Simple object to store service map configuration. Because all of the
        user config maps to columns in the ServiceMapGroup object, we just
        create the object here.
        """

        service_map_group = None

        def __init__(self, group_id, raw_dict):
            """
            Initialize a SystemMapConfig object with data from the raw config.

            :param raw_dict: the raw dictionary of feed settings
            :type raw_dict: dict
            :raise ValueError: if any of the required config settings are
                               missing.
            """
            self.service_map_group = models.ServiceMapGroup()
            self.service_map_group.id = group_id
            self.service_map_group.source = self.service_map_group.ServiceMapSource[
                raw_dict["source"].upper()
            ]
            if "conditions" in raw_dict:
                self.service_map_group.conditions = json.dumps(raw_dict["conditions"])
            else:
                self.service_map_group.conditions = None
            self.service_map_group.threshold = raw_dict.get("threshold", 0)
            self.service_map_group.use_for_routes_at_stop = raw_dict.get(
                "use_for_routes_at_stop", False
            )
            self.service_map_group.use_for_stops_in_route = raw_dict.get(
                "use_for_stops_in_route", False
            )

    feeds = None
    service_maps = None
    direction_name_files = None

    def __init__(self, config_str, extra_files, extra_settings):
        """
        Initialize a SystemConfig object with data from the raw config.

        :param config_str: the TOML configuration in a string
        :type config_str: str
        :param extra_files: extra files provided in the system config
        :type extra_files: dict
        :param extra_settings: extra settings provided in the system config
        :type extra_settings: dict
        :raise InvalidSystemConfig: if the TOML config is invalid, or references
                                    non-existent files or settings.
        """
        config = toml.loads(config_str)

        required_packages = set(config.get("prerequisites", {}).get("packages", {}))
        for required_package in required_packages:
            if importlib.util.find_spec(required_package) is None:
                raise self.InvalidSystemConfig(
                    "Missing required package: {}".format(required_package)
                )

        required_settings = set(config.get("prerequisites", {}).get("settings", {}))
        required_settings.difference_update(extra_settings.keys())
        if len(required_settings) > 0:
            raise self.InvalidSystemConfig(
                "Missing required settings {}".format(",".join(required_settings))
            )

        self.feeds = [
            self.FeedConfig(feed_id, raw_dict, extra_files, extra_settings)
            for feed_id, raw_dict in config.get("feeds", {}).items()
        ]

        self.service_maps = [
            self.ServiceMapConfig(group_id, raw_dict)
            for group_id, raw_dict in config.get("service_maps", {}).items()
        ]

        self.direction_name_files = []
        for file_key in config.get("direction_names", {}).get("file_uploads", []):
            self.direction_name_files.append(extra_files[file_key])


def _install_feeds(system, system_config):
    """
    Install feeds. This method persists feeds in the databases and then
    performs feed updates for those feeds whose update is required for
    install.

    :param system: the system in install the service maps in
    :type system: models.System
    :param system_config: the system config
    :type system_config: _SystemConfig
    """

    for feed_config in system_config.feeds:

        feed_config.feed.system = system

        if not feed_config.required_for_install:
            continue
        feed_update = models.FeedUpdate(feed_config.feed)
        updatemanager.execute_feed_update(feed_update)
        if feed_update.status == feed_update.Status.SUCCESS:
            continue

        if feed_config.file_upload_fallback is None:
            raise exceptions.InstallError("Update failed!")
        feed_update_retry = models.FeedUpdate(feed_config.feed)
        updatemanager.execute_feed_update(
            feed_update_retry, feed_config.file_upload_fallback
        )
        if feed_update_retry.status == feed_update.Status.SUCCESS:
            continue
        raise exceptions.InstallError("Update failed!")


def _install_service_maps(system, system_config):
    """
    Install service maps.

    :param system: the system in install the service maps in
    :type system: models.System
    :param system_config: the system config
    :type system_config: _SystemConfig
    """
    for service_map_config in system_config.service_maps:
        service_map_config.service_map_group.system = system


def _install_direction_names(system, system_config):
    """
    Install direction names.

    :param system: the system in install the direction names in
    :type system: models.System
    :param system_config: the system config
    :type system_config: _SystemConfig
    """
    # For the moment, assume direction names involve a full reset
    direction_name_files = system_config.direction_name_files
    stop_id_to_stop = {stop.id: stop for stop in stopdam.list_all_in_system(system.id)}
    priority = 0
    for direction_name_file in direction_name_files:
        csv_reader = csv.DictReader(
            line.decode("utf-8") for line in direction_name_file.readlines()
        )
        for row in csv_reader:
            stop = stop_id_to_stop.get(row["stop_id"], None)
            if stop is None:
                continue
            direction_id = row.get("direction_id", None)
            if direction_id is not None:
                direction_id = direction_id == "0"
            direction_name_rule = models.DirectionNameRule()
            direction_name_rule.stop = stop
            direction_name_rule.priority = priority
            direction_name_rule.direction_id = direction_id
            direction_name_rule.track = row.get("track", None)
            direction_name_rule.name = row["direction_name"]
            priority += 1
