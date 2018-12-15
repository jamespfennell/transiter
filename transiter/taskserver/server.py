from transiter.data.dams import feeddam
from transiter.services import feedservice
import rpyc
from rpyc.utils.server import ThreadedServer
from apscheduler.schedulers.background import BackgroundScheduler


class AutoUpdater:
    def __init__(self, feed, frequency):
        self.feed_pri_key = feed.id
        self.frequency = frequency
        self.job = None
        scheduler.add_job(
            feedservice.create_feed_update,
            'interval',
            seconds=5,
            args=[feed.system.system_id, feed.feed_id])

    def set_frequency(self, frequency):
        if frequency == self.frequency:
            return False
        # Adjust the job

    def __del__(self):
        # Finish the job
        pass


feed_pri_key_to_auto_updater = {}


def refresh_tasks():
    # TODO: NEED go through the feed service.
    #  Maybe list all with autoupdaters
    # This is not in UoW context
    feeds = feeddam.list_all()
    stale_feed_pri_keys = set(feed_pri_key_to_auto_updater.keys())
    for feed in feeds:
        if not feed.auto_updater_enabled:
            continue
        frequency = feed.auto_updater_frequency
        auto_updater = feed_pri_key_to_auto_updater.get(feed.id, None)
        if auto_updater is not None:
            auto_updater.set_frequency(frequency)
        else:
            auto_updater = AutoUpdater(feed, frequency)
            feed_pri_key_to_auto_updater[feed.id] = auto_updater
        stale_feed_pri_keys.discard(feed.id)

    for feed_pri_key in stale_feed_pri_keys:
        del feed_pri_key_to_auto_updater[feed_pri_key]

    print(feed_pri_key_to_auto_updater)
    return True


class TaskServer(rpyc.Service):

    def exposed_refresh_tasks(self):
        refresh_tasks()


if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.start()
    refresh_tasks()
    server = ThreadedServer(TaskServer, port=12345)
    server.start()
