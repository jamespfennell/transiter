"""
The system service is used to install, delete and retrieve information about
(transit) systems.
"""

import json
import logging

from transiter import models, exceptions
from transiter.data import dbconnection
from transiter.data.dams import systemdam, feeddam
from transiter.services import links, systemconfigreader
from transiter.services.update import updatemanager
from transiter.scheduler import client

logger = logging.getLogger(__name__)


@dbconnection.unit_of_work
def list_all(return_links=True):
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
def get_by_id(system_id, return_links=True):
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
        "agency_alerts": [
            alert.long_repr()
            for alert in systemdam.list_all_alerts_associated_to_system(system.pk)
        ],
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


def install(system_id, config_str, extra_settings):
    install_success = install_uow(system_id, config_str, extra_settings)
    client.refresh_tasks()
    return install_success


@dbconnection.unit_of_work
def install_uow(system_id, config_str, extra_settings):
    if systemdam.get_by_id(system_id) is not None:
        return False

    system_config = systemconfigreader.read(config_str, extra_settings)

    system = systemdam.create()
    system.id = system_id
    system.name = system_config[systemconfigreader.NAME]
    system.raw_config = config_str

    # Service maps must come first in case calculations are triggered
    # by install_required feed updates
    _install_service_maps(system, system_config[systemconfigreader.SERVICE_MAPS])
    _install_feeds(system, system_config[systemconfigreader.FEEDS])
    return True


def delete_by_id(system_id, error_if_not_exists=True):
    """
    Delete a transit system

    :param system_id: the ID of the system
    :type system_id: str
    :return: whether the delete succeeded
    :rtype: bool
    """
    stop_auto_updating_tasks(system_id)
    client.refresh_tasks()
    deleted = delete_by_id_uow(system_id)
    if not deleted and error_if_not_exists:
        raise exceptions.IdNotFoundError
    return True


@dbconnection.unit_of_work
def stop_auto_updating_tasks(system_id):
    feeds = feeddam.list_all_in_system(system_id)
    for feed in feeds:
        feed.auto_update_on = False


@dbconnection.unit_of_work
def delete_by_id_uow(system_id):
    return systemdam.delete_by_id(system_id)


def _install_feeds(system, feeds_config):
    """
    Install feeds. This method persists feeds in the databases and then
    performs feed updates for those feeds whose update is required for
    install.

    :param system: the system in install the service maps in
    :type system: models.System
    :param feeds_config: the feeds config from the system config file
    """

    for id_, config in feeds_config.items():
        feed = models.Feed()
        feed.id = id_
        feed.system = system
        feed.built_in_parser = config[systemconfigreader.PARSER].get(
            systemconfigreader.BUILT_IN
        )
        feed.custom_parser = config[systemconfigreader.PARSER].get(
            systemconfigreader.CUSTOM
        )
        feed.url = config[systemconfigreader.HTTP][systemconfigreader.URL]
        feed.headers = json.dumps(
            dict(config[systemconfigreader.HTTP][systemconfigreader.HEADERS])
        )
        feed.auto_update_on = config[systemconfigreader.AUTO_UPDATE][
            systemconfigreader.ENABLED
        ]
        feed.auto_update_period = config[systemconfigreader.AUTO_UPDATE][
            systemconfigreader.PERIOD
        ]

        if not config[systemconfigreader.REQUIRED_FOR_INSTALL]:
            continue
        feed_update = models.FeedUpdate(feed)
        updatemanager.execute_feed_update(feed_update)
        if feed_update.status != feed_update.Status.SUCCESS:
            raise exceptions.InstallError("Update failed!")


def _install_service_maps(system, service_maps_config):
    """
    Install service maps.

    :param system: the system in install the service maps in
    :type system: models.System
    :param service_maps_config: the service maps config
    """
    for id_, config in service_maps_config.items():
        group = models.ServiceMapGroup()
        group.id = id_
        group.system = system
        group.source = config[systemconfigreader.SOURCE]
        json_conditions = config.get(systemconfigreader.CONDITIONS)
        if json_conditions is not None:
            print(json_conditions)
            group.conditions = json.dumps(json_conditions, indent=2)
        group.threshold = config[systemconfigreader.THRESHOLD]
        group.use_for_routes_at_stop = config[systemconfigreader.USE_FOR_ROUTES_AT_STOP]
        group.use_for_stops_in_route = config[systemconfigreader.USE_FOR_STOPS_IN_ROUTE]
