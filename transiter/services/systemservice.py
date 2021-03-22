"""
The system service is used to install, delete and retrieve information about
(transit) systems.
"""
import datetime
import json
import traceback
import logging
import time
import typing
import uuid
from dataclasses import dataclass
from typing import Iterator

from transiter import exceptions, __metadata__
from transiter.db import dbconnection, models
from transiter.db.queries import feedqueries, genericqueries, systemqueries
from transiter.executor import celeryapp
from transiter.scheduler import client
from transiter.services import systemconfigreader, views, updatemanager

logger = logging.getLogger(__name__)


@dbconnection.unit_of_work
def list_all() -> typing.List[views.System]:
    return list(map(views.System.from_model, systemqueries.list_all()))


@dbconnection.unit_of_work
def get_by_id(system_id) -> views.SystemLarge:
    system = systemqueries.get_by_id(system_id)
    if system is None:
        raise exceptions.IdNotFoundError(models.System, system_id=system_id)
    response = views.SystemLarge.from_model(system)
    if system.status != system.SystemStatus.ACTIVE:
        return response
    for attr, view, relationship in (
        ("agencies", views.AgenciesInSystem, models.System.agencies),
        ("stops", views.StopsInSystem, models.System.stops),
        ("routes", views.RoutesInSystem, models.System.routes),
        ("feeds", views.FeedsInSystem, models.System.feeds),
        ("transfers", views.TransfersInSystem, models.System.transfers),
    ):
        setattr(
            response,
            attr,
            view.from_model(
                system,
                genericqueries.count_number_of_related_entities(relationship, system),
            ),
        )
    return response


@dbconnection.unit_of_work
def is_active(system_id):
    system = systemqueries.get_by_id(system_id)
    return system is not None and system.status != models.System.SystemStatus.ACTIVE


def set_auto_update_enabled(system_id, auto_update):
    with dbconnection.inline_unit_of_work():
        response = systemqueries.set_auto_update_enabled(system_id, auto_update)
    client.refresh_tasks()
    return response


def install(system_id, config_str, extra_settings, config_source_url, sync=True):
    """
    Install a transit system synchronously; i.e., in the current thread.

    This is a no-op if the system is already installed.

    This method is designed to be invoked both in a sync HTTP install request and in
    the executor of a async HTTP install request.

    If the transit system does not have a record in the DB when this method is called
    (as in the sync case), the install will take place in a single unit of work. One
    consequence of this is that if the install fails there will be no record of it
    in the DB.

    Otherwise a number of unit of works will be used to update the systems's status as
    it progresses through the install.
    """
    logger.info("Received system install request for id={}".format(system_id))
    system_update_pk = _create_system_update(
        system_id, config_str, extra_settings, config_source_url
    )
    sync_to_function = {
        True: _execute_system_update,
        False: _execute_system_update_async.delay,
    }
    sync_to_function[sync](system_update_pk)
    return system_update_pk


@dbconnection.unit_of_work
def get_update_by_id(system_update_id) -> views.SystemUpdate:
    system_update = systemqueries.get_update_by_pk(system_update_id)
    if system_update is None:
        raise exceptions.IdNotFoundError(models.SystemUpdate, id=str(system_update_id))
    result = views.SystemUpdate.from_model(system_update)
    result.system = views.System.from_model(system_update.system)
    return result


@dbconnection.unit_of_work
def _create_system_update(system_id, config_str, extra_settings, config_source_url):
    system = systemqueries.get_by_id(system_id)
    if system is not None:
        invalid_statuses_for_update = {
            models.System.SystemStatus.SCHEDULED,
            models.System.SystemStatus.INSTALLING,
            models.System.SystemStatus.DELETING,
        }
        if system.status in invalid_statuses_for_update:
            raise exceptions.InstallError(
                "Cannot install or update system with status '{}'. "
                "If the system is stuck in this state, delete it first to reinstall".format(
                    system.status.name
                )
            )
        elif system.status == models.System.SystemStatus.INSTALL_FAILED:
            system.status = models.System.SystemStatus.SCHEDULED
    else:
        system = models.System(
            id=system_id,
            name="(Awaiting install for full name)",
            status=models.System.SystemStatus.SCHEDULED,
        )
        systemqueries.create(system)

    update = models.SystemUpdate(
        system=system,
        status=models.SystemUpdate.Status.SCHEDULED,
        config_template=config_str,
        config_parameters=json.dumps(extra_settings, indent=2),
        config_source_url=config_source_url,
        transiter_version=__metadata__.__version__,
    )
    dbconnection.get_session().add(update)
    dbconnection.get_session().flush()
    return update.pk


@celeryapp.app.task
def _execute_system_update_async(system_update_pk):
    return _execute_system_update(system_update_pk)


def _execute_system_update(system_update_pk):
    context = _mark_update_started(system_update_pk)

    # Pause all other activity on this system to avoid database concurrency problems
    # during the large upcoming unit of works.
    client.refresh_tasks()

    try:
        feed_ids_to_update, feed_ids_to_delete = _install_system_configuration(
            system_update_pk
        )
        for feed_id in feed_ids_to_update:
            feed_update, exception = updatemanager.execute_feed_update(
                feed_update_pk=updatemanager.create_feed_update(
                    context.system_id, feed_id
                )
            )
            if feed_update.status != models.FeedUpdate.Status.SUCCESS:
                if exception is None:
                    exception = exceptions.InstallError(
                        message=(
                            f"Failed to update feed (id={feed_id}); "
                            f"status: {feed_update.status}; "
                            f"result: {feed_update.result}"
                        )
                    )
                raise exceptions.InstallError(
                    message=(
                        f"Failed to update a feed (id={feed_id}) "
                        f"that is required for install"
                    )
                ) from exception
        for feed_id in feed_ids_to_delete:
            _delete_feed(context.system_id, feed_id)
        _mark_update_completed(
            context, models.SystemUpdate.Status.SUCCESS,
        )
    except Exception:
        _mark_update_completed(
            context, models.SystemUpdate.Status.FAILED, traceback.format_exc()
        )
        logger.debug("Install or update of system failed", exc_info=True)

    client.refresh_tasks()


@dataclass
class _SystemUpdateContext:
    update_pk: int
    system_id: str
    prior_auto_update_setting: bool
    start_time: float


@dbconnection.unit_of_work
def _mark_update_started(system_update_pk) -> _SystemUpdateContext:
    system_update = systemqueries.get_update_by_pk(system_update_pk)
    system_update.status = models.SystemUpdate.Status.IN_PROGRESS
    system = system_update.system
    prior_auto_update_setting = system.auto_update_enabled
    system.auto_update_enabled = False
    if system.status == models.System.SystemStatus.SCHEDULED:
        system.status = models.System.SystemStatus.INSTALLING
    return _SystemUpdateContext(
        update_pk=system_update_pk,
        system_id=system.id,
        prior_auto_update_setting=prior_auto_update_setting,
        start_time=time.time(),
    )


@dbconnection.unit_of_work
def _mark_update_completed(
    context: _SystemUpdateContext, final_status, final_status_message=None,
):
    """
    Set the status of a transit system, if that system exists in the DB.
    """
    system_update = systemqueries.get_update_by_pk(context.update_pk)
    system_update.status = final_status
    system_update.status_message = final_status_message
    system_update.total_duration = time.time() - context.start_time
    system_update.completed_at = datetime.datetime.utcnow()
    system_update.system.auto_update_enabled = context.prior_auto_update_setting
    if system_update.system.status == models.System.SystemStatus.INSTALLING:
        if final_status == models.SystemUpdate.Status.SUCCESS:
            system_update.system.status = models.System.SystemStatus.ACTIVE
        else:
            system_update.system.status = models.System.SystemStatus.INSTALL_FAILED


@dbconnection.unit_of_work
def _install_system_configuration(system_update_pk):
    system_update = systemqueries.get_update_by_pk(system_update_pk)
    extra_settings = json.loads(system_update.config_parameters)
    system_update.config = systemconfigreader.render_template(
        system_update.config_template, extra_settings
    )
    system_config = systemconfigreader.read(system_update.config, extra_settings)
    system = system_update.system
    system.name = system_config[systemconfigreader.NAME]

    # Service maps must come first in case calculations are triggered
    # by install_required feed updates
    _save_service_map_configuration(
        system, system_config[systemconfigreader.SERVICE_MAPS]
    )
    return _save_feed_configuration(system, system_config[systemconfigreader.FEEDS])


def delete_by_id(system_id, error_if_not_exists=True, sync=True):
    """
    Delete a transit system
    """
    with dbconnection.inline_unit_of_work():
        system = systemqueries.get_by_id(system_id)
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

    sync_to_function = {
        True: _complete_delete_operation,
        False: _complete_delete_operation_async.delay,
    }
    sync_to_function[sync](system_id)


@celeryapp.app.task
def _complete_delete_operation_async(system_id):
    return _complete_delete_operation(system_id)


def _complete_delete_operation(system_id):
    feed_ids = set()
    with dbconnection.inline_unit_of_work():
        system = systemqueries.get_by_id(system_id)
        for feed in system.feeds:
            feed_ids.add(feed.id)

    for feed_id in feed_ids:
        _delete_feed(system_id, feed_id)

    with dbconnection.inline_unit_of_work():
        systemqueries.delete_by_id(system_id)


def _delete_feed(system_id, feed_id):
    logger.info("Deleting feed {}/{}".format(system_id, feed_id))
    updatemanager.execute_feed_update(
        updatemanager.create_feed_flush(system_id, feed_id)
    )
    with dbconnection.inline_unit_of_work():
        feedqueries.delete_in_system_by_id(system_id, feed_id)


def _save_feed_configuration(system, feeds_config):
    """
    Save feeds in a system.

    Stale feed maps -- those that are currently attached to the system but that
    do not correspond to entries in the config -- are *not* deleted by this method.

    :param system: the system to save the service maps in
    :param feeds_config: the feeds config JSON blob
    :return: a two-tuple of feed ID collections; the first collection contains IDs for
     feeds that need to be updated and the second for feeds that need to be deleted
    """
    feed_id_to_pk = genericqueries.get_id_to_pk_map(models.Feed, system.pk)
    session = dbconnection.get_session()
    feed_ids_to_update = list()
    for feed in _build_feeds_from_config(feeds_config):
        feed.system_pk = system.pk
        if feed.id in feed_id_to_pk:
            feed.pk = feed_id_to_pk[feed.id]
            del feed_id_to_pk[feed.id]
            logger.info("Updating feed {}/{}".format(system.id, feed.id))
        else:
            logger.info("Creating feed {}/{}".format(system.id, feed.id))
        session.merge(feed)
        if not feed.required_for_install:
            continue
        feed_ids_to_update.append(feed.id)

    feed_ids_to_delete = list(feed_id_to_pk.keys())
    return feed_ids_to_update, feed_ids_to_delete


def _build_feeds_from_config(feeds_config) -> Iterator[models.Feed]:
    for id_, config in feeds_config.items():
        feed = models.Feed()
        feed.id = id_
        feed.built_in_parser = config[systemconfigreader.PARSER].get(
            systemconfigreader.BUILT_IN
        )
        feed.custom_parser = config[systemconfigreader.PARSER].get(
            systemconfigreader.CUSTOM
        )
        parser_options = config[systemconfigreader.PARSER].get(
            systemconfigreader.OPTIONS
        )
        feed.parser_options = (
            json.dumps(parser_options, indent=2) if parser_options is not None else None
        )
        feed.url = config[systemconfigreader.HTTP][systemconfigreader.URL]
        feed.headers = json.dumps(
            dict(config[systemconfigreader.HTTP][systemconfigreader.HEADERS]), indent=2
        )
        feed.http_timeout = config[systemconfigreader.HTTP].get(
            systemconfigreader.TIMEOUT
        )
        feed.auto_update_enabled = config[systemconfigreader.AUTO_UPDATE][
            systemconfigreader.ENABLED
        ]
        feed.auto_update_period = config[systemconfigreader.AUTO_UPDATE][
            systemconfigreader.PERIOD
        ]
        feed.required_for_install = config[systemconfigreader.REQUIRED_FOR_INSTALL]
        yield feed


def _save_service_map_configuration(system, service_maps_config):
    """
    Save service maps in a system.

    Stale service maps -- those that are currently attached to the system but that
    do not correspond to entries in the config -- are deleted.

    :param system: the system to save the service maps in
    :param service_maps_config: the service maps config JSON blob
    """
    group_id_to_existing_service_map_group = {
        service_map_group.id: service_map_group
        for service_map_group in system.service_map_groups
    }
    session = dbconnection.get_session()
    for service_map_group in _build_service_maps_from_config(service_maps_config):
        service_map_group.system_pk = system.pk
        existing_service_map_group = group_id_to_existing_service_map_group.get(
            service_map_group.id
        )
        if existing_service_map_group is not None:
            service_map_group.pk = existing_service_map_group.pk
            del group_id_to_existing_service_map_group[service_map_group.id]
            logger.info(
                "Updating service map {}/{}".format(system.id, service_map_group.id)
            )
        else:
            logger.info(
                "Creating service map {}/{}".format(system.id, service_map_group.id)
            )
        session.merge(service_map_group)

    for existing_service_map_group in group_id_to_existing_service_map_group.values():
        logger.info(
            "Deleting service map {}/{}".format(
                system.id, existing_service_map_group.id
            )
        )
        session.delete(existing_service_map_group)


def _build_service_maps_from_config(
    service_maps_config,
) -> Iterator[models.ServiceMapGroup]:
    for id_, config in service_maps_config.items():
        group = models.ServiceMapGroup()
        group.id = id_
        group.source = config[systemconfigreader.SOURCE]
        json_conditions = config.get(systemconfigreader.CONDITIONS)
        if json_conditions is not None:
            group.conditions = json.dumps(json_conditions, indent=2)
        else:
            group.conditions = None
        group.threshold = config[systemconfigreader.THRESHOLD]
        group.use_for_routes_at_stop = config[systemconfigreader.USE_FOR_ROUTES_AT_STOP]
        group.use_for_stops_in_route = config[systemconfigreader.USE_FOR_STOPS_IN_ROUTE]
        yield group
