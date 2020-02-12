"""
This module contains the code for the transiterclt (Transiter command line
tools) command line program.
"""
import time

import click
from sqlalchemy import exc

from transiter import config
from transiter.data import dbconnection
from transiter.executor import celeryapp
from transiter.scheduler import server as scheduler


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
@click.argument("server", type=click.Choice(["webservice", "scheduler", "executor"]))
def launch(force, server):
    """
    Launch a Transiter service in debug mode.
    """
    if server == "webservice":
        # NOTE: the flask app is imported here because otherwise the task server will
        # use the app's logging configuration.
        from transiter.http import flaskapp

        flaskapp.launch(force)
    if server == "scheduler":
        app = scheduler.create_app()
        app.run(host="0.0.0.0", port=config.SCHEDULER_PORT, debug=False)
    if server == "executor":
        celeryapp.run()


@transiter_clt.group()
def db():
    """
    Perform Transiter database operation.
    """


@db.command()
def schema():
    """
    Dump the Transiter database's schema in SQL.
    """
    dbconnection.generate_schema()


@db.command()
def init():
    """
    Initialize the Transiter database.
    """
    while True:
        try:
            dbconnection.init_db()
            print("DB ready")
            return
        except exc.SQLAlchemyError:
            print("Failed to connect to the DB; Waiting 1 second")
            time.sleep(1)


@db.command()
@click.confirmation_option(
    prompt="This will result in all data in the current database being lost.\n"
    "Are you sure?"
)
def reset():
    """
    Reset the Transiter database.

    This operation drops all of the Transiter tables in the database, if they
    exist, and then creates them. All existing data will be lost.
    """
    dbconnection.rebuild_db()
