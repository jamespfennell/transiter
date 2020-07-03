import logging
import os

import flask
from werkzeug import exceptions as werkzeug_exceptions

from transiter import config, exceptions
from transiter.http import httpviews
from transiter.http.httpmanager import (
    link_target,
    HttpStatus,
    register_documented_endpoint,
)

docs_endpoints = flask.Blueprint(__name__, __name__)

logger = logging.getLogger(__name__)

_MISCONFIGURED_DOCUMENTATION_MESSAGE = """
The documentation appears to be misconfigured.

Please ensure that you have performed the following steps:

1. Generated the HTML documentation by executing `mkdocs build` in the
   Transiter documentation directory (./docs in the Git repo).

2. Set TRANSITER_DOCUMENTATION to point to the 'site' directory created by
   step 1. This environment variable can either be absolute, or relative
   to the directory of the Transiter WSGI app, which is:

       {}
"""

_FILE_NOT_FOUND_MESSAGE = """
Could not find file 'index.html' in the documentation root:

    TRANSITER_DOCUMENTATION_ROOT={}

The full absolute file path is:

    {}

Note that if TRANSITER_DOCUMENTATION_ROOT is a relative path, the absolute path is
calculated relative to the Transiter WSGI app's directory, which is:

    {}
"""


# NOTE: the built documentation refers to other HTML pages and assets using relative
# links. We need to redirect onto the URL with the slash in order for these to work.
@docs_endpoints.route("/", strict_slashes=True)
@docs_endpoints.route("/<path:path>", strict_slashes=True)
@register_documented_endpoint(None, "GET")
@link_target(httpviews.InternalDocumentationLink)
def docs(path="index.html", retry_with_index_dot_html=True, perform_validation=True):
    """
    Internal documentation

    If internal documentation is enabled, this endpoint returns the requested
    documentation HTML page.
    The internal documentation system is described in a
    [dedicated documentation page](../deployment/documentation.md).

    If internal documentation is disabled, this endpoint always returns a 404 error -
    i.e., Transiter behaves as if this endpoint doesn't exist.

    Return code | Description
    ------------|-------------
    `200 OK` | Internal documentation is enabled and the relevant page does not exist.
    `404 NOT FOUND` | Internal documentation is disabled, or it is enabled and the requested page does not exist.
    `503 SERVICE UNAVAILABLE` | Internal documentation is enabled but mis-configured. See the documentation page and the logs for debugging help.
    """
    if not config.DOCUMENTATION_ENABLED:
        logger.debug(f"Documentation not enabled so returning a 404 for docs/{path}.")
        flask.abort(HttpStatus.NOT_FOUND)
    if perform_validation and not _documentation_root_is_valid():
        logger.error(
            _MISCONFIGURED_DOCUMENTATION_MESSAGE.format(
                flask.helpers.current_app.root_path
            )
        )
        raise exceptions.InternalDocumentationMisconfigured
    try:
        return flask.send_from_directory(config.DOCUMENTATION_ROOT, path)
    except werkzeug_exceptions.HTTPException:
        if path == "404.html":
            logger.error("404.html page is missing from documentation root!")
            raise exceptions.InternalDocumentationMisconfigured
        if not retry_with_index_dot_html:
            return docs(
                "404.html", retry_with_index_dot_html=False, perform_validation=False
            )
        if not path.endswith("/"):
            path += "/"
        path += "index.html"
        return docs(path, retry_with_index_dot_html=False, perform_validation=False)


# The verification string is included in index.html using the footer configuration
# in docs/mkdocs.yml.
_VERIFICATION_STRING = (
    "6808e24437044a523cf793e1f93f6924-"
    "90388b1a0c91760551522c59a4088557-"
    "7a55dcd8cb6f2093d5ab9a9b7997d9cc"
)


def _documentation_root_is_valid():
    filename = os.path.join(config.DOCUMENTATION_ROOT, "index.html")
    if not os.path.isabs(filename):
        filename = os.path.join(flask.helpers.current_app.root_path, filename)
    try:
        with open(filename) as f:
            return _VERIFICATION_STRING in f.read()
    except FileNotFoundError:
        logger.error(
            _FILE_NOT_FOUND_MESSAGE.format(
                config.DOCUMENTATION_ROOT, filename, flask.helpers.current_app.root_path
            )
        )
        return False
