import builtins
from contextlib import contextmanager
from unittest import mock

import flask
import pytest
import werkzeug.exceptions as werkzeug_exceptions

from transiter import config, exceptions
from transiter.http.endpoints import docsendpoints


@pytest.fixture
def enable_documentation(monkeypatch):
    monkeypatch.setattr(config, "DOCUMENTATION_ENABLED", True)


@pytest.fixture
def flask_current_app(monkeypatch):
    current_app = mock.MagicMock(root_path="")
    monkeypatch.setattr(flask.helpers, "current_app", current_app)
    return current_app


@pytest.fixture
def flask_send_from_directory(monkeypatch):
    class FlaskSendFromDirectory:
        path_to_content = {}

        def send(self, documentation_root, path):
            content = self.path_to_content.get(path)
            if content is None:
                raise werkzeug_exceptions.HTTPException
            return content

    send_from_directory = FlaskSendFromDirectory()
    monkeypatch.setattr(flask, "send_from_directory", send_from_directory.send)
    return send_from_directory


@pytest.fixture
def make_documentation_valid(monkeypatch, enable_documentation):
    monkeypatch.setattr(docsendpoints, "_documentation_root_is_valid", lambda: True)


@pytest.mark.parametrize(
    "path_to_request,path_to_return",
    [
        pytest.param("my/page", "my/page"),
        pytest.param("my/page", "my/page/index.html"),
        pytest.param("my/page/", "my/page/index.html"),
        pytest.param("my/page/", "404.html"),
    ],
)
def test_get_documentation(
    flask_send_from_directory, make_documentation_valid, path_to_request, path_to_return
):

    content = "html page"

    flask_send_from_directory.path_to_content = {path_to_return: content}

    assert content == docsendpoints.docs(path_to_request)


def test_get_documentation__404_missing(
    flask_send_from_directory, make_documentation_valid
):
    flask_send_from_directory.path_to_content = {}

    with pytest.raises(exceptions.InternalDocumentationMisconfigured):
        docsendpoints.docs("my/path")


def test_documentation_disabled():
    with pytest.raises(werkzeug_exceptions.HTTPException):
        docsendpoints.docs()


def test_documentation__misconfigured(
    monkeypatch, enable_documentation, flask_current_app
):
    monkeypatch.setattr(docsendpoints, "_documentation_root_is_valid", lambda: False)

    with pytest.raises(exceptions.InternalDocumentationMisconfigured):
        docsendpoints.docs()


# docs root is absolute vs relative
# the file doesn't exist vs it doesn't contain the string vs it does


@pytest.mark.parametrize(
    "file_exists,file_contains_string,documentation_is_valid",
    [
        pytest.param(True, True, True),
        pytest.param(True, False, False),
        pytest.param(False, False, False),
        pytest.param(False, False, False),
    ],
)
@pytest.mark.parametrize(
    "documentation_root,app_root,expected_index_html_location",
    [
        pytest.param(
            "../here", "/transiter/http", "/transiter/http/../here/index.html"
        ),
        pytest.param("/here", "/transiter/http", "/here/index.html"),
    ],
)
def test_documentation_root_is_value(
    monkeypatch,
    flask_current_app,
    file_exists,
    file_contains_string,
    documentation_is_valid,
    documentation_root,
    app_root,
    expected_index_html_location,
):
    monkeypatch.setattr(config, "DOCUMENTATION_ROOT", documentation_root)
    flask_current_app.root_path = app_root

    class IndexHtmlFile:
        @staticmethod
        def read():
            if file_contains_string:
                return "<!-- {} -->".format(docsendpoints._VERIFICATION_STRING)
            else:
                return "<html></html>"

    @contextmanager
    def open_function(filename):
        assert (
            filename == expected_index_html_location
        ), "The wrong index.html has been requested"
        if file_exists:
            yield IndexHtmlFile()
        else:
            raise FileNotFoundError

    monkeypatch.setattr(builtins, "open", open_function)

    assert documentation_is_valid == docsendpoints._documentation_root_is_valid()
