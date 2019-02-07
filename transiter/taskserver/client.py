import logging

import rpyc

logger = logging.getLogger(__name__)


def refresh_tasks():
    return _run('refresh_tasks')


def update_feed(feed_pk):
    return _run('update_feed', feed_pk)


def _run(func_name, *args, **kwargs):
    try:
        conn = rpyc.connect('localhost', 12345)
        func = getattr(conn.root, func_name)
        return func(*args, **kwargs)
    except ConnectionRefusedError:
        logger.warning('Could not connect to the Transiter task server')
    return False