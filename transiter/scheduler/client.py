"""
The task server client module is used by the HTTP server to talk with the task server.
"""
import logging

import requests

from transiter import config

logger = logging.getLogger(__name__)


def refresh_tasks():
    """
    Refresh the task server's task list.
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
