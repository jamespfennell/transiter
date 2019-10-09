from contextlib import contextmanager

import docker

# .... should all of this just be done with docker compose?


@contextmanager
def source_server():
    print("Building the source server Docker image")
    image, __ = client.images.build(path="sourceserver")
    server = None
    try:
        print("Launching the source server")
        server = client.containers.run(
            image.id, name="sourceserver", network=network, detach=True
        )
        yield server
    finally:
        try:
            print("Stopping the source server")
            server.kill()
            server.remove()
        except AttributeError:
            pass


print("Initializing Docker client")
client = docker.from_env()
print("Resetting the database")
web_server = client.containers.get("transiter-webserver")
web_server.exec_run(["transiterclt", "rebuild-db", "--yes"])

network = list(web_server.attrs["NetworkSettings"]["Networks"].keys())[0]
print("Transiter is running on the Docker network: {}".format(network))
transiter_port = list(web_server.attrs["NetworkSettings"]["Ports"].values())[0][0][
    "HostPort"
]
print("Transiter is running on the Docker network port: {}".format(transiter_port))

with source_server():
    print("Building the test driver Docker image")
    image, __ = client.images.build(path="driver")
    print("Running the test driver Docker container")
    container = client.containers.run(image.id, network=network, detach=True)
    for line in container.logs(stream=True):
        print(line.strip().decode("utf-8"))

    exit_code = container.wait()["StatusCode"]

if exit_code == 0:
    print("Test passed")
else:
    print("Test failed")
exit(exit_code)
