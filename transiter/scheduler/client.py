"""
The scheduler client module is used to talk with the scheduler.
"""
import logging

import requests

from transiter import config
import json

logger = logging.getLogger(__name__)


def ping():
    """
    Ping the scheduler.

    If it cannot be reached return None; otherwise, return a JSON representation of the
    tasks that are currently being scheduled.
    """
    try:
        response = requests.get(
            "http://{}:{}".format(config.SCHEDULER_HOST, config.SCHEDULER_PORT),
            timeout=0.25,
        )
        response.raise_for_status()
        return json.loads(response.text)
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
