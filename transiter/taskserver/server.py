import logging
import datetime
import random
import apscheduler.schedulers.background
import rpyc.utils.server

from transiter.services import feedservice

#TODO: handle apscheduler warnings about feed updates
#logger = logging.getLogger('apscheduler')
#logger.setLevel(logging.DEBUG)

logger = logging.getLogger('transiter')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
logger.addHandler(handler)
formatter = logging.Formatter(
        '%(asctime)s TS %(levelname)-5s [%(module)s] %(message)s')
handler.setFormatter(formatter)


class Task:
    def __init__(self, func, args, period, start_time_offset=None):
        if start_time_offset is None:
            start_time_offset = period
        self._job = scheduler.add_job(
            func,
            'interval',
            next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=start_time_offset),
            seconds=period,
            args=args
        )

    def set_period(self, period, start_time_offset=None):
        if start_time_offset is None:
            start_time_offset = period
        self._job.reschedule(
            'interval',
            seconds=period
        )
        self._job.modify(next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=start_time_offset))

    def run_now(self):
        self._job.modify(next_run_time=datetime.datetime.now())

    def __del__(self):
        self._job.remove()


class FeedAutoUpdateTask(Task):

    def __init__(self, system_id, feed_id, period):
        super().__init__(
            feedservice.create_feed_update,
            [system_id, feed_id],
            period,
            period * random.uniform(0, 1)
        )

    def set_period(self, period, start_time_offset=None):
        if start_time_offset is None:
            start_time_offset = period * random.uniform(0, 1)
        super().set_period(period, start_time_offset)


feed_pk_to_auto_update_task = {}
feed_update_trim_task = None


def refresh_feed_auto_update_tasks(p=None):
    feeds_data = feedservice.list_all_autoupdating()
    logger.info('Refreshing {} feed auto update tasks'.format(len(feeds_data)))

    stale_feed_pks = set(feed_pk_to_auto_update_task.keys())
    for feed_data in feeds_data:
        period = feed_data['auto_update_period']
        if p is not None:
            period = p
        auto_update_task = feed_pk_to_auto_update_task.get(feed_data['pk'], None)
        if auto_update_task is not None:
            auto_update_task.set_period(period)
        else:
            auto_update_task = FeedAutoUpdateTask(
                feed_data['system_id'],
                feed_data['id'],
                period,
            )
            feed_pk_to_auto_update_task[feed_data['pk']] = auto_update_task
        stale_feed_pks.discard(feed_data['pk'])

    for feed_pk in stale_feed_pks:
        del feed_pk_to_auto_update_task[feed_pk]


class TaskServer(rpyc.Service):

    def exposed_refresh_tasks(self):
        logger.info('Received external refresh tasks command')
        refresh_feed_auto_update_tasks(30)
        return True

    def exposed_update_feed(self, feed_pk):
        auto_update_task = feed_pk_to_auto_update_task.get(feed_pk, None)
        auto_update_task.run_now()


if __name__ == "__main__":
    logger.info('Launching Transiter task server')

    logger.info('Launching background scheduler')
    scheduler = apscheduler.schedulers.background.BackgroundScheduler()
    scheduler.start()

    feed_update_trim_task = Task(feedservice.trim_feed_updates, [], 30*60)
    refresh_feed_auto_update_tasks()

    logger.info('Launching RPyC server')
    server = rpyc.utils.server.ThreadedServer(TaskServer, port=12345)
    server.start()
