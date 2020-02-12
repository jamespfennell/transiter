"""
Transiter Task Server

The task server is Python process that runs tasks periodically using APScheduler. It
has an RPyC interface that enables a Transiter HTTP server to communicate with it.
"""
import datetime
import logging
import random
import time

import apscheduler.schedulers.background
import flask

from transiter.executor import celeryapp
from transiter.services import feedservice

logger = logging.getLogger("transiter")


scheduler = apscheduler.schedulers.background.BackgroundScheduler(
    executors={"default": {"type": "threadpool", "max_workers": 20}}
)

feed_pk_to_auto_update_task = {}
feed_update_trim_task = None


class Task:
    def __init__(self, func, args, trigger, **job_kwargs):
        self._job = scheduler.add_job(func, args=args, trigger=trigger, **job_kwargs)

    def run_now(self):
        self._job.modify(next_run_time=datetime.datetime.now())

    def __del__(self):
        self._job.remove()


class IntervalTask(Task):
    def __init__(self, func, args, period):
        super().__init__(
            func,
            args,
            "interval",
            seconds=period,
            next_run_time=self._calculate_next_run_time(period),
        )

    def set_period(self, period):
        self._job.reschedule("interval", seconds=period)
        self._job.modify(next_run_time=self._calculate_next_run_time(period))

    @staticmethod
    def _calculate_next_run_time(period):
        return datetime.datetime.now() + datetime.timedelta(
            seconds=period * random.uniform(0, 1)
        )


class CronTask(Task):
    def __init__(self, func, args, **job_kwargs):
        super().__init__(func, args, "cron", **job_kwargs)


@celeryapp.app.task
def create_feed_update(*args, **kwargs):
    return feedservice.create_feed_update(*args, **kwargs)


class FeedAutoUpdateTask(IntervalTask):
    def __init__(self, system_id, feed_id, period):
        super().__init__(create_feed_update.delay, [system_id, feed_id], period)


def refresh_feed_auto_update_tasks():
    """
    Refresh the task server's registry of auto update tasks.
    """
    global feed_pk_to_auto_update_task
    feeds_data = feedservice.list_all_auto_updating()
    logger.info("Refreshing {} feed auto update tasks".format(len(feeds_data)))

    stale_feed_pks = set(feed_pk_to_auto_update_task.keys())
    for feed_data in feeds_data:
        period = feed_data["auto_update_period"]
        auto_update_task = feed_pk_to_auto_update_task.get(feed_data["pk"], None)
        if auto_update_task is not None:
            auto_update_task.set_period(period)
        else:
            auto_update_task = FeedAutoUpdateTask(
                feed_data["system_id"], feed_data["id"], period
            )
            feed_pk_to_auto_update_task[feed_data["pk"]] = auto_update_task
        stale_feed_pks.discard(feed_data["pk"])

    logger.info("Cancelling {} feed auto update tasks".format(len(stale_feed_pks)))
    for feed_pk in stale_feed_pks:
        del feed_pk_to_auto_update_task[feed_pk]


def initialize_feed_auto_update_tasks():

    while True:
        try:
            refresh_feed_auto_update_tasks()
            return
        except:
            logger.info("Failed to update tasks; trying again in 1 second.")
            time.sleep(1)


@celeryapp.app.task
def trim_feed_updates(*args, **kwargs):
    return feedservice.trim_feed_updates()


def create_app():
    """
    Launch the task server.
    """

    app = flask.Flask(__name__)

    @app.route("/", methods=["GET"])
    def ping():
        logger.info("Received external ping (HTTP)")
        return str(len(feed_pk_to_auto_update_task))

    @app.route("/", methods=["POST"])
    def refresh_tasks():
        logger.info("Received external refresh tasks command (HTTP)")
        refresh_feed_auto_update_tasks()
        return "", 204

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    formatter = logging.Formatter(
        "%(asctime)s TS %(levelname)-5s [%(module)s] %(message)s"
    )
    handler.setFormatter(formatter)
    logger.info("Launching Transiter task server")

    logger.info("Launching background scheduler")
    global feed_update_trim_task, scheduler
    scheduler.start()
    feed_update_trim_task = CronTask(trim_feed_updates.delay, [], minute="*/15")
    initialize_feed_auto_update_tasks()

    logger.info("Launching RPyC server")
    return app
