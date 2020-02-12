"""
The task server client module is used by the HTTP server to talk with the scheduler.
"""
import logging

import requests

from transiter import config

logger = logging.getLogger(__name__)


def ping():
    """
    Ping the scheduler and, if it is alive, return the number of update tasks.
    """
    try:
        response = requests.get(
            "http://{}:{}".format(config.SCHEDULER_HOST, config.SCHEDULER_PORT),
            timeout=0.25,
        )
        response.raise_for_status()
        return int(response.text)
    except requests.RequestException:
        return None


def refresh_tasks():
    """
    Refresh the scheduler's update task list.
    """
    try:
        response = requests.post(
            "http://{}:{}".format(config.SCHEDULER_HOST, config.SCHEDULER_PORT)
        )
        response.raise_for_status()
        return True
    except requests.RequestException:
        logger.info("Could not connect to the Transiter scheduler")
    return False
