"""
Transiter Scheduler

The scheduler is a Python process that runs tasks periodically using APScheduler. It
has a HTTP interface that enables a Transiter webserver to communicate with it.
"""
import collections
import datetime
import json
import logging
import random
import time
import typing

import apscheduler.schedulers.background
import flask
import inflection
import prometheus_client as prometheus
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from transiter.executor import celeryapp
from transiter.scheduler import metrics
from transiter.services import feedservice

logger = logging.getLogger("transiter")


scheduler = apscheduler.schedulers.background.BackgroundScheduler(
    executors={"default": {"type": "threadpool", "max_workers": 20}}
)


class Schedule:
    def job_kwargs(self):
        raise NotImplementedError

    def json(self):
        return {
            "type": inflection.underscore(self.__class__.__name__)[:-9].upper(),
            "parameters": {key[1:]: value for key, value in vars(self).items()},
        }

    def __repr__(self):
        return ",".join(
            sorted("{}={}".format(*item) for item in self.job_kwargs().items())
        )

    def __eq__(self, other):
        return isinstance(other, Schedule) and str(self) == str(other)


class PeriodicSchedule(Schedule):
    def __init__(self, period):
        self._period = period

    @property
    def period(self):
        return self._period

    def job_kwargs(self):
        return {
            "trigger": "interval",
            "seconds": self._period,
            "next_run_time": self._calculate_next_run_time(self._period),
        }

    @staticmethod
    def _calculate_next_run_time(period):
        return datetime.datetime.now() + datetime.timedelta(
            seconds=period * random.uniform(0, 1)
        )


class CronSchedule(Schedule):
    def __init__(self, minute):
        self._minute = minute

    def job_kwargs(self):
        return {"trigger": "cron", "minute": self._minute}


class Task:
    def __init__(self):
        self._schedule: typing.Optional[Schedule] = None
        self._job = None

    def run(self):
        raise NotImplementedError

    @property
    def schedule(self):
        return self._schedule

    @schedule.setter
    def schedule(self, schedule: typing.Optional[Schedule]):
        if self._schedule == schedule:
            return
        if self._schedule is not None:
            self._job.remove()
        self._schedule = schedule
        if schedule is None:
            return
        self._job = scheduler.add_job(self.run, **schedule.job_kwargs())

    def json(self):
        return {
            "type": inflection.underscore(self.__class__.__name__)[:-5].upper(),
            "parameters": {
                key[1:]: value
                for key, value in vars(self).items()
                if key not in {"_job", "_schedule"}
            },
            "schedule": self._schedule.json() if self._schedule is not None else None,
        }


class FeedAutoUpdateTask(Task):
    def __init__(self, system_id, feed_id):
        self._system_id = system_id
        self._feed_id = feed_id
        super().__init__()

    def run(self):
        expires = (
            self.schedule.period * 0.8
            if isinstance(self.schedule, PeriodicSchedule)
            else None
        )
        # NOTE: access the task like a static method to avoid the current instance
        # being unnecessarily being sent through RabbitMQ.
        logger.info("Triggering task update %s/%s", self._system_id, self._feed_id)
        FeedAutoUpdateTask._create_feed_update.apply_async(
            args=(None, self._system_id, self._feed_id), expires=expires
        )

    @celeryapp.app.task
    def _create_feed_update(self, system_id, feed_id):
        return feedservice.create_and_execute_feed_update(
            system_id, feed_id, execute_async=False
        )


class TrimFeedUpdatesTask(Task):
    def __init__(self):
        super().__init__()
        self.schedule = CronSchedule(minute="*/15")

    def run(self):
        # NOTE: access the task like a static method to avoid the current instance
        # being unnecessarily being sent through RabbitMQ.
        TrimFeedUpdatesTask._trim_feed_updates.delay(None)

    @celeryapp.app.task
    def _trim_feed_updates(self):
        return feedservice.trim_feed_updates()


class Registry:
    def initialize(self):
        while True:
            try:
                self.refresh()
            except SQLAlchemyError:
                logger.info(
                    "Failed to connect to the database; trying again in 1 second."
                )
                time.sleep(1)
                continue
            except Exception as e:
                logger.exception("Unexpected error", e)
                exit(1)
            break

    def refresh(self):
        raise NotImplementedError

    def all_tasks(self):
        raise NotImplementedError


class FeedAutoUpdateRegistry(Registry):
    def __init__(self):
        self._system_id_to_feed_id_to_task: typing.Dict[
            str, typing.Dict[str, FeedAutoUpdateTask]
        ] = collections.defaultdict(lambda: {})

    def refresh(self):
        stale_feed_keys = set(self._current_feed_keys())
        for feed in feedservice.list_all_auto_updating():
            task = self._system_id_to_feed_id_to_task[feed.system.id].get(feed.id)
            if task is None:
                logger.info("Adding {}/{}".format(feed.system.id, feed.id))
                task = FeedAutoUpdateTask(feed.system.id, feed.id)
                self._system_id_to_feed_id_to_task[feed.system.id][feed.id] = task
            else:
                logger.info("Updating {}/{}".format(feed.system.id, feed.id))
            task.schedule = PeriodicSchedule(feed.auto_update_period)
            stale_feed_keys.discard((feed.system.id, feed.id))

        for system_id, feed_id in stale_feed_keys:
            logger.info("Removing {}/{}".format(system_id, feed_id))
            feed_id_to_task = self._system_id_to_feed_id_to_task[system_id]
            feed_id_to_task[feed_id].schedule = None
            feed_id_to_task.pop(feed_id)
            if len(feed_id_to_task) == 0:
                del self._system_id_to_feed_id_to_task[system_id]

    def all_tasks(self):
        for feed_id_to_task in self._system_id_to_feed_id_to_task.values():
            yield from feed_id_to_task.values()

    def _current_feed_keys(self):
        for system_id, feed_id_to_task in self._system_id_to_feed_id_to_task.items():
            for feed_id in feed_id_to_task.keys():
                yield system_id, feed_id


class TransiterRegistry(Registry):
    def __init__(self):
        self._tasks = []

    def refresh(self):
        if len(self._tasks) > 0:
            return
        self._tasks = [TrimFeedUpdatesTask()]

    def all_tasks(self):
        return self._tasks


feed_auto_update_registry = FeedAutoUpdateRegistry()
transiter_registry = TransiterRegistry()
metrics_populator = metrics.MetricsPopulator()


def app_ping():
    logger.info("Received external ping via HTTP")
    return json.dumps(
        [
            task.json()
            for registry in [feed_auto_update_registry, transiter_registry]
            for task in registry.all_tasks()
        ],
        indent=2,
    )


def app_refresh_tasks():
    logger.info("Received external refresh tasks command via HTTP")
    feed_auto_update_registry.refresh()
    metrics_populator.refresh()
    return "", 204


def app_feed_update_callback():
    # TODO: add a time.sleep and verify that this is blocking
    error_message = metrics_populator.report(flask.request.json)
    if error_message is None:
        return "", 200
    logger.info(error_message)
    return error_message, 400  # bad request


def create_app():
    app = flask.Flask(__name__)
    app.add_url_rule("/", "ping", app_ping, methods=["GET"])
    app.add_url_rule("/", "refresh_tasks", app_refresh_tasks, methods=["POST"])
    app.add_url_rule(
        "/feed_update_callback",
        "feed_update_callback",
        app_feed_update_callback,
        methods=["POST"],
    )
    # Add prometheus wsgi middleware to route /metrics requests
    app.wsgi_app = DispatcherMiddleware(
        app.wsgi_app, {"/metrics": prometheus.make_wsgi_app()}
    )

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    formatter = logging.Formatter(
        "%(asctime)s TS %(levelname)-5s [%(module)s] %(message)s"
    )
    handler.setFormatter(formatter)

    logger.info("Launching scheduler")
    scheduler.start()
    feed_auto_update_registry.initialize()
    transiter_registry.initialize()
    metrics_populator.refresh()

    logger.info("Launching HTTP server")
    return app
