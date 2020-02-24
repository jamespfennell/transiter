"""
The system service is used to install, delete and retrieve information about
(transit) systems.
"""

import json
import logging

from transiter import models, exceptions
from transiter.data import dbconnection
from transiter.data.dams import systemdam, feeddam
from transiter.executor import celeryapp
from transiter.scheduler import client
from transiter.services import links, systemconfigreader
from transiter.services.update import updatemanager

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
        system_response = system.to_dict()
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
    response = system.to_dict()
    if system.status != system.SystemStatus.ACTIVE:
        if system.error_message is not None:
            response["error"] = json.loads(system.error_message)
        return response
    response.update(
        {
            **system.to_dict(),
            "stops": {"count": systemdam.count_stops_in_system(system_id)},
            "routes": {"count": systemdam.count_routes_in_system(system_id)},
            "feeds": {"count": systemdam.count_feeds_in_system(system_id)},
            "agency_alerts": [
                alert.to_large_dict()
                for alert in systemdam.list_all_alerts_associated_to_system(system.pk)
            ],
        }
    )
    if return_links:
        entity_type_to_link = {
            "stops": links.StopsInSystemIndexLink(system),
            "routes": links.RoutesInSystemIndexLink(system),
            "feeds": links.FeedsInSystemIndexLink(system),
        }
        for entity_type, link in entity_type_to_link.items():
            response[entity_type]["href"] = link
    return response


def install_async(system_id, config_str, extra_settings):
    """
    Install a transit system asynchronously.

    This is a no-op if the system is already installed.

    This method first adds the system to the DB with status SCHEDULED. It then queues
    the actual install on the executor cluster.
    """
    with dbconnection.inline_unit_of_work():
        system = systemdam.get_by_id(system_id)
        if system is None:
            system = systemdam.create()
            system.id = system_id
        elif system.status != system.SystemStatus.INSTALL_FAILED:
            return False
        system.status = system.SystemStatus.SCHEDULED

    _execute_install_async.delay(system_id, config_str, extra_settings)
    return True


@celeryapp.app.task
def _execute_install_async(system_id, config_str, extra_settings):
    return install(system_id, config_str, extra_settings)


def install(system_id, config_str, extra_settings):
    """
    Install a transit system synchronously; i.e., in the current thread.

    This is a no-op if the system is already installed.

    This method is designed to be called both in a sync HTTP install request and as
    the main install method called by the executor of a async HTTP install request.

    If the transit system does not have a record in the DB when this method is called
    (as in the sync case), the install will take place in a single unit of work. One
    consequence of this is that if the install failed there will be no record of it
    in the DB.

    Otherwise a number of unit of works will be used to update the systems's status as
    it progresses through the install
    """
    with dbconnection.inline_unit_of_work():
        system = systemdam.get_by_id(system_id)
        if system is not None and system.status == models.System.SystemStatus.ACTIVE:
            return False
    _set_status(system_id, models.System.SystemStatus.INSTALLING)
    try:
        install_success = _execute_install_uow(system_id, config_str, extra_settings)
        client.refresh_tasks()
        return install_success
    except exceptions.TransiterException as e:
        _set_status(
            system_id,
            models.System.SystemStatus.INSTALL_FAILED,
            json.dumps(e.response()),
        )
        raise e
    except Exception as e:
        _set_status(system_id, models.System.SystemStatus.INSTALL_FAILED, str(e))
        raise e


@dbconnection.unit_of_work
def _set_status(system_id, status, error_message=None):
    """
    Set the status of a transit system, if that system exists in the DB.
    """
    system = systemdam.get_by_id(system_id)
    if system is not None:
        system.status = status
        if error_message is not None:
            system.error_message = error_message


@dbconnection.unit_of_work
def _execute_install_uow(system_id, config_str, extra_settings):
    system_config = systemconfigreader.read(config_str, extra_settings)

    system = systemdam.get_by_id(system_id)
    if system is None:
        system = systemdam.create()
        system.id = system_id
    system.status = system.SystemStatus.ACTIVE
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
    """
    # First, stop all of the update tasks for this system.
    with dbconnection.inline_unit_of_work():
        feeds = feeddam.list_all_in_system(system_id)
        for feed in feeds:
            feed.auto_update_on = False
    client.refresh_tasks()

    with dbconnection.inline_unit_of_work():
        deleted = systemdam.delete_by_id(system_id)
    if not deleted and error_if_not_exists:
        raise exceptions.IdNotFoundError

    return True


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
