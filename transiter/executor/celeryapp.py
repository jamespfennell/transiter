import os

from celery import Celery

host = os.environ.get("TRANSITER_RABBITMQ_HOST", "127.0.0.1")

app = Celery("transiter", broker="amqp://{}".format(host))


def run(log_level="warning"):
    app.start(argv=["celeryapp", "worker", "-l", log_level])


if __name__ == "__main__":
    run()
