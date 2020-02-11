from celery import Celery
import os

host = os.environ.get("TRANSITER_RABBITMQ_HOST", "127.0.0.1")

app = Celery("transiter", broker="amqp://{}".format(host))


def run():
    app.start(argv=["celeryapp", "worker", "-l", "info"])


if __name__ == "__main__":
    run()
