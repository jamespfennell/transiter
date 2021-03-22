"""
This module contains the code for the transiterclt (Transiter command line
tools) command line program.
"""
import time

import click
from sqlalchemy import exc

from transiter import config
from transiter.db import dbconnection
from transiter.executor import celeryapp
from transiter.scheduler import server as scheduler, client


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
@click.option(
    "-l",
    "--log-level",
    default="warning",
    type=click.Choice(["debug", "info", "warning", "error", "fatal"]),
    help="The log level.",
)
@click.argument("server", type=click.Choice(["webservice", "scheduler", "executor"]))
def launch(force, log_level, server):
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
        celeryapp.run(log_level)


@transiter_clt.group()
def db():
    """
    Perform Transiter database operation.
    """


@db.command()
def init():
    """
    Initialize the Transiter database.

    This is a no-op if the database is already initialized to any version of the
    database. It is designed to safely avoid accidental upgrades.
    """
    while True:
        try:
            if dbconnection.get_current_database_revision() is not None:
                print(
                    "The database has already been initialized and "
                    "no upgrade will be attempted."
                )
                print(
                    "In order to upgrade the database use the "
                    "`transiterclt db upgrade` command. "
                )
                return
            print("Initializing the database")
            dbconnection.upgrade_database()
            print("Database initialized!")
        except exc.SQLAlchemyError:
            print("Failed to connect to the database; Waiting 1 second")
            time.sleep(1)


@db.command()
def upgrade():
    """
    Upgrade the Transiter database to its latest version.
    """
    dbconnection.upgrade_database()


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
    print("Deleting old tables...")
    dbconnection.delete_all_tables()
    print("Upgrading database...")
    dbconnection.upgrade_database()
    client.refresh_tasks()
    print("Done.")


if __name__ == "__main__":
    transiter_clt()
