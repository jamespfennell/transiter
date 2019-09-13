import docker

from contextlib import contextmanager


@contextmanager
def source_server():
    image, __ = client.images.build(path="sourceserver")
    server = None
    try:
        server = client.containers.run(
            image.id, name="sourceserver", network=network, detach=True
        )
        yield server
    finally:
        try:
            server.kill()
            server.remove()
        except AttributeError:
            pass


client = docker.from_env()
# TODO: allow container reference to be specified by env variable
web_server = client.containers.get("transiter-webserver")
web_server.exec_run(["transiterclt", "rebuild-db", "--yes"])

network = list(web_server.attrs["NetworkSettings"]["Networks"].keys())[0]
transiter_port = list(web_server.attrs["NetworkSettings"]["Ports"].values())[0][0][
    "HostPort"
]

with source_server():
    image, __ = client.images.build(path="runner")
    container = client.containers.run(image.id, network=network, detach=True)
    for line in container.logs(stream=True):
        print(line.strip().decode("utf-8"))

    exit(container.wait()["StatusCode"])
