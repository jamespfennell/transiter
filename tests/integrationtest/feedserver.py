from flask import Flask, request

app = Flask(__name__)


class Feed:

    content = None
    status = 200

    def get_content(self):
        return self.content

    def set_content(self, new_content):
        self.content = new_content

    def get_status(self):
        return self.status

    def set_status(self, new_status):
        self.status = new_status


feed = Feed()


@app.route("/", methods=["GET"])
def get_feed():
    content = feed.get_content()
    if content is None:
        content = ""
    status = feed.get_status()
    if status is None:
        status = 200
    return content, status, ""


@app.route("/", methods=["PUT"])
def put_feed():
    feed.set_content(request.data)
    feed.set_status(200)
    return ""


@app.route("/", methods=["DELETE"])
def delete_feed():
    feed.set_content(None)
    feed.set_status(404)
    return ""


if __name__ == "__main__":
    app.run(port=5001)
