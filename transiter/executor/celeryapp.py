import logging
import os

from celery import Celery, signals, app

host = os.environ.get("TRANSITER_RABBITMQ_HOST", "127.0.0.1")

app = Celery("transiter", broker="amqp://{}".format(host))


@signals.after_setup_logger.connect
def on_after_setup_logger(**kwargs):
    # These configurations disable the task received at and completed at msgs
    logger = logging.getLogger("celery.worker.strategy")
    logger.propagate = False
    logger = logging.getLogger("celery.app.trace")
    logger.propagate = False


def run(log_level="warning"):
    app.start(argv=["celeryapp", "worker", "-l", log_level])


if __name__ == "__main__":
    run()
