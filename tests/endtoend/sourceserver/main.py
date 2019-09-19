import os
from flask import Flask, request

app = Flask(__name__)


path_to_content = {}


def route(method):
    decorator_1 = app.route("/", defaults={"path": ""}, methods=[method])
    decorator_2 = app.route("/<path:path>", methods=[method], strict_slashes=False)
    return lambda func: decorator_1(decorator_2(func))


@route("GET")
def get(path):
    if path not in path_to_content:
        return "", 404
    return path_to_content[path], 200


@route("PUT")
def put(path):
    path_to_content[path] = request.data
    return "", 204


@route("DELETE")
def delete(path):
    if path not in path_to_content:
        return "", 404
    del path_to_content[path]
    return "", 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.environ.get("SOURCE_SERVER_PORT", 5001))
