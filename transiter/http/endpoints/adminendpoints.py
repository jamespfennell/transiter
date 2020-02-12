import logging

from flask import Blueprint

from transiter.scheduler import client
from transiter.executor.celeryapp import app as celery_app
from transiter.http.httpmanager import http_endpoint
from transiter.http.permissions import requires_permissions, PermissionsLevel

admin_endpoints = Blueprint(__name__, __name__)

logger = logging.getLogger(__name__)


@http_endpoint(admin_endpoints, "health")
@requires_permissions(PermissionsLevel.ADMIN_READ)
def health():
    """Generate a health response."""
    num_scheduler_update_tasks = client.ping()
    scheduler_up = num_scheduler_update_tasks is not None
    num_celery_workers = len(celery_app.control.ping(timeout=0.25))
    celery_up = num_celery_workers > 0
    return {
        "up": celery_up and scheduler_up,
        "services": {
            "scheduler": {
                "up": scheduler_up,
                "num_update_tasks": num_scheduler_update_tasks,
            },
            "executor": {"up": celery_up, "num_workers": num_celery_workers},
        },
    }
