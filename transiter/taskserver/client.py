"""
The task server client module is used by the HTTP server to talk with the task server.
"""
import logging

import rpyc

from transiter import config

logger = logging.getLogger(__name__)


def refresh_tasks():
    """
    Refresh the task server's task list.
    """
    return _run("refresh_tasks")


def update_feed(feed_pk):
    """
    Perform a feed update using the task server.

    :param feed_pk: the feed's PK
    :return:
    """
    return _run("update_feed", feed_pk)


def _run(func_name, *args, **kwargs):
    try:
        conn = rpyc.connect(config.TASKSERVER_HOST, config.TASKSERVER_PORT)
        func = getattr(conn.root, func_name)
        return func(*args, **kwargs)
    except:
        logger.info("Could not connect to the Transiter task server")
    return False
