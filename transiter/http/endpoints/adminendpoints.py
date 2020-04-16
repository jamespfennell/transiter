import logging

from flask import Blueprint

from transiter.executor.celeryapp import app as celery_app
from transiter.http.httpmanager import http_endpoint, HttpMethod
from transiter.http.permissions import requires_permissions, PermissionsLevel
from transiter.scheduler import client

admin_endpoints = Blueprint(__name__, __name__)

logger = logging.getLogger(__name__)


@http_endpoint(admin_endpoints, "health")
@requires_permissions(PermissionsLevel.ADMIN_READ)
def health():
    """Generate a health response."""
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
    return client.ping()


@http_endpoint(admin_endpoints, "scheduler", method=HttpMethod.POST)
@requires_permissions(PermissionsLevel.ALL)
def scheduler_refresh_tasks():
    return client.refresh_tasks()
