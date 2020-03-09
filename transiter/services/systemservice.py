"""
The system service is used to install, delete and retrieve information about
(transit) systems.
"""

import json
import logging
import uuid

from transiter import models, exceptions
from transiter.data import dbconnection
from transiter.data.dams import systemdam
from transiter.executor import celeryapp
from transiter.scheduler import client
from transiter.services import links, systemconfigreader, constants as c
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
            system_response[c.HREF] = links.SystemEntityLink(system)
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
            response[c.ERROR] = json.loads(system.error_message)
        return response
    response.update(
        {
            **system.to_dict(),
            c.STOPS: {c.COUNT: systemdam.count_stops_in_system(system_id)},
            c.ROUTES: {c.COUNT: systemdam.count_routes_in_system(system_id)},
            c.FEEDS: {c.COUNT: systemdam.count_feeds_in_system(system_id)},
            "agency_alerts": [
                alert.to_large_dict()
                for alert in systemdam.list_all_alerts_associated_to_system(system.pk)
            ],
        }
    )
    if return_links:
        entity_type_to_link = {
            c.STOPS: links.StopsInSystemIndexLink(system),
            c.ROUTES: links.RoutesInSystemIndexLink(system),
            c.FEEDS: links.FeedsInSystemIndexLink(system),
        }
        for entity_type, link in entity_type_to_link.items():
            response[entity_type][c.HREF] = link
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
    logger.info("Received system install request for id={}".format(system_id))
    with dbconnection.inline_unit_of_work():
        system = systemdam.get_by_id(system_id)
        if system is not None and system.status == models.System.SystemStatus.ACTIVE:
            return False
    _set_status(system_id, models.System.SystemStatus.INSTALLING)
    try:
        feed_ids_to_update = _install_system_configuration(
            system_id, config_str, extra_settings
        )
        for feed_id in feed_ids_to_update:
            feed_update_pk = updatemanager.create_feed_update(system_id, feed_id)
            update_status, __ = updatemanager.execute_feed_update(feed_update_pk)
            if update_status != models.FeedUpdate.Status.SUCCESS:
                raise exceptions.InstallError(
                    message="Failed to update feed with id={}; reason: {}".format(
                        feed_id, update_status
                    )
                )
        _set_status(system_id, models.System.SystemStatus.ACTIVE)
        client.refresh_tasks()
        return feed_ids_to_update
    except exceptions.TransiterException as e:
        _set_status(
            system_id,
            models.System.SystemStatus.INSTALL_FAILED,
            json.dumps(e.response()),
        )
        raise e
    except Exception as e:
        _set_status(
            system_id,
            models.System.SystemStatus.INSTALL_FAILED,
            json.dumps(exceptions.UnexpectedError(str(e)).response()),
        )
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
def _install_system_configuration(system_id, config_str, extra_settings):
    system_config = systemconfigreader.read(config_str, extra_settings)

    system = systemdam.get_by_id(system_id)
    if system is None:
        system = systemdam.create()
        system.id = system_id
    system.status = system.SystemStatus.INSTALLING
    system.name = system_config[systemconfigreader.NAME]
    system.raw_config = config_str

    # Service maps must come first in case calculations are triggered
    # by install_required feed updates
    _install_service_map_configuration(
        system, system_config[systemconfigreader.SERVICE_MAPS]
    )
    return _install_feed_configuration(system, system_config[systemconfigreader.FEEDS])


def delete_by_id(system_id, error_if_not_exists=True, sync=True):
    """
    Delete a transit system
    """
    with dbconnection.inline_unit_of_work():
        system = systemdam.get_by_id(system_id)
        if system is not None:
            system.status = models.System.SystemStatus.DELETING
            if not sync:
                system.id = system.id + "_deleting_" + str(uuid.uuid4())
                system_id = system.id
        elif error_if_not_exists:
            raise exceptions.IdNotFoundError
        else:
            return
    client.refresh_tasks()

    if sync:
        _complete_delete_operation(system_id)
    else:
        _complete_delete_operation_async.delay(system_id)


@celeryapp.app.task
def _complete_delete_operation_async(system_id):
    return _complete_delete_operation(system_id)


def _complete_delete_operation(system_id):
    feed_ids = set()
    with dbconnection.inline_unit_of_work():
        system = systemdam.get_by_id(system_id)
        for feed in system.feeds:
            feed_ids.add(feed.id)

    for feed_id in feed_ids:
        updatemanager.execute_feed_update(
            updatemanager.create_feed_flush(system_id, feed_id)
        )

    with dbconnection.inline_unit_of_work():
        systemdam.delete_by_id(system_id)


def _install_feed_configuration(system, feeds_config):
    """
    Install feeds. This method persists feeds in the databases and then
    performs feed updates for those feeds whose update is required for
    install.

    :param system: the system in install the service maps in
    :type system: models.System
    :param feeds_config: the feeds config from the system config file
    """
    session = dbconnection.get_session()
    for feed in system.feeds:
        session.delete(feed)
    session.flush()
    feed_ids_to_update = list()
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
        feed_ids_to_update.append(feed.id)
    return feed_ids_to_update


def _install_service_map_configuration(system, service_maps_config):
    """
    Install service maps.

    :param system: the system in install the service maps in
    :type system: models.System
    :param service_maps_config: the service maps config
    """
    session = dbconnection.get_session()
    for service_map_groups in system.service_map_groups:
        session.delete(service_map_groups)
    session.flush()
    for id_, config in service_maps_config.items():
        group = models.ServiceMapGroup()
        group.id = id_
        group.system = system
        group.source = config[systemconfigreader.SOURCE]
        json_conditions = config.get(systemconfigreader.CONDITIONS)
        if json_conditions is not None:
            group.conditions = json.dumps(json_conditions, indent=2)
        group.threshold = config[systemconfigreader.THRESHOLD]
        group.use_for_routes_at_stop = config[systemconfigreader.USE_FOR_ROUTES_AT_STOP]
        group.use_for_stops_in_route = config[systemconfigreader.USE_FOR_STOPS_IN_ROUTE]
