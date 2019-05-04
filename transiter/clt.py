"""
This module contains the code for the transiterclt (Transiter command line
tools) command line program.
"""
import click

from transiter.data import dbconnection
from transiter import config, exceptions
from transiter.http import flaskapp
from transiter.taskserver import server as taskserver


@click.group()
@click.option(
    "-c",
    "--config-file",
    default=None,
    type=str,
    help="Path to the Transiter config file. If not provided, this defaults "
    "to the value of the environment variable TRANSITER_CONFIG, "
    "or transiter-config.toml "
    "if the environment variable is not set. "
    "In the last case, if transiter-config.toml does not exist, the"
    "default (SQLite) configuration is used.",
)
def transiter_clt(config_file):
    """
    Transiter Command Line Tools
    """
    try:
        config.load(config_file)
    except exceptions.ConfigFileNotFoundError:
        click.echo('Error: config file "{}" not found.'.format(config_file))
        exit()


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
        flaskapp.launch(force)
    if server == "task-server":
        taskserver.launch(force)


@transiter_clt.command()
@click.option("-f", "--force", is_flag=True, help="Overwrite any existing file.")
@click.option(
    "-o",
    "--output-file",
    default=None,  # config.DEFAULT_FILE_PATH,
    show_default=True,
    help="Path to output the config file to.",
)
@click.option(
    "-u",
    "--use-current-values",
    is_flag=True,
    help="Populate the Transiter config file with the current config values, "
    "rather than the defaults.",
)
def generate_config(force, output_file, use_current_values):
    """
    Generate a Transiter config file template.

    Write to the standard output, or to a file if -o is specified.
    """
    mode = "w" if force else "x"
    if use_current_values:
        config_str = config.generate()
    else:
        config_str = config.generate(
            database_config=config.DefaultDatabaseConfig,
            task_server_config=config.DefaultTaskServerConfig,
        )
    if output_file is None:
        print(config_str)
        return
    try:
        with open(output_file, mode) as file_handle:
            file_handle.write(config_str)
    except FileExistsError:
        click.echo("File already exists. Use the -f option to overwrite it.")


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
