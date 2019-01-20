import logging

import apscheduler.schedulers.background
import rpyc.utils.server

from transiter.services import feedservice

logger = logging.getLogger('transiter')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
logger.addHandler(handler)
formatter = logging.Formatter(
        '%(asctime)s TS %(levelname)-5s [%(module)s] %(message)s')
handler.setFormatter(formatter)


class AutoUpdater:
    def __init__(self, system_id, feed_id, frequency):
        self.frequency = frequency
        self.job = None
        scheduler.add_job(
            feedservice.create_feed_update,
            'interval',
            seconds=frequency,
            args=[system_id, feed_id])

    def set_frequency(self, frequency):
        if frequency == self.frequency:
            return False
        # Adjust the job
        return True

    def __del__(self):
        # Finish the job
        pass


feed_pri_key_to_auto_updater = {}


def refresh_tasks():
    feeds = feedservice.list_all_autoupdating()
    logger.info('Initializing {} feed autoupdate tasks'.format(len(feeds)))
    stale_feed_pri_keys = set(feed_pri_key_to_auto_updater.keys())
    for feed_data in feeds:
        frequency = feed_data['auto_updater_frequency']
        auto_updater = feed_pri_key_to_auto_updater.get(feed_data['pk'], None)
        if auto_updater is not None:
            auto_updater.set_frequency(frequency)
        else:
            auto_updater = AutoUpdater(
                feed_data['system_id'],
                feed_data['id'],
                frequency)
            feed_pri_key_to_auto_updater[feed_data['pk']] = auto_updater
        stale_feed_pri_keys.discard(feed_data['pk'])

    for feed_pri_key in stale_feed_pri_keys:
        del feed_pri_key_to_auto_updater[feed_pri_key]

    return True


class TaskServer(rpyc.Service):

    def exposed_refresh_tasks(self):
        logger.info('Received external refresh tasks command')
        return refresh_tasks()


if __name__ == "__main__":
    logger.info('Launching Transiter task server')
    scheduler = apscheduler.schedulers.background.BackgroundScheduler()
    scheduler.start()
    refresh_tasks()
    server = rpyc.utils.server.ThreadedServer(TaskServer, port=12345)
    server.start()
