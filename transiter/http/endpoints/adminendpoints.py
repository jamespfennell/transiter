"""
Admin

These endpoints are used for administering the Transiter instance.
"""
import logging
from flask import Blueprint

from transiter.db import dbconnection
from transiter.executor.celeryapp import app as celery_app
from transiter.http.httpmanager import http_endpoint, HttpMethod
from transiter.http.permissions import requires_permissions, PermissionsLevel
from transiter.scheduler import client

admin_endpoints = Blueprint(__name__, __name__)

logger = logging.getLogger(__name__)


@http_endpoint(admin_endpoints, "health")
@requires_permissions(PermissionsLevel.ADMIN_READ)
def health():
    """
    Transiter health status

    Return Transiter's health status.
    This describes whether or not the scheduler and executor cluster are up.
    """
    scheduler_response = client.ping()
    if scheduler_response is None:
        scheduler_up = False
        scheduler_num_tasks = None
    else:
        scheduler_up = True
        scheduler_num_tasks = len(scheduler_response)
    num_celery_workers = len(celery_app.control.ping(timeout=0.25))
    celery_up = num_celery_workers > 0
    return {
        "up": celery_up and scheduler_up,
        "services": {
            "scheduler": {"up": scheduler_up, "num_update_tasks": scheduler_num_tasks},
            "executor": {"up": celery_up, "num_workers": num_celery_workers},
        },
    }


@http_endpoint(admin_endpoints, "scheduler")
@requires_permissions(PermissionsLevel.ADMIN_READ)
def scheduler_ping():
    """
    List scheduler tasks

    List all tasks that are currently being scheduled by the scheduler.

    This contains the feed auto update tasks as well as the cron task that trims old feed updates.
    """
    return client.ping()


@http_endpoint(admin_endpoints, "scheduler", method=HttpMethod.POST)
@requires_permissions(PermissionsLevel.ALL)
def scheduler_refresh_tasks():
    """
    Refresh scheduler tasks

    When this endpoint is hit the scheduler inspects the database and ensures that the right tasks are being scheduled
    and with the right periodicity, etc.
    This process happens automatically when an event occurs that
    potentially requires the tasks list to be changed, like a system install or delete.
    This endpoint is designed for the case when an admin manually edits something in the database and
    wants the scheduler to reflect that edit.
    """
    return client.refresh_tasks()


@http_endpoint(admin_endpoints, "upgrade", method=HttpMethod.POST)
@requires_permissions(PermissionsLevel.ALL)
def upgrade_database():
    """
    Upgrade database

    Upgrades the Transiter database to the schema/version associated to
    the Transiter version of the webservice.
    This endpoint is used during Transiter updates: after first updating
    the Python code (or Docker contains), this endpoint can be hit to
    upgrade the database schema.
    It has the same effect as the terminal command:

        transiterclt db upgrade

    """
    return dbconnection.upgrade_database()
