import os
import time

from flask import Flask, request

app = Flask(__name__)


path_to_content = {}


@app.route("/", methods=["GET"])
def list_urls():
    return "\n".join(path_to_content.keys())


def random():
    time_hash = str(time.time())
    dict_hash = str(hash(list_urls()))
    full_hash = hex(abs(hash(time_hash + dict_hash)))[2:14]
    return "{:0<12}".format(full_hash)


@app.route("/", methods=["POST"])
def create_url():
    prefix = request.args.get("prefix", "")
    suffix = request.args.get("suffix", "")
    new_path = prefix + random() + suffix
    path_to_content[new_path] = ""
    return new_path


@app.route("/<path:path>", methods=["GET"], strict_slashes=False)
def get(path):
    if path not in path_to_content:
        return "", 404
    return path_to_content[path], 200


@app.route("/<path:path>", methods=["PUT"], strict_slashes=False)
def put(path):
    if path not in path_to_content:
        return "", 404
    path_to_content[path] = request.data
    return "", 204


@app.route("/<path:path>", methods=["DELETE"], strict_slashes=False)
def delete(path):
    if path not in path_to_content:
        return "", 404
    del path_to_content[path]
    return "", 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.environ.get("SOURCE_SERVER_PORT", 5001))
