import logging
import datetime
import random
import apscheduler.schedulers.background
import rpyc.utils.server
import warnings
warnings.simplefilter('default')

def log(*args, **kwargs):
    print('Recieved warning:')
    print(args)

    print(kwargs)
    #raise ValueError
#warnings.showwarning = log
from transiter.services import feedservice

#TODO: catch handle apscheduler warnings about feed updates <- just set the period low to test
#logger = logging.getLogger('apscheduler')
#logger.setLevel(logging.DEBUG)

logger = logging.getLogger('transiter')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)
formatter = logging.Formatter(
        '%(asctime)s TS %(levelname)-5s [%(module)s] %(message)s')
handler.setFormatter(formatter)


scheduler = apscheduler.schedulers.background.BackgroundScheduler()
feed_pk_to_auto_update_task = {}
feed_update_trim_task = None


class Task:
    def __init__(self, func, args, trigger, **job_kwargs):
        self._job = scheduler.add_job(
            func,
            args=args,
            trigger=trigger,
            **job_kwargs,
        )

    def run_now(self):
        self._job.modify(next_run_time=datetime.datetime.now())

    def __del__(self):
        pass
        #self._job.remove()


class IntervalTask(Task):

    def __init__(self, func, args, period):
        #period = 1
        super().__init__(
            func, args, 'interval',
            seconds=period,
            next_run_time=self._calculate_next_run_time(period)
        )

    def set_period(self, period):
        self._job.reschedule(
            'interval',
            seconds=period
        )
        self._job.modify(next_run_time=self._calculate_next_run_time(period))

    @staticmethod
    def _calculate_next_run_time(period):
        return (
            datetime.datetime.now()
            + datetime.timedelta(seconds=period * random.uniform(0, 1))
        )


class CronTask(Task):

    def __init__(self, func, args, **job_kwargs):
        super().__init__(
            func,
            args,
            'cron',
            **job_kwargs
        )


class FeedAutoUpdateTask(IntervalTask):

    def __init__(self, system_id, feed_id, period):
        super().__init__(
            #feedservice.test,
            feedservice.create_feed_update,
            [system_id, feed_id],
            period
        )


def refresh_feed_auto_update_tasks(p=None):
    global feed_pk_to_auto_update_task
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


def launch():
    global feed_update_trim_task, scheduler
    logger.info('Launching Transiter task server')

    logger.info('Launching background scheduler')
    scheduler.start()

    feed_update_trim_task = CronTask(feedservice.trim_feed_updates, [], minute='*/15')
    refresh_feed_auto_update_tasks()

    logger.info('Launching RPyC server')
    server = rpyc.utils.server.ThreadedServer(TaskServer, port=12345)
    server.start()


if __name__ == '__main__':
    launch()
