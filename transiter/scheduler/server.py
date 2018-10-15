from transiter.database.accessobjects import FeedDao
feed_dao = FeedDao


class AutoUpdater:
    def __init__(self, feed_pri_key, frequency):
        self.feed_pri_key = feed_pri_key
        self.frequency = frequency
        self.job = None
        # Start the job

    def set_frequency(self, frequency):
        if frequency == self.frequency:
            return False
        # Adjust the job

    def __del__(self):
        # Finish the job
        pass


feed_pri_key_to_auto_updater = {}


def refresh_jobs():

    feeds = feed_dao.list_all()
    stale_feed_pri_keys = set(feed_pri_key_to_auto_updater.keys())
    for feed in feeds:
        if not feed.auto_updater_enabled:
            continue
        frequency = feed.auto_updater_frequency
        auto_updater = feed_pri_key_to_auto_updater.get(feed.id, None)
        if auto_updater is not None:
            auto_updater.set_frequency(frequency)
        else:
            auto_updater = AutoUpdater(feed.id, frequency)
            feed_pri_key_to_auto_updater[feed.id] = auto_updater
        stale_feed_pri_keys.remove(feed.id)

    for feed_pri_key in stale_feed_pri_keys:
        del feed_pri_key_to_auto_updater[feed_pri_key]


"""
Store the current autoupdate settings with references to the
    relevant jobs
Have a refresh_jobs() functions
This consults the database -> Pull in all the feeds and sees
which ones have autoupdaters
Sees if any jobs have been added or changed
If so it reschedules these and updates its internal store



We can just use a memory scheduler as this server handles the persistence

from transiter import feedservice
feedservice.create_feed_update(system_id, feed_id)
"""
