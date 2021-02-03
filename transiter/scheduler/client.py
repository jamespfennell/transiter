"""
The scheduler client module is used to talk with the scheduler.
"""
import json
import logging

import requests

from transiter import config

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
            "http://{}:{}".format(config.SCHEDULER_HOST, config.SCHEDULER_PORT),
            timeout=2,  # These requests are important so we allow a longer timeout
        )
        response.raise_for_status()
        return True
    except requests.RequestException:
        logger.info("Could not connect to the Transiter scheduler")
    return False


def feed_update_callback(feed_pk, status, result, entity_type_to_num_in_db):
    """
    Send a message to the scheduler that a feed update has completed
    """
    try:
        requests.post(
            "http://{}:{}/feed_update_callback".format(
                config.SCHEDULER_HOST, config.SCHEDULER_PORT
            ),
            json={
                "feed_pk": feed_pk,
                "status": status.name,
                "result": result.name,
                "entity_type_to_count": entity_type_to_num_in_db,
            },
            timeout=0.25,
        )
    except requests.RequestException:
        pass


def metrics():
    """
    Return the Prometheus metrics from the scheduler
    """
    return requests.get(
        "http://{}:{}/metrics".format(config.SCHEDULER_HOST, config.SCHEDULER_PORT),
        timeout=0.25,
    ).text
