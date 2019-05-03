"""
The config module is responsible for loading Transiter's global config at
runtime and providing it to modules that require it.

The config currently includes the database and task server port configuration.

The config is loaded from the following locations, in
decreasing order of precedence:
1. The location specified using the -c argument of transiterclt.
2. The location specified in the environment variable TRANSITER_CONFIG.
3. The file transiter-config.toml in the current working directory,
   if it exists
4. The default configuration in this module.

In cases (1) and (2), if the location is specified and the file can not be
found, an exception is raised and Transiter will fail to launch.
"""

import os

import toml

from transiter import exceptions

DEFAULT_FILE_PATH = "transiter-config.toml"


class DefaultDatabaseConfig:
    DRIVER = "sqlite"
    DIALECT = None
    NAME = "transiter.db"
    USERNAME = None
    PASSWORD = None
    HOST = None
    PORT = None


DatabaseConfig = DefaultDatabaseConfig


class DefaultTaskServerConfig:
    PORT = 5001


TaskServerConfig = DefaultTaskServerConfig


def generate(database_config=DatabaseConfig, task_server_config=TaskServerConfig):
    """
    Generate a Transiter config string.

    The config string will be populated with values from the config classes
    passed in. If not config class is passed in the current values will
    be used.

    :param database_config: the database config
    :param task_server_config: the taskserver config to use
    :return: the TOML string
    """
    format_dict = {}
    for type_, config in (
        ("DatabaseConfig", database_config),
        ("TaskServerConfig", task_server_config),
    ):
        for key, value in config.__dict__.items():
            if key[0] == "_":
                continue
            if value is None:
                value = ""
            full_key = "{}-{}".format(type_, key)
            format_dict[full_key] = value
    return _TOML_CONFIG_STR_TEMPLATE.format(**format_dict)


def load_from_str(toml_str: str):
    """
    Load a Transiter TOML config given as a string.

    :param toml_str: the config string
    """

    new_config = toml.loads(toml_str)

    class CustomDatabaseConfig(DefaultDatabaseConfig):
        pass

    class CustomTaskServerConfig(DefaultTaskServerConfig):
        pass

    toml_section_to_config = {
        "database": CustomDatabaseConfig,
        "taskserver": CustomTaskServerConfig,
    }

    for section, Config in toml_section_to_config.items():
        for name, value in new_config.get(section, {}).items():
            existing_names = set(dir(Config))
            if name.upper() in existing_names:
                if value == "":
                    value = None
                setattr(Config, name.upper(), value)

    global DatabaseConfig, TaskServerConfig
    DatabaseConfig = CustomDatabaseConfig
    TaskServerConfig = CustomTaskServerConfig


def load(file_path: str = None):
    """
    Load the Transiter config.

    This config implements the business logic specified in the module docstring.

    :param file_path: the optional file path to the config.
    :return: nothing. The config is loaded into the module variables.
    """
    file_must_exist = True
    if file_path is None:
        file_path = os.environ.get("TRANSITER_CONFIG", None)
        if file_path is None:
            file_must_exist = False
            file_path = DEFAULT_FILE_PATH

    try:
        with open(file_path, "r") as file_handle:
            toml_str = file_handle.read()
    except FileNotFoundError:
        if file_must_exist:
            raise exceptions.ConfigFileNotFoundError()
        else:
            return

    load_from_str(toml_str)


_TOML_CONFIG_STR_TEMPLATE = """
# Transiter configuration file

[database]

# The driver and dialect settings are used to specify which DBMS is in use
# and which Python package to use to connect to it. Currently officially 
# supported options:
#
# | DBMS       | Driver     | Dialect    | Additional python packages required |
# |------------+------------+------------+-------------------------------------|
# | Postgresql | postgresql | psycopg2   | psycopg2-binary                     |

driver = '{DatabaseConfig-DRIVER}'
dialect = '{DatabaseConfig-DIALECT}'

# The database name. Note that for SQLite the database name is the location 
# of the file on disk relative to the directory Transiter servers are launched.

name = '{DatabaseConfig-NAME}'

# User settings.

username = '{DatabaseConfig-USERNAME}'
password = '{DatabaseConfig-PASSWORD}'

# Host settings. If using Postgres or another client/server DBMS the database
# can be on a separate machine to the Transiter instance. If running the
# Transiter instance on the same Unix machine as the database, it is highly 
# recommended to use Unix domain sockets instead of TCP, in which case the
# host and port settings should be empty

host = '{DatabaseConfig-HOST}'
port = '{DatabaseConfig-PORT}'

[taskserver]

# The port that the task server listens on. This is used both when 
# launching the task server, and when the main HTTP server attempts to 
# communicate with it.

port = '{TaskServerConfig-PORT}'

"""

load()
