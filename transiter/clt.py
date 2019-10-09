"""
This module contains the code for the transiterclt (Transiter command line
tools) command line program.
"""
import click

from transiter.data import dbconnection
from transiter.taskserver import server as taskserver


@click.group()
def transiter_clt():
    """
    Transiter Command Line Tools
    """
    pass


@transiter_clt.command()
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="Force start by killing any process listening on the target port.",
)
@click.argument("server", type=click.Choice(["http-debug-server", "task-server"]))
def launch(force, server):
    """
    Launch a Transiter server.

    - The http-debug-server is a Flask debug server for testing HTTP endpoints.
    It should not be used in production!

    - The task-server is designed to be used in production.
    """
    if server == "http-debug-server":
        # NOTE: the flask app is imported here because otherwise the task server will
        # use the app's logging configuration.
        from transiter.http import flaskapp

        flaskapp.launch(force)
    if server == "task-server":
        taskserver.launch(force)


@transiter_clt.command()
def generate_schema():
    """
    Generate a SQL file that builds the Transiter schema.
    """
    dbconnection.generate_schema()


@transiter_clt.command()
@click.confirmation_option(
    prompt="This will result in all data in the current database being lost.\n"
    "Are you sure?"
)
def rebuild_db():
    """
    Build or rebuild the Transiter database.

    This operation drops all of the Transiter tables in the database, if they
    exist, and then creates them. All existing data will be lost.
    """
    dbconnection.rebuild_db()
